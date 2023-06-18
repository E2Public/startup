# author : Chris Idema
# created: 11.12.2020
#

import e2
from time import sleep
import blynklib_mp as BlynkLib
import network
import socket
import ure

#typedef enum { IDLE = 0, INVALID_CALL=1, BUSY = 2, DONE_OK = 3, DONE_ERROR=4} gsm_request_state;

GSM_IDLE = 0
GSM_INVALID_CALL = 1
GSM_BUSY = 2
GSM_DONE_OK = 3
GSM_DONE_ERROR = 4

gsm = e2.gsm(0)

print("GSM TEXT MESSAGE DEMO")

with open("data/motd.txt","r") as f:
    print(f.read())

print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
    _x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
    print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')

def print_error():
	error = gsm.get_CME_error()
	if error != 0:
		print("CME Error: ",error)
		# see for more error codes: https://www.g1sat.com/faq-2/list-of-cme-error-codes/
		if error == 10:
			print("SIM not inserted")


modem_state = False

def send_sms(phonenumber,message):
	global modem_state
	if modem_state == False:
		print('Starting gsm...')
		gsm.startup()	

		state = gsm.get_request_state() 

		while state == GSM_BUSY:		
			sleep(1)
			state = gsm.get_request_state() 	

		if state == GSM_DONE_OK:
			print('Started gsm')
			modem_state = True
		elif state== GSM_IDLE:
			print('Device has reset' )
		elif state== GSM_DONE_ERROR:
			print("Starting gsm failed.")
			print_error()
		else:
			print('Unknown state! ',state )
	
	if modem_state == True:
		print('Sending SMS...')
		gsm.send_sms(phonenumber,message)

		state = gsm.get_request_state() 

		while state == GSM_BUSY:		
			sleep(1)
			state = gsm.get_request_state() 

		if state == GSM_DONE_OK:
			print('SMS send!')			
		elif state == GSM_DONE_ERROR:
			print("Sending sms failed.")
			print_error()
			modem_state = False  
		elif state== GSM_IDLE:
			print('Device has reset' )
			modem_state = False  
		else:
			print('Unknown state! ',state )
			modem_state = False  




while True:
	phonenumber = input('Enter phone number in national format: ')	
	message = input('Please enter message: ')

	send_sms(phonenumber,message)


	    
