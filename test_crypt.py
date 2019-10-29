from crypt import CryptAes

nodeid     = 1
session_id = 43
x_val      = 0.0001
y_val      = 0.0023
z_val      = 0.0032
temp       = 25.265

crypter = CryptAes(nodeid, session_id)
crypter.encrypt((x_val, y_val, z_val, temp))
print(str(crypter.encrypted_data))
#print(crypter.encrypted_nodeid)
#print(crypter.encrypted_iv)
#print(crypter.encrypted_data + crypter.encrypted_iv + crypter.encrypted_nodeid)
hmac = crypter.sign_hmac(session_id)
print("HMAC MADE")
print(hmac.digest())
encrypted_sensor_data = crypter.send_mqtt(hmac)
print("Encrypted Data: ", encrypted_sensor_data)
print(crypter.verify_hmac(encrypted_sensor_data))
print(crypter.decrypt(encrypted_sensor_data))

