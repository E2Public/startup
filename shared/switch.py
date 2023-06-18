import shutil
import glob
import sys
import os
import io

MAIN_DIRECTORY = 'main'
PROJECTS_DIRECTORY = 'demos'

class demoProject:
	loadedFile = ".loaded"

	def __init__(self, dir, description = None):
		self.dir = dir
		self.techname = os.path.basename(os.path.normpath(dir))
		if description == None:
			self.loadDescription()
		else:
			self._desc = description

	def loadDescription(self):
		try:
			rl = ""
			desc_dir = MAIN_DIRECTORY if self.isLoaded() else self.dir
			with open(os.path.join(desc_dir, 'README.md'), "r") as f:
				while len(rl) < 2:
					rl = f.readline()
			self._desc = rl.strip(" \r\n#*")
		except Exception as e:
			self._desc = '*** No description available ***'

	@property
	def loadCtrlFile(self):
		return os.path.join(self.dir, demoProject.loadedFile)

	@property
	def description(self):
		return self._desc
	
	def isLoaded(self):
		return os.path.exists(self.loadCtrlFile)

	def load(self, locationDir):
		if self.isLoaded():
			return
		for mfile in glob.glob(os.path.join(self.dir, '*')):
			shutil.move(mfile, locationDir)
		with open(self.loadCtrlFile, "w") as f:
			f.write(".")

	def unload(self, locationDir):
		if not self.isLoaded():
			return
		os.remove(self.loadCtrlFile)
		for mfile in glob.glob(os.path.join(locationDir, '*')):
			shutil.move(mfile, self.dir)

def main():
	paths = [path for path in glob.glob(os.path.join(PROJECTS_DIRECTORY, '*'))]
	paths.sort()
	projects = [ demoProject(pdir) for pdir in paths]
	print("Available projects:")
	i = 1
	for p in projects:
		print("%2d. [%-20s] %-50s %s" % (i, p.techname, p.description, "(loaded)" if p.isLoaded() else ""))
		i = i + 1
	print("")
	print("Please enter project number to load, or anything else to cancel.")
	v = input('--> ')
	va = 0
	try:
		va = int(v)
	except Exception as e:
		va = -1
	if va >= 1 and va <= len(projects):
		va = va-1
		for p in projects:
			if p.isLoaded():
				p.unload(MAIN_DIRECTORY)
				print("Unloaded project %s." % p.description)
		q = projects[va]
		q.load(MAIN_DIRECTORY)
		print("Loaded project %s." % q.description)
		print("Cleaning...")
		shutil.rmtree('.pio', ignore_errors=True)
		print("Done!")
	else:
		print("No changes done.")

if __name__ == "__main__":
	main()
