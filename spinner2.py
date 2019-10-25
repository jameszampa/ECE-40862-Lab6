import upip
from network import WLAN, STA_IF
from ubinascii import hexlify

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

connect_WiFi('DESKTOP-FUGJA40 9245', 'tI5845?9')
upip.install("micropython-umqtt.simple")
upip.install("micropython-umqtt.robust")
upip.install("micropython-hmac")

