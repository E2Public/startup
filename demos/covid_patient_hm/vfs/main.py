# author : Igor Rybakowski
# created: 29.11.2020
#

import e2
from time import sleep
import blynklib_mp as BlynkLib
import network
import socket
import ure

# Variables to store data needed to connect to WiFi and Blynk
wlan_sta = network.WLAN(network.STA_IF)
TEST_SSID = "Electron_Square_AP_2.4GHz"
TEST_PASSWORD = "64J4KF7HGKQY"
TEST_BLYNK_KEY = "ILqCGY6qktXp75h8JVaxrcfFYhV8fPlV"

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
		sleep(0.1)
		print('.', end='')
	if connected:
		print('\nConnected. Network config: ', wlan_sta.ifconfig())
	else:
		print('\nFailed. Not Connected to: ' + ssid)
	return connected

# Connect with Wifi and Blynk
connection = do_connect(TEST_SSID, TEST_PASSWORD)
blynk = BlynkLib.Blynk(TEST_BLYNK_KEY)

# Modules initialization
hum = e2.humiditysensor(0)
pul = e2.sensorhub(0)
joy = e2.joystick(0)
bts = e2.bodytemperaturesensor(0)
buz = e2.buzzer(0)
seg = e2.segmentdisplay(0)
rgb = e2.rgbled(0)

# Dictionary with sensor names
names = ["humidity sensor", "bodytemperaturesensor", "pulseoximeter"]
modes = ['single mode', 'run program', 'run all', 'exit to repl']


# Functions used to print out the sensors data
# and to send readings to Blynk app
def read_hum():
	while joy.get_state() < 200:
		blynk.run()
		rgb.set_rgb(0,255,0)
		humidity = hum.get_humidity()
		temperature = hum.get_temperature()
		print(chr(27) + "[2J")
		print("[humiditysensor  ]")
		print("Room temperature and humidity")
		print("Press joystick to quit")
		print("humidity: ", humidity, "%RH")
		print("temperature: ", temperature, "'C")
		blynk.virtual_write(3, humidity)
		blynk.virtual_write(4, temperature)


def read_bts():
	print("Wait 2 sec...")
	sleep(2)
	while joy.get_state() < 200:
		blynk.run()
		temperature = bts.get_temperature()
		if temperature > 1:
			blynk.virtual_write(2, temperature)
			rgb.set_rgb(0,255,0)
			print(chr(27) + "[2J")
			print("[bodytemperaturesensor  ]")
			print("Hold your thumb on the sensor")
			print("Press joystick to quit")
			print("temperature: ", temperature, "'C")
			str = "%2dc" % (temperature)
			seg.display_string([elem.encode()[0] for elem in str])
			sleep(1)

	rgb.set_all(0)

def read_pul():
	# Wait for pulsoximeter to calibrate
	while pul.get_bpm() == 0:
		blynk.run()
		rgb.set_rgb(200,200,0)
		print(chr(27) + "[2J")
		print("[pulsoximeter  ]")
		print("Put your thumb on the sensor to receive readings")
		print("Wait for the green light")
		sleep(0.5)


	while joy.get_state() < 200:
		blynk.run()
		pulse = pul.get_bpm()
		spo2 = pul.get_spo2()
		if pulse == 0:
			rgb.set_rgb(0,128,128)
		else :
			rgb.set_rgb(0,128,0)
		
		if pulse > 0 or spo2 > 0:
			blynk.virtual_write(0, pulse)
			blynk.virtual_write(1, spo2)

		# APP ALERT 
		if pulse > 140 or pulse < 40:
			blynk.virtual_write(4, 1)
		else:
			blynk.virtual_write(4, 0)

		print(chr(27) + "[2J")
		print("[pulsoximeter  ]")
		print("Put your thumb on the sensor to receive pulse readings")
		print("Hold your thumb on the pulsoximeter")
		print("Press joystick to quit")
		print("[BPM   ]", pulse)
		print("[SpO2  ]", spo2, " %")
		str = "%2dc" % (pul.get_bpm())
		seg.display_string([elem.encode()[0] for elem in str])

		sleep(0.5)

	print("Wait 2 sec")
	sleep(2)

