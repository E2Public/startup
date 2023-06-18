# sample python program that runs at boot

# message of the day
with open("data/motd.txt","r") as f:
	print(f.read())

print('')
