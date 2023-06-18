import e2

print("Connected blocks:")
_x_dir = {}
for _x_i in e2.current_devices_list():
	_x_dir[type(_x_i).__name__] = 1 + _x_dir.get(type(_x_i).__name__, 0)
for _x_i in _x_dir.keys():
	print("\t- %2d * %s" % (_x_dir[_x_i], _x_i))

print('')
