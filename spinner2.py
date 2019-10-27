#upip.install("micropython-umqtt.simple")
#upip.install("micropython-umqtt.robust")
#upip.install("micropython-hmac")

import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import random
from machine import Timer
import umqtt.simple

def connect_WiFi(ssid='Is this the Krusty Krab?', password='tHiSiStHePaSsWoRd'):
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
    print('Connected to ' + ssid)
    print('MAC Address: ', mac)
    print('IP Address: ', wlan.ifconfig()[0])
    return wlan

#connect_WiFi('Is this the Krusty Krab?', 'tHiSiStHePaSsWoRd')
connect_WiFi('', '')
client = umqtt.simple.MQTTClient(b'esp32_', 'farmer.cloudmqtt.com', user='vijxbefv', port='14245', password='YkkggDr3iVuM')
client.connect()

def publish_SessionID(x):
    id = random.randint(1, 101)
    print(id)
    client.publish("SessionID", str(id))

tim = Timer(1)
tim.init(period=1000, mode=Timer.PERIODIC, callback=publish_SessionID)
