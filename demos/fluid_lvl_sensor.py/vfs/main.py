# author : Igor Rybakowski
# created: 27.11.2020
#

import e2
import time
import blynklib_mp as BlynkLib
import network
import socket
import ure

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

# Connect to Wifi
do_connect(ap_ssid, ap_password)
# Integrate with blynk app
blynk = BlynkLib.Blynk('KGNUOdaRSq8KqlozX-Z4w8U84cJAavj5')


# Modules initialization
but = e2.button(0)
owt = e2.onewiretemperaturesensor(0)
dis = e2.distancesensor(0)
seg = e2.segmentdisplay(0)


# If mode is True then segment display will return the Temperature readings
# While False it returns readings from distance sensor
mode = False

print(" FLUID LVL SENSOR ")
print(" The segment display shows distance readings now ")
print(" Use the button to switch between temperature and distance readings")

# Main Loop
while True:
	blynk.run()
	temp = owt.get_temperature()
	distance = dis.get_distance() / 10
	print("[Temp sensor    ] Temperature: ", temp, " C")
	print("[Distance sensor] Distance: ", distance, " cm")
	
	# Send the data to blynk app
	blynk.virtual_write(0, temp)
	blynk.virtual_write(1, distance)
	if but.get_event() == 1: 
		mode = not mode
	if mode == True:
		str = "%2dc" % (temp)
		seg.display_string([elem.encode()[0] for elem in str])
	else:
		str = "%2dc" % (distance)
		seg.display_string([elem.encode()[0] for elem in str])
	time.sleep(0.2)
	# If the fluid level is high, notify the user
	if distance < 40:
		blynk.notify("It's time for cesspool disposal ")

