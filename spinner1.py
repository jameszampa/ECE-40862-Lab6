import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import crypt
import umqtt.simple


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


def http_get(url, data):
    _, _, host, path = url.split('/', 3)
    addr = getaddrinfo(host, 80)[0][-1]
    s = socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n%s\r\n\r\n' % (path, host, len(data), data), 'utf8'))
    while True:
        data = s.recv(100)
        if data:
            pass
        else:
            break
    s.close()


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


def temp_c(data):
    value = data[0] << 8 | data[1]
    temp = value & 0xFFFF
    if value & 0x8000:
        temp -= 65536
    temp = temp / 128.0
    return temp


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
    global I2C_UNIT, PWM_ONBOARD, STATE, PREV_STATE, TOTAL_SAMPLE_COUNT
        
    if PREV_STATE != 'Sensor':
        print('Inference Sensor State')
        
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
    

def new_data(topic, msg):
    global I2C_UNIT, STATE, PREV_STATE, PREV_TOPIC
    
    print(topic, msg)
    
    if (topic == b'Acknowledgement') & (prev_topic != b'Acknowledgement'):
        PREV_TOPIC = topic
    
    if (topic == b'SessionID') & (PREV_TOPIC != b'SessionID'):
        session_id = msg
        data = bytearray(6)
        I2C_UNIT.readfrom_mem_into(83, 0x32, data)
        x_val = sense_g([data[0], data[1]]) * 0.0039
        y_val = sense_g([data[2], data[3]]) * 0.0039
        z_val = sense_g([data[4], data[5]]) * 0.0039
        # Detect Temperature
        data = bytearray(2)
        I2C_UNIT.readfrom_mem_into(72, 0, data)
        temp = temp_c(data)
        
        # Upload to Google Sheet
        data = {}
        data['value1'] = '1|||' + session_id + '|||' + x_val + '|||' + y_val + '|||' + z_val + '|||' + temp
        http_get('https://maker.ifttt.com/trigger/UpdateSheet_Spinner1/with/key/diOQOLSzW1_Sh8OGpu4QgJ', ujson.dumps(data))
        
        crypter = crypt.CryptAes(0)
        crypter.encrypt((x_val, y_val, z_val, temp))
        hmac = crypter.sign_hmac(session_id)
        encrypted_sensor_data = crypter.send_mqtt(hmac)
        
        client.publish("Sensor_Data", encrypted_sensor_data)
    
    PREV_STATE = STATE
    STATE = 'Spinner'
    
# connect_WiFi('Is this the Krusty Krab?', 'tHiSiStHePaSsWoRd')
WLAN = connect_WiFi('DESKTOP-FUGJA40 9245', 'tI5845?9')

client = umqtt.simple.MQTTClient(b'esp32_', 'farmer.cloudmqtt.com', user='vijxbefv', port='14245', password='YkkggDr3iVuM')
client.connect()
client.set_callback(new_data)
client.subscribe(b'SessionID')
client.subscribe(b'Acknowledgement')


# print('Installing UMQTT and HMAC packages...')
# upip.install('micropython-umqtt.simple')
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-hmac')

print('Initialization')
SWITCH1    = Pin(34, Pin.IN)
SWITCH2    = Pin(39, Pin.IN)
SWITCH1.irq(trigger=Pin.IRQ_RISING, handler=switch1_handler)
SWITCH2.irq(trigger=Pin.IRQ_RISING, handler=switch2_handler)

I2C_UNIT = I2C(0, scl=Pin(22), sda=Pin(23), freq=400000)

STATE = 'Idle'
PREV_STATE = 'Idle'
PREV_TOPIC = None

while(1):
    sleep_ms(100)
    if STATE == 'Sensor':
        interfacing_sensors()
    elif STATE == 'Spinner':
        client.wait_msg()