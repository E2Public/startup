Import("env")

import sys
import subprocess
def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

assume_remote_mode = False

try:
	Import("projenv")
except Exception as e:
	assume_remote_mode = True

if not assume_remote_mode:
	try:
		from littlefs import LittleFS
	except:
		install("littlefs-python")
		from littlefs import LittleFS

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from os.path import basename, isfile, join
from zipfile import ZipFile
from pathlib import Path

import collections
import argparse
import hashlib
import socket
import types
import glob
import json
import io
import os
import re

args = types.SimpleNamespace()

def libapi_builder_function(env, target, source):
	nregex = r"^0[0-9a-fA-F]{6,}\s+([g\*]).*0[0-9a-fA-F]{6,}\s(.*)$"
	regex = r"(.*)lib(ElectronSquare.*API)\.a"
	objfiles = {}
	newobjfiles = []
	globalsyms = {}
	undefsyms = {}
	mulsyms = []
	working_path = join(env.get("PROJECT_BUILD_DIR"), env.get("PIOENV"), "apibuild")
	# cleanup tmp dir
	# find object files for libraries (global, undefined) and capture
	for libfile in source:
		matches = re.match(regex, str(libfile), re.MULTILINE)
		if matches:
			lowcase_libname = matches.group(2).lower()
			objfiles[lowcase_libname] = []
			path = join(matches.group(1), matches.group(2))
			for ofile in env.Glob(join(path,'*.o')):
				objfiles[lowcase_libname].append(ofile)
	prefix = projenv.get("AR")[0:-2]
	for lowcase_libname in objfiles.keys():
		globalsyms[lowcase_libname] = []
		undefsyms[lowcase_libname] = []
		for ofile in objfiles[lowcase_libname]:
			cout = os.popen("%sobjdump -t %s" % (prefix, ofile)).read()
			matches = re.finditer(nregex, cout, re.MULTILINE)
			for match in matches:
				symboltype = match.group(1)
				symbolname = match.group(2)
				if symboltype == 'g':
					globalsyms[lowcase_libname].append(symbolname)
				else:
					undefsyms[lowcase_libname].append(symbolname)
	for slave_family in read_slave_families():
		libname_lowcase = "electronsquare%sapi" % slave_family
		count = sum([1 if s['family'] == slave_family else 0 for s in read_slave_directory()])
		print(libname_lowcase, count)
		for idx in range(0,count):
			psyms = []
			psyms.extend([[gsym, '__%s_%d_e2_api_%s_%s' % (slave_family,idx,slave_family,gsym)] for gsym in globalsyms[libname_lowcase]])
			mulsyms.extend([[slave_family, idx, sym, dsym] for (sym, dsym) in psyms])
			psyms.extend([['e2_parameter_assign','__e2_%s_%d_parameter_assign' % (slave_family, idx)]])
			mapfile = join(working_path, "sym_map_%s_%d.txt" % (slave_family, idx))
			with open(mapfile, 'w') as mapfileio:
				for psym in psyms:
					mapfileio.write("%s %s\n" % (psym[0],psym[1]))
			for objfile in objfiles[libname_lowcase]:
				newobjfile = "%s_%s_%s" % (slave_family, idx, os.path.basename(str(objfile)))
				newobjfilepath = join(working_path, newobjfile)
				cmdline = "%sobjcopy --redefine-syms=\"%s\" %s %s" % (prefix, mapfile, objfile, newobjfilepath)
				act = env.VerboseAction(cmdline, "Cloning objectfile %s for slave family %s, index %d" % (objfile, slave_family, idx))
				env.Execute(act)
				newobjfiles.append(newobjfilepath)
	# create library and corresponding C file
	for utarget in target:
		if str(utarget).endswith('.a'):
			car = "%sar rs %s %s" % (prefix, str(utarget), ' '.join(newobjfiles))
			aract = env.VerboseAction(car, "Linking merged slaves library")
			env.Execute(aract)
		if str(utarget).endswith('.c'):
			dmaps = {}
			for msym in mulsyms:
				key = "__%s_all_e2_api_%s_%s" % (msym[0], msym[0], msym[2])
				val = "__%s_%d_e2_api_%s_%s" % (msym[0], msym[1], msym[0], msym[2])
				if key not in dmaps:
					dmaps[key] = []
				dmaps[key].append([msym[1],val])
			defs = []
			links = []
			for section in dmaps:
				dmaps[section].sort()
				ctr = 0;
				defs.extend(["extern void (*%s[])() __attribute__ ((weak));" % section])
				defs.extend(["extern void %s();" % name[1] for name in dmaps[section]])
				links.extend(["\tif (%s != NULL) { ESP_LOGD(\"Gen mapper\", \"assigning %s[%d] = %s @ %%p\",%s); %s[%d] = %s; }" % (section, section, name[0], name[1], name[1], section, name[0], name[1]) for name in dmaps[section]])
			cout = """#include <stddef.h>
#include "esp_log.h"
%s
void __e2_merged_initializer() {
%s
}
			""" % ('\n'.join(defs), '\n'.join(links))
			gen_output(str(utarget), cout)

