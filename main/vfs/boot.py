# sample python program that runs at boot

# message of the day
with open("data/motd.txt","r") as f:
	print(f.read())

# try running webrepl
ssid = 'ElectronSquare'
try:
	import network
	ap = network.WLAN(network.AP_IF) # create access-point interface
	ap.config(essid=ssid) # set the ESSID of the access point
	ap.config(max_clients=4) # set how many clients can connect to the network
	ap.active(True)         # activate the interface

	import webrepl
	webrepl.start()

	from webrepl_cfg import PASS
	print("Access WebREPL client at http://micropython.org/webrepl/")
	print("Connect to WIFI '%s'" % ssid)
	print("WebREPL password is: %s" % PASS)
except Exception as e:
	print("WIFI is not available on this device")

print('')
