# author : Chris Idema
# created: 11.12.2020

import e2
from time import sleep

print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
	_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
	print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')

# ---------------------------------------

def display_clear():
	print(chr(27) + "[2J")

def pixel_on(x,y):
	print(' '*x +'*')
	pass

def pixel_off(x,y):
	print(' '*x +' ')
	pass

def pixel_write(x,y,brightness):
	pass

def scoreboard(score):
	pass

def buzzer(on):
	pass

def input_get():
	return 0

# ---------------------------------------


# import curses 
from random import randint
import e2
joy = e2.joystick(0)
display = e2.md8x8(0)
scoreboard = e2.segmentdisplay(0)
buz = e2.buzzer(0)
buz.set_frequency(2000)
buz.sound_off()
rgb = e2.rgbled(0)
rgb.set_rgb(0,0,0)


def write_rgb(r,g,b):
	rgb.set_rgb(r,g,b)
	print(chr(27) + "[1;10H",end='')#reset cursor to line 1 column 10
	print(chr(27) + "[48;2;"+str(r)+';'+str(g)+';'+str(b)+'m ',end='')        
	print(chr(27) + "[49m",end='')

def getch():
	c = -1
	if joy.get_state() == 0:
		c = ord('w')
	elif joy.get_state() == 1:
		c = ord('s')
	elif joy.get_state() == 2:
		c = ord('a')
	elif joy.get_state() == 3:
		c = ord('d')
	elif joy.get_state() == 244:
		c = 27

	return c



def newwin(y,x,a,b):
	display.set_all(0)
	
	scoreboard.display_string('   ')
	
	print(chr(27) + "[2J")#clear screen
	print(chr(27) + "[?25l")#hide cursor
	print(chr(27) + "[1;1H",end='')#reset cursor to line 1 column 1
	
	print()

	if y <= 2 or x <= 2:
		return 0
	
	print(' ' + '_'*(x*2-1) )
	for i in range(y):
		print('|'+' '*(x*2-1)+'|')
	print('^'*(x*2+1))

def write_block(y,x,c):
	
	if c == '#':
		print(chr(27) + "[31m",end='')            
		print(chr(27) + "["+str(y+3)+';'+str(x*2+2)+'H'+c)
		print(chr(27) + "[39m",end='')
		display.set_pixel(y,x,255)
	elif c == '*':
		print(chr(27) + "["+str(y+3)+';'+str(x*2+2)+'H'+c)
		display.set_pixel(y,x,64)
	elif c == ' ':
		print(chr(27) + "["+str(y+3)+';'+str(x*2+2)+'H'+c)
		display.set_pixel(y,x,0)


def write_score(score):
	s = str(score)
	s = ' '*(3-len(s))+s
	print(chr(27) + "[32m",end='')
	print(chr(27) + "[1;1H"+s,end='')#reset cursor to line 1 column 1
	print(chr(27) + "[39m",end='')
	scoreboard.display_string(' '*(3-len(s))+s)

	
#constants

width = 8
height = 8 

while True:
	newwin(height, width, 0, 0)
	
	write_rgb(0,0,0)
	buz.sound_off()

	# snake and food
	snake = [(4, 4), (4, 3), (4, 2)]
	food = (6, 6)

	write_block(food[0], food[1], '#')
	# game logic
	score = 0

	ESC = 27
	key = ord('d')

	while key != ESC:

		write_score(score)
		delay = 150 - (len(snake)) // 5 + len(snake)//10 % 120 # increase speed

		tick = 0
		while tick < delay:
			prev_key = key
			event = getch()
			if event != -1:
				key = event
			sleep(0.100)
			tick = tick + 100

		if key not in [ord('w'),ord('s'),ord('a'),ord('d'), ESC]:
			key = prev_key

		# calculate the next coordinates
		y = snake[0][0]
		x = snake[0][1]
		if key in [ord('s')]:
			y += 1
		elif key in [ord('w')]:
			y -= 1
		elif key in [ord('a')]:
			x -= 1
		elif key in [ord('d')]:
			x += 1
			
		# allow wrap around    
		y = (y + height) % height
		x = (x + width) % width

		snake.insert(0, (y, x)) # append O(n)

		# check if we hit the border
		if y == -1: break
		if y == height: break
		if x == -1: break
		if x == width: break


		# if snake runs over itself
		if snake[0] in snake[1:]: 
			write_rgb(128,0,0)
			sleep(3) 
			break

		if snake[0] == food:
			buz.sound_on()
			write_rgb(0,255,0)
			print('\a')
			sleep(0.020)
			buz.sound_off()
			write_rgb(0,0,0)
			# eat the food
			score += 1
			food = ()
			while food == ():
				food = (randint(0,height-1), randint(0,width-1))
				if food in snake:
					food = ()
			write_block(food[0], food[1], '#')
		else:
			# move snake
			last = snake.pop()
			write_block(last[0], last[1], ' ')

		write_block(snake[0][0], snake[0][1], '*')


	print(chr(27) + "[2J",end='') # clear display
	display.set_all(0)
	if key == ESC:
		print("Exiting game")
		break
	else:
		print("Final score = " + str(score))
		sleep(3) 
	

print(chr(27) + "[?25h") # show cursor again
