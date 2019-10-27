import upip
from network import WLAN, STA_IF
from ubinascii import hexlify


"""
Written by: James Zampa
"""


def connect_WiFi(ssid='NachoWifi', password='ICUPatnight'):
    wlan = WLAN(STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    mac = hexlify(WLAN().config('mac'),':').decode()
    print('Oh Yes! Get Connected')
    print('Connected to NachoWifi')
    print('MAC Address: ', mac)
    print('IP Address: ', wlan.ifconfig()[0])
    return wlan


def switch1_handler(t):
    global STATE, PREV_STATE
    PREV_STATE = STATE
    STATE = 'Sensor'
    return


def sense_g(data):
    g = ((data[1] & 0x1F) << 5) | (data[0] & 0x1F)
    g = g & 0x3FF
    if g & 0x200:
        g -= 1024
    return g


def switch2_handler(t):
    global STATE, PREV_STATE
    if STATE != 'Idle':
        PREV_STATE = STATE
        STATE = 'Spinner'
    return


def update_offset():
    global I2C_UNIT, TOTAL_SAMPLE_COUNT, TOTAL_OFFSET_X, TOTAL_OFFSET_Y, TOTAL_OFFSET_Z
    
    data = bytearray(6)
    I2C_UNIT.readfrom_mem_into(ACCEL_ADDR, 0x32, data)
    TOTAL_OFFSET_X += sense_g(data[0:2])
    TOTAL_OFFSET_Y += sense_g(data[2:4])
    TOTAL_OFFSET_Z += sense_g(data[4:6])
    TOTAL_SAMPLE_COUNT += 1
    
    sleep_ms(10)
    
    avgx = round(TOTAL_OFFSET_X / TOTAL_SAMPLE_COUNT)
    avgy = round(TOTAL_OFFSET_Y / TOTAL_SAMPLE_COUNT)
    avgz = round(TOTAL_OFFSET_Z / TOTAL_SAMPLE_COUNT)
    
    s_z = 256
    z_0g = avgz - s_z
    
    offset_x = -1 * round(avgx / 4)
    offset_y = -1 * round(avgy / 4)
    offset_z = -1 * round(z_0g / 4)
    
    return offset_x, offset_y, offset_z


def interfacing_sensors():
    global I2C_UNIT, PWM_ONBOARD, STATE, PREV_STATE, RED_LED, GREEN_LED, TOTAL_SAMPLE_COUNT
        
    if PREV_STATE != 'Sensor':
        PWM_ONBOARD.freq(1000)
        PWM_ONBOARD.duty(512)
        
        print('Inference Sensor State')
        
        RED_LED.off()
        GREEN_LED.off()
        
        total_samp_count = 0
        total_offset_x = 0
        total_offset_y = 0
        total_offset_z = 0
        
        # Initialize Accelerometer
        data = bytearray(1)
        # ACCEL_ADDR = 83
        # ACCEL_ID_REG = 0
        I2C_UNIT.readfrom_mem_into(83, 0, data)
        if data != b'\xe5':
            raise ValueError('Error reading ID value for accelerometer.')
        
        # set 13 bit mode with range to +-2g
        # ACCEL_DATA_FORMAT = 0x31
        I2C_UNIT.writeto_mem(83, 0x31, b'\x08')
        print('Configured Acceleration Sensor to 13-bit +-2g mode')
        
        # ACCEL_BW_RATE = 0x2C
        # set ODR to 800Hz
        I2C_UNIT.writeto_mem(83, 0x2C, b'\x0D')
        print('Configured Acceleration Sensor for 800Hz ODR')
        
        # ACCEL_PWR_CTL = 0x2D
        # enable measure bit
        I2C_UNIT.writeto_mem(83, 0x2D, b'\x08')
        print('Enabled measurements for Acceleration Sensor')
        
        # Temp Sense
        # TEMP_ADDR = 72
        # TEMP_ID_REG = 0x0B
        # TEMP_CONF_REG = 0x03
        data = bytearray(1)
        I2C_UNIT.readfrom_mem_into(72, 0x0B, data)
        if data != b'\xcb':
            raise ValueError('Error reading ID value for temperature sensor.')
        # config for 16 bit resolution
        I2C_UNIT.writeto_mem(72, 0x03, b'\x80')
        print('Set Temperature Sensor for 16-bit high resolution')
        print('Temperature Sensor Configured')
    
    if TOTAL_SAMPLE_COUNT < 100:
        x_offset, y_offset, z_offset = update_offset()
        I2C_UNIT.writeto_mem(83, 0x1e, x_offset.to_bytes(1, 'big'))
        I2C_UNIT.writeto_mem(83, 0x1F, y_offset.to_bytes(1, 'big'))
        I2C_UNIT.writeto_mem(83, 0x20, z_offset.to_bytes(1, 'big'))
        if TOTAL_SAMPLE_COUNT == 100:
            print('Calibration Complete...')
            print('Final Offsets...')
            print('X: ', x_offset, 'Y: ', y_offset, 'Z: ', z_offset)
    
    print('Acceleration Sensor Configured')
    PREV_STATE = STATE
    STATE = 'Sensor'


def spinner():
    if PREV_STATE != 'Spinner':
        PWM_ONBOARD.freq(10)
        PWM_ONBOARD.duty(512)


connect_WiFi('DESKTOP-FUGJA40 9245', 'tI5845?9')

print('Installing UMQTT and HMAC packages...')
upip.install('micropython-umqtt.simple')
upip.install('micropython-umqtt.robust')
upip.install('micropython-hmac')

print('Initialization')
SWITCH1    = Pin(34, Pin.IN)
SWITCH2    = Pin(39, Pin.IN)
SWITCH1.irq(trigger=Pin.IRQ_RISING, handler=switch1_handler)
SWITCH2.irq(trigger=Pin.IRQ_RISING, handler=switch2_handler)

GREEN_LED  = Pin(4, Pin.OUT)
RED_LED    = Pin(26, Pin.OUT)
GREEN_LED.off()
RED_LED.off()

I2C_UNIT = I2C(0, scl=Pin(22), sda=Pin(23), freq=400000)

PWM_ONBOARD = PWM(Pin(13), freq=10, duty=0)

STATE = 'Idle'
PREV_STATE = 'Idle'

while(1):
    sleep_ms(100)
    if STATE == 'Sensor':
        interfacing_sensors()
    elif STATE == 'Spinner':
        spinner()