# author : Igor Rybakowski
# created: 29.11.2020

# To do:


import e2
from time import sleep


print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
	_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
	print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')

# Variables to store data needed to connect to WiFi
ap_ssid = "Electron_Square_AP_2.4GHz"
ap_password = "64J4KF7HGKQY"
wlan_sta = network.WLAN(network.STA_IF)


# Function used to connect the device to WiFi network
def do_connect(ssid, password):
	wlan_sta.active(True)
	if wlan_sta.isconnected():
		return None
	print('Trying to connect to %s...' % ssid)
	wlan_sta.connect(ssid, password)
	for retry in range(100):
		connected = wlan_sta.isconnected()
		if connected:
			break
		time.sleep(0.1)
		print('.', end='')
	if connected:
		print('\nConnected. Network config: ', wlan_sta.ifconfig())
	else:
		print('\nFailed. Not Connected to: ' + ssid)
	return connected

do_connect(ap_ssid, ap_password)
blynk = BlynkLib.Blynk('')

rgb = e2.rgbled(0)
buz = e2.buzzer(0)
mq2 = e2.gassensormq2(0)
but = e2.button(0)

print(rgb)
print(buz)
print(mq2)
print(but)

risk = 100



#initialize smoke detector
mq2.get_smoke()
buz.sound_off()

# Quick mq2 initialization
rgb.set_rgb(128,128,0)
sleep(1)
rgb.set_all(0)
sleep(1)
rgb.set_rgb(128,128,0)
sleep(1)
rgb.set_all(0)
sleep(1)

# Wait for the MQ2 sensor to initialize
while mq2.get_smoke() > risk:
	rgb.set_rgb(128,128,0)
	sleep(0.5)
	rgb.set_all(0)
	sleep(0.5)


# Main loop
while True:
	blynk.run()
	for i in range(60):
		smoke = mq2.get_smoke()
		print(smoke)
		if smoke > risk:
			Blynk.notify("SMOKE ALARM")
			buz.set_frequency(2000)
			buz.sound_on()
			rgb.set_rgb(255,0,0)
		else:
			buz.sound_off()
			rgb.set_rgb(0,64,0)
		sleep(0.5)
		rgb.set_all(0)
		buz.sound_off()
		sleep(0.5)