def setup_interim_directory(env):
	interim_dir = join(env.get('PROJECT_BUILD_DIR'), env.get('PIOENV') , "apibuild")
	env.Execute(Mkdir(interim_dir))
	return interim_dir

def gen_output(fname, fdata, times=None):
	with open(fname, 'w') as f:
		os.utime(fname, times)
		if fdata is not None:
			f.write(fdata)

def libname_is_api(libname):
	mre = re.compile("(.*)(\\W|lib)ElectronSquare([A-Za-z0-9_]+)API(\\.a)?");
	if re.match(mre, libname):
		return True
	return False

def libname_matches(libname, matchname):
	mre = re.compile("(.*)(\\W|lib)ElectronSquare(?i:%s)(\\.a)?" % matchname);
	if re.match(mre, libname):
		return True
	return False

def findlib(e2libname):
	thelib = None
	for lib in projenv.get('LIBS'):
		name = lib
		if not isinstance(name, str):
			name = name[0];
		name = str(name)
		if libname_matches(name, e2libname):
			thelib = name
	return thelib

def exec_ar_add_command(name, library, binary_objects):
	arc = "%s r %s %s" % (
			projenv.get('AR'),
			str(library),
			' '.join([str(binary_object[0]) for binary_object in binary_objects])
		)
	return env.VerboseAction(arc, name)

def get_merge_config():
	mergeconfig = configparser.ConfigParser()
	mergeconfig.read(join(env.get("PROJECT_SRC_DIR"), 'merge.ini'))
	return mergeconfig

def read_slave_directory():
	slaveidmap = {}
	mergeconfig = get_merge_config()
	slaves = mergeconfig.sections()
	ret = []
	for slave in slaves:
		if slave.startswith('slave:'):
			family = mergeconfig.get(slave, 'family')
			if family in slaveidmap:
				slaveidmap[family] += 1
			else:
				slaveidmap[family] = 0
			ret.append({
				"entry":slave,
				"family":family,
				"seq":slaveidmap[family]
				})
	return ret

def read_slave_families():
	return list(dict.fromkeys([c['family'] for c in read_slave_directory()]))

def single_pinmapper(slave_name, family_name, seq_number):
	maps = []
	config = get_merge_config()
	for mapping in config.get(slave_name, 'mapping').split():
		(point, data) = mapping.split(':')
		(point_name, point_id) = point[0:-1].split('[')
		maps.append("\tif ((per_type == PERIPHERAL_%s) && (p_id == %s)) return %s;" % (point_name, point_id, data));
	return """int __e2_%s_%d_parameter_assign(e2_peripheral_type_t per_type, int p_id, int def_val) {
	ESP_LOGV("Gen code", "parameter assigned started");
%s
	ESP_LOGV("Gen code", "parameter assigned failed");
	assert(NULL);
	return -1;
}""" % (family_name, seq_number, '\n'.join(maps))

def pinmap_builder_function(env, target, source):
	print("E2 pinmap builder @ %s" % (target[0]))
	lines = ['#include <assert.h>', '#include <stdint.h>', '#include <stdbool.h>', '#include <e2.h>', '#include "esp_log.h"']
	mergeconfig = get_merge_config()
	slave_directory = read_slave_directory()
	lines.extend([single_pinmapper(s['entry'], s['family'], s['seq']) for s in slave_directory])
	genfile = '\n\n'.join(lines)
	for utarget in target:
		gen_output(str(utarget), genfile)

