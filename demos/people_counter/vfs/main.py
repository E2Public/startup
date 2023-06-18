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

dis1 = e2.distancesensor(0)
dis2 = e2.distancesensor(1)
rgb = e2.rgbled(0)
buz = e2.buzzer(0)
seg = e2.segmentdisplay(0)
joy = e2.joystick(0)


dis1.set_timing_budget(dis1.TB020MS)
dis2.set_timing_budget(dis2.TB020MS)
buz.set_frequency(2000)

def config():
	print("SET UP A MAXIMUM AMOUNT OF PEOPLE THAT CAN ENTER")
	print("Move joystick UP/DOWN to add or remove units")
	print("Hold the joystick to confirm")
	rgb.set_rgb(0,0,255)
	counter = 0
	buz.sound_off()
	while True:
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
		# CENTER to confirm
		if joy.get_state() == 244:
			rgb.set_all(0)    
			break
	return counter


people_counter = 0

state3_old = 0
state4 = 0

def get_count():

	distance1 = dis1.get_distance()
	distance2 = dis2.get_distance()

	state1 = 0
	state2 = 0
	state3 = 0
	global state3_old
	global state4
	global people_counter
	
	if distance1 < 500:
		state1 = 1
	elif distance1 > 750:
		state1 = 0

	if distance2 < 500:
		state2 = 1
	elif distance2 >750:
		state2 = 0

	state3 = state2*2 + state1
	if state3 == 2:
		state3 = 3
	elif state3 == 3:
		state3 = 2
	
	if state3 != state3_old:
		diff = state3 - state3_old
		state3_old = state3
		if diff > 2:
			diff = diff -4
		elif diff < -2:
			diff = diff + 4					
		
		state4 = state4 + diff
		people_counter = state4//4





buzz_state = False
def buzz(state,error):
	global buzz_state

	if state != buzz_state:
		buzz_state = state
		if buzz_state:
			buz.sound_on()
			if error:
				rgb.set_rgb(255,0,0)
			else:
				rgb.set_all(128)
		else:
			buz.sound_off()
			rgb.set_all(0)


beep_count = 0
def beep_update(state):
	global beep_count
	if state:
		if beep_count%10 < 5:
			buzz(True,True)
		else:
			buzz(False,True)

		beep_count = beep_count + 1

	else:
		buzz(False,True)
		beep_count = 0

short_beep_count = 0
def short_beep(state):
	global short_beep_count


	if state or short_beep_count !=0:
		if short_beep_count%2 < 1:
			buzz(True,False)
		else:
			buzz(False,False)
		
	
		if short_beep_count < 2*4:
			short_beep_count = short_beep_count + 1
		else:
			short_beep_count = 0







def guard(limit):

	global people_counter
	people_counter_old = 0
	
	while True:
		get_count()
		if people_counter < 0:
			people_counter = 0
		
		str = "%2dc" % (people_counter)
		seg.display_string([elem.encode()[0] for elem in str])
		
		if people_counter > limit:
			beep_update(1)
			short_beep(False)
		else:	
			if people_counter_old != people_counter:
				people_counter_old = people_counter
				short_beep(True)
				beep_update(0)
			else:
				beep_update(0)
				short_beep(False)
		
		sleep(0.01)



while True:
	buz.sound_off()
	max_seats = config()
	guard(max_seats)

