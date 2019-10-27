import upip
from network import WLAN, STA_IF
from ubinascii import hexlify
import urequests
import ujson

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


def http_get(url):
    _, _, host, path = url.split('/', 3)
    addr = getaddrinfo(host, 80)[0][-1]
    s = socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(100)
        if data:
            pass
        else:
            break
    s.close()
    
    
connect_WiFi()

#print('Installing UMQTT and HMAC packages...')
#upip.install('micropython-umqtt.simple')
#upip.install('micropython-umqtt.robust')
#upip.install('micropython-hmac')

stuff = {}
stuff['value1'] = '456'
stuff['value2'] = '789'
stuff['value3'] = '123'

r = urequests.request('POST', 'https://maker.ifttt.com/trigger/UpdateSheet/with/key/diOQOLSzW1_Sh8OGpu4QgJ', data=ujson.dumps(stuff))

