import e2

print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
	_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
	print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')

from time import sleep

# Modules initialization
thg = e2.thg(0)
mq2 = e2.gassensormq2(0)
lis = e2.lightintensitysensor(0)
hum = e2.humiditysensor(0)
lts = e2.lightsensor(0)
joy = e2.joystick(0)
buz = e2.buzzer(0)
rgb = e2.rgbled(0)

# Dictionary with sensor names
dic = {"humidity sensor" : "e2.humiditysensor", "gas sensor mq2" : "e2.gassensormq2",
		"light sensor" : "e2.lightsensor", "thg sensor": "e2.thg",
		"light intensity sensor" : "e2.lightintensitysensor"}

# Functions used to print out the sensors data
def read_thg():
	print("[THG     ] temperature: ", thg.get_temperature(), "'C")
	print("[THG     ] humidity: ", thg.get_humidity(), "%RH" )
	print("[THG     ] pressure: ", thg.get_pressure(), "hPa")
	
def read_mq2():
	print("[MQ2     ] Hydrogen: ", mq2.get_h2())
	print("[MQ2     ] LPG: ", mq2.get_lpg())
	print("[MQ2     ] Alcohol: ", mq2.get_alcohol())
	print("[MQ2     ] Smoke: ", mq2.get_smoke())

def read_hum():
	print("[Humidity] humidity: ", hum.get_humidity(), "%RH")
	print("[Humidity] temperature: ", hum.get_temperature(), "'C")

def read_lts():
	print("[Light   ] light intensity: ", lis.get_light_intensity())

def read_lis():
	print("[Light   ] UVA: ", lts.get_UVA())
	print("[Light   ] UVB: ", lts.get_UVB())
	print("[Light   ] UVI: ", lts.get_UVI())


# Dictionary containing functions
func_dic = {"0" : read_thg, "3" : read_mq2, "2" : read_hum,
			"4" : read_lts, "1" : read_lis}

# Dictionaries with available modes
modes = {"All sensors" : 1, "Single sensor" : 2}


# Function used to navigate through dictionaries
# and to select 
def menu(crs, base):
	print(chr(27) + "[2J")
	print("[e2 Multisensor]")
	print(crs)
	for index, key in enumerate(base):
		if crs == index:
			print("[*]", end = '')
			print(key)
		else:
			print("[ ]", end = '')
			print(key)

# Select mode
# Single sensor to receive readings from only one sensor
# All sensors to continously receive readings from all sensors
def select_mode():
	print("Select mode")
	cursor = 0
	while True:
		if joy.get_state() == 0:
			sleep(0.06)
			cursor+=1
			if cursor > 1:
				cursor = 0
			menu(cursor, modes)
		if joy.get_state() == 1:
			sleep(0.06)
			cursor-=1
			if cursor < 0:
				cursor = 1
			menu(cursor, modes)
		if joy.get_state() == 244:
			return cursor
		sleep(0.03)

# Select sensor in single mode
def select_sensor():
	print("Select sensor. Push the button to navigate")
	print("Hold to confirm")
	cursor = 0
	while True:
		if joy.get_state() == 0:
			sleep(0.06)
			cursor+=1
			if cursor > 4:
				cursor = 0
			menu(cursor, dic)
		if joy.get_state() == 1:
			sleep(0.06)
			cursor-=1
			if cursor < 0:
				cursor = 4
			menu(cursor, dic)
		if joy.get_state() == 244:
			return cursor
		sleep(0.03)

# main loop
while True:
	choice = 0
	mode = str(select_mode())
	sleep(1)
	if mode == "0":
		choice = str(select_sensor())
		while True:
			func_dic[choice]()
			sleep(0.6)
			if joy.get_state() == 244:
				sleep(1)
				break

	if mode == "1":
		while True:
			for key in func_dic:
				func_dic[key]()
				sleep(1)
			if joy.get_state() == 244:
				sleep(1)
				break
