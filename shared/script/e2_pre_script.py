Import("env")

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from os.path import basename, isfile, join
from pathlib import Path

import collections
import argparse
import hashlib
import sys
import io
import os
import re

def _file_long_data_workaround(env, _data):
	data = env.subst(_data).replace("\\", "/")
	build_dir = env.subst("$BUILD_DIR")
	tmp_file = join(
		build_dir, "longcmd-%s" % hashlib.md5(data.encode()).hexdigest()
	)
	retval = '@"%s"' % tmp_file
	if not isfile(tmp_file):
		with open(tmp_file, "w") as fp:
			fp.write(data)
	return retval

def implant_hook_for_libflags():
	env.Replace(_long_libflags_hook=_file_long_data_workaround)
	coms = {}
	key = "LINKCOM"
	t = env.get(key, "").replace(
		"$_LIBFLAGS", "${_long_libflags_hook(__env__, _LIBFLAGS)}"
	)
	if not t.startswith("${TEMPFILE('$LINK"):
		coms[key] = t
		env.Replace(**coms)

def anybase_int(string):
	return int(string,0)

def load_options(config, section, names, specific = True, die_on_fail = False):
	out = {}
	for option_name in names:
		try:
			out[option_name] = config.get(section + ("" if not specific else (":" + env.get("PIOPLATFORM"))), option_name)
		except configparser.NoOptionError as e:
			if die_on_fail:
				print(e)
				sys.exit(1)
			else:
				out[option_name] = None
	return out

baseconfig = configparser.ConfigParser()
baseconfig.read(env.get("PROJECT_CONFIG"))

common_options = load_options(baseconfig, 'env:'+env.get('PIOENV'), ['mode'], False, True)

if common_options['mode'] not in ['master', 'master_merged']:
	print('Invalid mode %s in environment %s' % (common_options['mode'], 'env:'+env.get('PIOENV')))
	sys.exit(1)

env.Prepend(
	E2_PROCESS_MODE=common_options['mode']
)

implant_hook_for_libflags()

mergeconfig = configparser.ConfigParser()
if env.get('E2_PROCESS_MODE') == 'master_merged':
	try:
		mergeconfig.read(join(env.get("PROJECT_SRC_DIR"), 'merge.ini'))
	except Exception as e:
		print('Issue accessing merge.ini, exception details follow...')
		print(e)
		sys.exit(1)

# dump environment for debug
# debug_dir = join(env.get('PROJECT_BUILD_DIR'), 'debug')
# env.Execute(Mkdir(debug_dir))
# dump_file = join(env.get('PROJECT_BUILD_DIR'), 'debug', 'pre-%s-%s.txt' % (env.get('PIOPLATFORM'), env.get('PIOENV')))
# with open(dump_file, 'w') as f:
# 	print("Pre platform script", file=f)
# 	print("*********** ENV", file=f)
# 	print(env.Dump(), file=f)
