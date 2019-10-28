import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import crypt
import umqtt.simple
import random


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


def publish_SessionID(x):
    global SESSION_ID, CLIENT
    id = random.randint(1, 101)
    # print(id)
    SESSION_ID = id
    CLIENT.publish("SessionID", str(id))


def new_data(topic, msg):
    global CLIENT
    ack = verify_hmac(msg)
    if ack == 'Passed HMAC Authentication':
        pass
    else:
        
    CLIENT.publish("Acknowledgement", ack)
    
    

connect_WiFi('Is this the Krusty Krab?', 'tHiSiStHePaSsWoRd')

CLIENT = umqtt.simple.MQTTClient(b'esp32_', 'farmer.cloudmqtt.com', user='vijxbefv', port='14245', password='YkkggDr3iVuM')
CLIENT.connect()
CLIENT.set_callback(new_data)
CLIENT.subscribe('Sensor_Data')

# print('Installing UMQTT and HMAC packages...')
# upip.install('micropython-umqtt.simple')
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-hmac')

SESSION_ID = 0

tim = Timer(1)
tim.init(period=1000, mode=Timer.PERIODIC, callback=publish_SessionID)
