from crypt import CryptAes
import struct

def encode_str(encrypt_stuff):
    str_temp = ''
    for b in encrypt_stuff:
        str_temp += chr(b)
    return str_temp

def decode_str(encrypt_stuff):
    x = bytearray(len(encrypt_stuff))
    for i in range(len(encrypt_stuff)):
        x[i] = ord(encrypt_stuff[i])
    return x

nodeid     = 1
session_id = 43
x_val      = 0.0001
y_val      = 0.0023
z_val      = 0.0032
temp       = 25.265

crypter = CryptAes(nodeid, session_id)
crypter.encrypt((x_val, y_val, z_val, temp))
#print(str(crypter.encrypted_data))
#print(crypter.encrypted_nodeid)
#print(crypter.encrypted_data + crypter.encrypted_iv + crypter.encrypted_nodeid)
hmac = crypter.sign_hmac(session_id)
#print("HMAC MADE")
#print(hmac.digest())
encrypted_sensor_data = crypter.send_mqtt(hmac)
#print(crypter.encrypted_iv)
#print((crypter.encrypted_iv).decode('utf8'))
#print(crypter.encrypted_iv.decode('utf-8').encode('utf-8'))

#print("Encrypted Data: ", encrypted_sensor_data)

print(crypter.verify_hmac(encrypted_sensor_data))
print(crypter.decrypt(encrypted_sensor_data))
print(struct.unpack("qq", crypter.decrypted_iv))
print(struct.unpack("qq", crypter.decrypted_nodeid))
print(struct.unpack("ffff", crypter.decrypted_data))