def slave_enum_builder_function(env, target, source):
	slaves = read_slave_directory()
	families = read_slave_families()	
	slaves_setup_code = '\n'.join(["\t__local_e2_slave_addp(E2_%s_FAMILY_ID_NUMBER,%d);" % (c['family'].upper(), c['seq']) for c in slaves])
	includes = ['#include <assert.h>', '#include "e2.h"', '#include "e2libs.h"', '#include "esp_log.h"']
	# includes.extend(["#include \"e2_c_api_%s.h\"" % fname for fname in families])
	gen = """%s

extern e2_devices_list_t e2_devices_list;

static void __local_e2_slave_addp(uint16_t family, uint8_t id) {
	ESP_LOGD("Gen code", "slave enumerated");
	e2_devices_list_t current = (e2_devices_list_t)malloc(sizeof(struct e2_devices_list_s));
	current->next = e2_devices_list;
	current->family = family;
	current->id = id;
	current->address = 0x0;
	e2_devices_list = current;
}

void e2_merged_static_slave_enumerator() {
	ESP_LOGD("Gen code", "static slave enumerator");
	e2_devices_list = NULL;
%s
}""" % ('\n'.join(includes), slaves_setup_code)
	for utarget in target:
		gen_output(str(utarget), gen)

def slave_mapping():
	setup_interim_directory(env)

	pinmap_gen = env.Command(
		join(env.get("BUILD_DIR"), "apibuild", "pinmap.c"),
		join(env.get("PROJECT_SRC_DIR"), 'merge.ini'),
		pinmap_builder_function
	)
	pinmap_bin = projenv.Object(pinmap_gen)

	slave_enum_gen = env.Command(
		join(env.get("BUILD_DIR"), "apibuild", "slave_enum.c"),
		join(env.get("PROJECT_SRC_DIR"), 'merge.ini'),
		slave_enum_builder_function
	)
	slave_enum_bin = projenv.Object(slave_enum_gen)

	core_lib = findlib('Core')
	env.Depends(core_lib, pinmap_bin)
	env.Depends(core_lib, slave_enum_bin)
	projenv.AddPostAction(core_lib, exec_ar_add_command("Update core lib with pinmap and slave enumerator", core_lib, [pinmap_bin, slave_enum_bin]))

def api_replicator():
	# find api libs
	apilibs = []
	for tlib in env.get("LIBS"):
		name = tlib
		if not isinstance(name, str):
			name = name[0];
		name = str(name)
		if libname_is_api(name):
			apilibs.append(tlib)

	# generate mixed lib and merging code
	lib_target = join("$BUILD_DIR", "apibuild", "libe2projmerged.a")
	cmix_target = join("$BUILD_DIR", "apibuild", "mergedmap.c")
	mixlib_gen = env.Command(
		[lib_target, cmix_target],
		apilibs,
		libapi_builder_function
	)
	cmix_compiled_target = projenv.Object(cmix_target)

	env.Append(LIBS='e2projmerged')
	env.Append(LIBPATH=join("$BUILD_DIR", "apibuild"))
	env.Depends(mixlib_gen, apilibs)
	env.Depends("$BUILD_DIR/$PROGNAME$PROGSUFFIX", lib_target)

	apis_lib = findlib('APIs')
	env.Depends(apis_lib, cmix_compiled_target)
	projenv.AddPostAction(apis_lib, exec_ar_add_command("Update APIs lib with cloned merge calls", apis_lib, [cmix_compiled_target]))

def _parse_size(value):
	if isinstance(value, int):
		return value
	elif value.isdigit():
		return int(value)
	elif value.startswith("0x"):
		return int(value, 16)
	elif value[-1].upper() in ("K", "M"):
		base = 1024 if value[-1].upper() == "K" else 1024 * 1024
		return int(value[:-1]) * base
	return value

def _parse_partitions(env, direct = False):
	if not direct == False:
		partitions_csv = direct
	else:
		partitions_csv = env.subst("$PARTITIONS_TABLE_CSV")
	if not isfile(partitions_csv):
		sys.stderr.write("Could not find the file %s with partitions "
						 "table.\n" % partitions_csv)
		env.Exit(1)
		return

	result = []
	next_offset = 0
	with open(partitions_csv) as fp:
		for line in fp.readlines():
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			tokens = [t.strip() for t in line.split(",")]
			if len(tokens) < 5:
				continue
			partition = {
				"name": tokens[0],
				"type": tokens[1],
				"subtype": tokens[2],
				"offset": tokens[3] or next_offset,
				"size": tokens[4],
				"flags": tokens[5] if len(tokens) > 5 else None
			}
			result.append(partition)
			next_offset = (_parse_size(partition['offset']) +
						   _parse_size(partition['size']))
	return result

