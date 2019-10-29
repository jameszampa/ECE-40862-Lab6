import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import crypt
import umqtt.simple
import random
import struct

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
    
    
def publish_SessionID(x):
    global SESSION_ID, CLIENT, CRYPT_AES
    id = random.randint(1, 101)
    # print(id)
    SESSION_ID = id
    CLIENT.publish("SessionID", str(id))
    CRYPT_AES = crypt.CryptAes(2, SESSION_ID)


def new_data(topic, msg):
    global CLIENT, CRYPT_AES, RED_LED, PREV_TEMP, GREEN_LED, PREV_STATE, SESSION_ID
        
    ack = CRYPT_AES.verify_hmac(msg)
    
    if ack == 'Passed HMAC Authentication':
        if PREV_STATE != 'Spinner':
            GREEN_LED.freq(10)
            GREEN_LED.duty(512)
        
        crypt_msg = CRYPT_AES.decrypt(msg)
        
        sensor_data = [None, None, None, None]
        sensor_data[0], sensor_data[1], sensor_data[2], sensor_data[3] = struct.unpack('ffff',CRYPT_AES.decrypted_data)
        x_val, y_val, z_val, temp = sensor_data
        
        if abs(x_val) > 1:
            RED_LED.on()
        elif abs(y_val) > 1:
            RED_LED.on()
        elif abs(z_val) > 1:
            RED_LED.on()
        else:
            RED_LED.off()
            
        if PREV_TEMP == None:
            PREV_TEMP = temp
        else:
            if temp - PREV_TEMP >= 1:
                GREEN_LED.freq(GREEN_LED.freq() + 5)
            elif PREV_TEMP - temp >= 1:
                GREEN_LED.freq(GREEN_LED.freq() - 5)
        
        # Update Google Sheet
        data = {}
        data['value1'] = '1|||' + str(SESSION_ID) + '|||' + x_val + '|||' + y_val + '|||' + z_val + '|||' + temp
        http_get('https://maker.ifttt.com/trigger/UpdateSheet_Spinner2/with/key/diOQOLSzW1_Sh8OGpu4QgJ', ujson.dumps(data))
        CLIENT.publish("Acknowledgement", crypt_msg)
    
    CLIENT.publish("Acknowledgement", ack)
    
    PREV_STATE = STATE
    STATE = 'Spinner'


def interfacing_sensors():
    global GREEN_LED, RED_LED, PREV_STATE, STATE
    
    print('Interfacing Sensors')
    RED_LED.off()
    GREEN_LED.freq(1000)
    GREEN_LED.duty(512)
    print('Spinner 2 does not use sensors...')
    
    PREV_STATE = STATE
    STATE = 'Sensor'


def switch1_handler(t):
    global STATE, PREV_STATE
    PREV_STATE = STATE
    STATE = 'Sensor'
    return


def switch2_handler(t):
    global STATE, PREV_STATE
    if STATE != 'Idle':
        PREV_STATE = STATE
        STATE = 'Spinner'
    return


#connect_WiFi('Is this the Krusty Krab?', 'tHiSiStHePaSsWoRd')
WLAN = connect_WiFi('DESKTOP-FUGJA40 9245', 'tI5845?9')

print('Initialization')
SWITCH1    = Pin(27, Pin.IN)
SWITCH2    = Pin(33, Pin.IN)
SWITCH1.irq(trigger=Pin.IRQ_RISING, handler=switch1_handler)
SWITCH2.irq(trigger=Pin.IRQ_RISING, handler=switch2_handler)

CLIENT = umqtt.simple.MQTTClient(b'esp32_', 'farmer.cloudmqtt.com', user='vijxbefv', port='14245', password='YkkggDr3iVuM')
CLIENT.connect()
CLIENT.set_callback(new_data)
CLIENT.subscribe('Sensor_Data')

# print('Installing UMQTT and HMAC packages...')
# upip.install('micropython-umqtt.simple')
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-hmac')

CRYPT_AES  = None
SESSION_ID = None
PREV_TEMP  = None
GREEN_LED  = PWM(Pin(12), freq=10, duty=0)
RED_LED    = Pin(32, Pin.OUT)
STATE      = 'Idle'
PREV_STATE = 'Idle'

tim = Timer(1)
tim.init(period=1000, mode=Timer.PERIODIC, callback=publish_SessionID)

while(1):
    sleep_ms(100)
    if STATE == 'Sensor':
        interfacing_sensors()
    elif STATE == 'Spinner':
        CLIENT.wait_msg()