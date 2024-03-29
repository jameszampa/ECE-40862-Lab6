import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import crypt
import umqtt.simple
import random
from machine import Pin
from machine import PWM
from machine import Timer
from time import sleep_ms

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
    global SESSION_ID, CLIENT
    SESSION_ID += 1
    try:
        CLIENT.publish("SessionID", str(SESSION_ID))
    except:
        pass
    CRYPT_AES = crypt.CryptAes(2, SESSION_ID)


def new_data(topic, msg):
    global CLIENT, CRYPT_AES, RED_LED, PREV_TEMP, GREEN_LED, PREV_STATE, SESSION_ID
    
    #print(msg)
    ack = CRYPT_AES.verify_hmac(msg)
    #print(ack)
    if ack == 'Passed HMAC Authentication':
        if PREV_STATE != 'Spinner':
            GREEN_LED.freq(10)
            GREEN_LED.duty(512)
        
        crypt_msg = CRYPT_AES.decrypt(msg)
        
        x_val, y_val, z_val, temp = struct.unpack("ffff", CRYPT_AES.decrypted_data)
        
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
        
        data = {}
        string = '2' + '|||' + str(session_id) + '|||' + str(x_val) + '|||' + str(y_val) + '|||' + str(z_val) + '|||' + str(temp)
        data['value1'] = string
        http_get('https://maker.ifttt.com/trigger/UpdateSheet_Spinner2/with/key/diOQOLSzW1_Sh8OGpu4QgJ', ujson.dumps(data))
        CLIENT.publish("Acknowledgement", ack)
        CLIENT.publish("Acknowledgement", crypt_msg)
    else:
        CLIENT.publish("Acknowledgement", ack)
    
    
    PREV_STATE = STATE
    STATE = 'Spinner'


def interfacing_sensors():
    global GREEN_LED, RED_LED, PREV_STATE, STATE, tim
    
    if PREV_STATE != 'Sensor':
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
SWITCH1    = Pin(34, Pin.IN)
SWITCH2    = Pin(39, Pin.IN)
SWITCH1.irq(trigger=Pin.IRQ_RISING, handler=switch1_handler)
SWITCH2.irq(trigger=Pin.IRQ_RISING, handler=switch2_handler)

CLIENT = umqtt.simple.MQTTClient(b'esp32_', 'farmer.cloudmqtt.com', user='vijxbefv', port='14245', password='YkkggDr3iVuM')
CLIENT.set_callback(new_data)
CLIENT.connect()
CLIENT.subscribe('Sensor_Data')

# print('Installing UMQTT and HMAC packages...')
# upip.install('micropython-umqtt.simple')
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-hmac')

CRYPT_AES  = None
SESSION_ID = 0
PREV_TEMP  = None
GREEN_LED  = PWM(Pin(4), freq=10, duty=0)
RED_LED    = Pin(26, Pin.OUT)
STATE      = 'Idle'
PREV_STATE = 'Idle'

tim = None

print("Init Complete")
while(1):
    sleep_ms(100)
    if STATE == 'Sensor':
        interfacing_sensors()
    elif STATE == 'Spinner':
        if PREV_STATE == 'Sensor':
            print("now in secure spinner demo")        
            if tim == None:
                tim = Timer(1)
                tim.init(period=1000, mode=Timer.PERIODIC, callback=publish_SessionID)
            else:
                tim.deinit()
                tim = Timer(1)
                tim.init(period=1000, mode=Timer.PERIODIC, callback=publish_SessionID)
            #publish_SessionID("owefij")
        try:
            CLIENT.wait_msg()
        except:
            pass