def littlefs_builder(target, source, env):
	vfsdir = env.subst('$E2MPYVFSDIR')
	vfsdirlen = len(vfsdir)
	bsize = 4096
	psize = int(env.get('E2MPYVFSPARTSIZE'))
	bcount = psize // bsize
	fs = LittleFS(block_size=bsize, block_count=bcount)
	for fsrcfile in source[:-1]:
		srcfile = fsrcfile.get_abspath()
		base_name = srcfile[vfsdirlen:].replace(os.sep, '/')
		if os.path.isdir(srcfile):
			fs.mkdir(base_name)
		else:
			with open(srcfile, 'rb') as sfh:
				with fs.open(base_name, 'w') as tfh:
					data = sfh.read()
					tfh.write(data)
	with open(str(target[0]), 'wb') as fh:
		fh.write(fs.context.buffer)
	print("littlefs built, %d blocks, %d bytes" % (bcount, bcount*bsize))

def vfs_build_esp32_port():
	if not env.get("PARTITIONS_TABLE_CSV"):
		raise ValueError("missing partition table reference")
	vfspartsd = [
		(_parse_size(p['offset']), _parse_size(p['size'])) 
			for p in _parse_partitions(env) if p['name'] == "vfs"
	]
	if vfspartsd:
		fsbin = join("$BUILD_DIR", "fsdata.bin")
		vfsdir = join("$PROJECT_SRC_DIR", 'vfs')
		env.Replace(E2MPYVFSDIR=vfsdir)
		fs_sources = env.Glob(join("$E2MPYVFSDIR", '*'))
		fs_sources.extend(env.Glob(join("$E2MPYVFSDIR", '*', '*')))
		fs_sources.extend(env.Glob(join("$E2MPYVFSDIR", '*', '*', '*')))
		fs_sources.extend(env.Glob(join("$E2MPYVFSDIR", '*', '*', '*', '*')))
		fs_sources.append(env.File(join('$PROJECT_DIR', 'shared', 'script', 'partitions.csv')))
		env.Append(UPLOADERFLAGS=[
			'0x%x'%vfspartsd[0][0], fsbin
		])
		env.Replace(E2MPYVFSPARTSIZE=vfspartsd[0][1])
		fsdata_gen = env.Command(
			fsbin,
			fs_sources,
			littlefs_builder
		)
		upload_b = env.Alias("vfsbin", [fsdata_gen])
		env.Depends("$BUILD_DIR/$PROGNAME$PROGSUFFIX", [fsdata_gen])

def complete_offset_towards(value, curroffset, filehandle, filename):
	dist = value - curroffset
	if dist > 0:
		print("padding concatenated ESP32 binary, current offset 0x%x, expected 0x%x, before file %s" % (curroffset, value, filename))
		filehandle.write(bytearray([0xff] * dist))
	if dist < 0:
		raise Exception("invalid input for concatenated ESP32 binary, current offset 0x%x, value 0x%x, file %s" % (curroffset, value, filename))
	return value

def concat_builder_esp32(target, source, env):
	master_bin_name = env.subst("$PROGNAME${'.bin'}")
	partitions_data_file_name = env.File(join('$PROJECT_DIR', 'shared', 'script', 'partitions.csv')).get_abspath()
	partitions_parsed = [(p['name'], _parse_size(p['offset']), _parse_size(p['size'])) 
			for p in _parse_partitions(env, partitions_data_file_name)]
	offset_vfs = 0
	offset_factory = 0
	for pdata in partitions_parsed:
		if pdata[0] == 'vfs':
			offset_vfs = pdata[1]
		if pdata[0] == 'factory':
			offset_factory = pdata[1]
	offset = 0x1000
	with open(str(target[0]), 'wb') as fh:
		for fsrcfile in source:
			srcfile = fsrcfile.get_abspath()
			if srcfile.endswith('bootloader.bin'):
				offset = complete_offset_towards(0x1000, offset, fh, srcfile)
			if srcfile.endswith('partitions.bin'):
				offset = complete_offset_towards(0x8000, offset, fh, srcfile)
			if srcfile.endswith('fsdata.bin'):
				offset = complete_offset_towards(offset_vfs, offset, fh, srcfile)
			if srcfile.endswith(master_bin_name):
				offset = complete_offset_towards(offset_factory, offset, fh, srcfile)
			with open(srcfile, 'rb') as sfh:
				data = sfh.read()
				fh.write(data)
				offset = offset + len(data)