def run_all():
	while joy.get_state() < 200:
		blynk.run()
		rgb.set_rgb(0,0,180)
		bte = bts.read_temperature()
		pulse = pul.get_bpm()
		spo2 = pul.get_spo2()	
		if pulse > 0:
			blynk.virtual_write(0, pulse)
			print("[BPM   ]", pulse)
		if spo2 > 0:
			blynk.virtual_write(1, spo2)
			print("[SpO2  ]", spo2, " %")
		if bte > 1:
			blynk.virtual_write(2, bte)
			print("[Body temperature ]", bte, "'C")
		temperature = hum.get_temperature()
		humidity = hum.get_humidity()
		print("temperature: ", temperature, "'C")
		blynk.virtual_write(3, humidity)
		blynk.virtual_write(4, temperature)
		rgb.set_all(0)
		print(" ")
		
		sleep(0.08)


# Dictionary containing functions
func_dic = {"0" : read_hum, "1" : read_bts, "2" : read_pul}

# Menu loop with cursor
def menu(crs, tsil):
	length = len(tsil)
	print(chr(27) + "[2J")
	print("[e2] COVID PATIENT HEALTH MONITOR")
	print(crs)
	for i in range(length):
		if crs == i:
			print("[*]", end = '')
			print(tsil[i])
		else:
			print("[ ]", end = '')
			print(tsil[i])

# Select mode
# Single sensor to receive readings from only one sensor
# All sensors to continously receive readings from all sensors
def select_mode():
	print(chr(27) + "[2J")
	print("[e2] COVID PATIENT HEALTH MONITOR")
	print("Select mode")
	cursor = 0
	while True:
		blynk.run()
		if joy.get_state() == 0:
			sleep(0.1)
			cursor+=1
			if cursor > 3:
				cursor = 0
			menu(cursor, modes)
		if joy.get_state() == 1:
			sleep(0.1)
			cursor-=1
			if cursor < 0:
				cursor = 3
			menu(cursor, modes)
		if joy.get_state() == 244:
			return cursor
		sleep(0.03)


# Select sensor in single mode
def select_sensor():
	print(chr(27) + "[2J")
	print("[e2] COVID PATIENT HEALTH MONITOR")
	print("Select sensor. Push the button to navigate")
	print("Hold to confirm")
	cursor = 0
	while True:
		blynk.run()
		if joy.get_state() == 0:
			sleep(0.06)
			cursor+=1
			if cursor > 2:
				cursor = 0
			menu(cursor, names)
		if joy.get_state() == 1:
			sleep(0.06)
			cursor-=1
			if cursor < 0:
				cursor = 2
			menu(cursor, names)
		if joy.get_state() == 244:
			print(cursor)
			return cursor
		sleep(0.03)


with open("data/motd.txt","r") as f:
	print(f.read())

def get_blocks():
	print("Connected blocks:")
	_x_dir = {}
	for _x_i in e2.current_devices_list():
		_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
	for _x_i in _x_dir.keys():
		print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))
	print('')

# main loop
while True:
	print("[e2 COVID HEALTH MONITOR")
	get_blocks()
	blynk.run()
	string = "%2dc" % (000)
	seg.display_string([elem.encode()[0] for elem in string])
	rgb.set_rgb(0,100,180)
	sleep(2)
	choice = 0
	mode = str(select_mode())
	sleep(1)
	if mode == "0":
		choice = str(select_sensor())
		print("Wait 2 sec...")
		sleep(2)
		func_dic[str(choice)]()

	if mode == "1":
		func_dic["0"]()
		print("Wait 2 sec...")
		func_dic["1"]()
		print("Wait 2 sec...")
		func_dic["2"]()

	if mode == "2":
		run_all()

	if mode == "3":
		break
	
		
