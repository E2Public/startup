# author : Igor Rybakowski
# created: 29.11.2020

# To do:

import e2
from time import sleep

# Print out the block that are connected to the motherboard
print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
	_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
	print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')

# Modules initialization
seg = e2.segmentdisplay(0)
rgb = e2.rgbled(0)
buz = e2.buzzer(0)
joy = e2.joystick(0)

print("[electron square] Timer")

# Set up time of the countdown
def config():
	print("SET UP A TIMER")
	print("Move joystick UP/DOWN to set up time counter")
	print("LEFT/RIGHT to add or substract minutes")
	rgb.set_rgb(0,255,0)
	buz.sound_off()
	counter = 0
	# while True:
	# 	print(joy.get_state())
	# 	sleep(0.1)
	while True:
		print(counter)
		str = "%2dc" % (counter)
		seg.display_string([elem.encode()[0] for elem in str])
		# UP to add seconds
		if joy.get_state() == 1:
			if counter < 999:
				counter+=1
				sleep(0.06)
		# DOWN to substract seconds
		if joy.get_state() == 0:
			if counter > 0:
				counter-=1
				sleep(0.06)
		# LEFT to add 60 seconds
		if joy.get_state() == 3:
			if (counter + 60) < 999:
				counter+=60
				sleep(0.06)
		# RIGHT to remove 60 seconds
		if joy.get_state() == 2:
			if (counter - 60) > 0:
				counter-=60
				sleep(0.06)
		# CENTER to confirm
		if joy.get_state() == 244:
			beep()       
			break
	return counter

# This function counts down the time with 1 second
# The parameter is the countdown time
def countdown(time):
	r_val = 0
	g_val = 60
	buz.sound_off()
	while time != -1:
		str = "%2dc" % (time)
		seg.display_string([elem.encode()[0] for elem in str])
		time-=1
		if time > 9:
			buz.sound_off()
			rgb.set_rgb(0,255,0)
			sleep(0.5)
			rgb.set_all(0)
			sleep(0.5)
		else : 
			buz.sound_on()
			rgb.set_rgb(255,0,0)
			sleep(0.5)
			buz.sound_off()
			rgb.set_all(0)
			sleep(0.5)
			
		
		
# Function that does BEEEP!
def beep():
	while joy.get_state() == 4:
		rgb.set_rgb(0,0,255)
		buz.sound_on()
		sleep(0.1)
		rgb.set_all(0)
		buz.sound_off()
		sleep(0.1)
	buz.sound_off()
	rgb.set_all(0)


# Main loop of the program
while True:
	buz.set_frequency(500)
	counter = 0
	time = config()
	countdown(time)
	beep()