def define_concat_binary_esp32():
	bootloader_bin_file = join('$BUILD_DIR','bootloader.bin')
	partitions_bin_file = join('$BUILD_DIR','partitions.bin')
	vfs_bin_file = join('$BUILD_DIR','fsdata.bin')
	firmware_bin_file = "$BUILD_DIR/$PROGNAME${'.bin'}"
	complete_bin_file = join("$BUILD_DIR", "e2-complete-esp32-0x1000.bin") # env.File(join('$PROJECT_BUILD_DIR','$PIOENV','e2-complete-esp32-0x1000.bin'))
	concat_bin = env.Command(
		complete_bin_file,
		[bootloader_bin_file, partitions_bin_file, firmware_bin_file, vfs_bin_file],
		concat_builder_esp32
	)
	complete_bin_alias = env.Alias("concatbin", [concat_bin])
	env.Depends("concatbin", ["$BUILD_DIR/$PROGNAME$PROGSUFFIX"])

# in pio-remote scenario this runs on the remote server and is the central build place
if not assume_remote_mode:
	if env.get('E2_PROCESS_MODE') == 'master_merged':
		slave_mapping()
		api_replicator()
	if env.get('PIOPLATFORM') == 'espressif32':
		vfs_build_esp32_port()
		define_concat_binary_esp32()

# in pio-remote scenario this runs on the user box (that is the "remote" from the server perspective)
if assume_remote_mode:
	# TODO : consider different platforms, below code applicable only to ESP32
	partitions_data_file_name = env.File(join('$PROJECT_DIR', 'shared', 'script', 'partitions.csv')).get_abspath()
	partitions_parsed = [(p['name'], _parse_size(p['offset']), _parse_size(p['size'])) 
			for p in _parse_partitions(env, partitions_data_file_name)]
	bootloader_bin_file = env.File(join('$PROJECT_BUILD_DIR','$PIOENV','bootloader.bin'))
	partitions_bin_file = env.File(join('$PROJECT_BUILD_DIR','$PIOENV','partitions.bin'))
	vfs_bin_file = env.File(join('$PROJECT_BUILD_DIR','$PIOENV','fsdata.bin'))	
	if vfs_bin_file.exists():
		for pdata in partitions_parsed:
			if pdata[0] == 'vfs':
				env.Append(UPLOADERFLAGS=[
					'0x%x' % pdata[1], vfs_bin_file.get_abspath()
				])
	env.Append(UPLOADERFLAGS=[
		'0x%x' % 0x1000, bootloader_bin_file.get_abspath()
	])
	env.Append(UPLOADERFLAGS=[
		'0x%x' % 0x8000, partitions_bin_file.get_abspath()
	])

# # dump complete environment
# dump_file = join(env.get('PROJECT_BUILD_DIR'), 'debug', 'post-%s-%s.txt' % (env.get('PIOPLATFORM'), env.get('PIOENV')))
# def dump(list, file):
# 	if list is None:
# 		print(list)
# 	else:
# 		for i in list:
# 			print(i, file=file)
# piobuildfiles = None
# try:
# 	piobuildfiles = projenv.get('PIOBUILDFILES')
# except Exception:
# 	piobuildfiles = env.get('PIOBUILDFILES')
# with open(dump_file, 'w') as f:
# 	print("Post platform script", file=f)
# 	print("*********** ENV", file=f)
# 	print(env.Dump(), file=f)
# 	print("*********** PROJENV", file=f)
# 	print(projenv.Dump(), file=f)
# 	print("Build files", file=f)
# 	dump(piobuildfiles, f)
# 	print("Libs", file=f)
# 	dump(projenv['LIBS'], f)
