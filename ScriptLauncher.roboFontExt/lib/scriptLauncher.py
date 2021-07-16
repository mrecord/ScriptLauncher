#!/usr/bin/python
# coding: utf-8


import os
import vanilla
import plistlib
import configparser
from AppKit import NSScreen
from mojo.UI import StatusInteractivePopUpWindow, GetFolder, OpenScriptWindow


class scriptLauncher(object):

	def __init__(self):

		## Preference Files
		self.lastScriptFile = os.path.join("/".join(os.path.realpath(__file__).split("/")[:-1]), "lastscript.ini")
		self.preferencesFile = os.path.join("/".join(os.path.realpath(__file__).split("/")[:-1]), "preferences.ini")

		## Preference Defaults
		self.scriptsDirectory = os.path.join(os.getenv("HOME"), "Library/Application Support/RoboFont/scripts")
		self.extensionsDirectory = os.path.join(os.getenv("HOME"), "Library/Application Support/RoboFont/plugins")
		self.rememberLast = 1
		self.searchLocal = False
		self.searchUpDir = 3
		# Storage
		self.scripts = {"preferences" : ""} # scriptName : scriptPath

		## Window
		width = 500
		height = 200

		screen = NSScreen.mainScreen()
		screenRect = screen.frame()
		(screenX, screenY), (screenW, screenH) = screenRect
		screenY = -(screenY + screenH) # convert to vanilla coordinate system
		x = screenX + ((screenW - width) / 2)
		y = screenY + ((screenH - height) / 2)

		self.w = StatusInteractivePopUpWindow((x, y, width, height), screen=screen)

		self.w.search_box = vanilla.EditText((10, 10, -10, 21), "", callback=self.searchScripts)
		"""using EditText because SearchBox overrides tab and Enter buttons"""
		self.w.list = vanilla.List((10, 40, -10, -30), "", allowsMultipleSelection=0, doubleClickCallback=self.runScript)
		self.w.ok_button = vanilla.Button((10, -25, -10, 20), "Run Script", callback=self.runScript)

		# off Window
		self.w.closeWindow_button = vanilla.Button((10, 300, -10, 20), "Close Window", callback=self.closeWindow)
		self.w.prev_button = vanilla.Button((10, 300, -10, 20), "up", callback=self.previousScript)
		self.w.next_button = vanilla.Button((10, 300, -10, 20), "down", callback=self.nextScript)
		self.w.scriptingWindow_button = vanilla.Button((10, 300, -10, 20), "Open in ScriptingWindow", callback=self.openScriptInScriptingWindow)

		# Preferences Drawer

		self.d = vanilla.Drawer((100, 160), self.w, preferredEdge="bottom")
		self.w.togglePreferencesDrawer_button = vanilla.Button((10, 300, -10, 20), "Preferences", callback=self.togglePreferencesDrawer)

		self.d.title = vanilla.TextBox((10, 5, -10, 20), "Preferences")

		self.d.scripts_button = vanilla.Button((10, 30, 100, 20), "Scripts", callback=self.preferencesChanged)
		self.d.scripts_path = vanilla.TextBox((120, 30, -1, 20), "default: ~/Library/Application Support/RoboFont/scripts")
		self.d.extensions_button = vanilla.Button((10, 60, 100, 20), "Extensions", callback=self.preferencesChanged)
		self.d.extensions_path = vanilla.TextBox((120, 60, -10, 20), "default: ~/Library/Application Support/RoboFont/plugins")

		self.d.local_search_checkbox = vanilla.CheckBox((10, 95, 240, 20), "Search near open fonts for scripts", value=self.searchLocal, callback=self.preferencesChanged)
		self.d.local_search_title = vanilla.TextBox((250, 96, 120, 20), "Search up:")
		self.d.local_search_count = vanilla.PopUpButton((320, 95, 40, 22), ["0", "1", "2", "3", "4", "5", "6", "7"], callback=self.preferencesChanged)
		self.d.local_search_title2 = vanilla.TextBox((365, 96, -10, 20), "directories")

		self.d.remember_title = vanilla.TextBox((10, 130, 120, 20), "Remember Last:")
		self.d.remember_count = vanilla.PopUpButton((120, 128, 40, 22), ["0", "1", "2", "3", "4", "5",], callback=self.preferencesChanged)
		self.d.remember_title2 = vanilla.TextBox((170, 130, -10, 20), "scripts")


		self.readPreferences()
		self.lastScriptRead()

		# Bindings
		self.w.prev_button.bind("uparrow", [])
		self.w.next_button.bind("downarrow", [])
		self.w.setDefaultButton(self.w.ok_button)
		self.w.closeWindow_button.bind(chr(27), []) # esc
		self.w.togglePreferencesDrawer_button.bind(',', ['command', 'option'])
		self.w.scriptingWindow_button.bind('o', ['command', 'option']) # can we bind option+enter?


		self.w.getNSWindow().makeFirstResponder_(self.w.search_box.getNSTextField())

		self.w.open()


	# # # # # # # #	
	# PREFERENCES
	# # # # # # # #


	def togglePreferencesDrawer(self, sender):
		self.d.toggle()


	def readPreferences(self):
		# Read the preferences file which contains custom paths (scripts/extensions) and other preferential stuff.
		if os.path.exists(self.preferencesFile):
			config = configparser.ConfigParser()
			config.read(self.preferencesFile)

			if "scriptsDir" in config["PATHS"]:
				self.scriptsDirectory = [config["PATHS"]["scriptsDir"]][0]
				self.d.scripts_path.set(self.scriptsDirectory)
			else:
				self.d.scripts_path.set("default")
			if "extensionsDir" in config["PATHS"]:
				self.extensionsDirectory = [config["PATHS"]["extensionsDir"]][0]
				self.d.extensions_path.set(self.extensionsDirectory)
			else:
				self.d.extensions_path.set("default")

			if "rememberLast" in config["REMEMBER"]:
				self.rememberLast = int([config["REMEMBER"]["rememberLast"]][0])
			self.d.remember_count.set(self.rememberLast)

			if "value" in config["SEARCHLOCAL"]:
				self.searchLocal = int([config["SEARCHLOCAL"]["value"]][0])
			self.d.local_search_checkbox.set(self.searchLocal)

			if "searchUpDir" in config["SEARCHLOCAL"]:
				self.searchUpDir = int([config["SEARCHLOCAL"]["searchUpDir"]][0])
			self.d.local_search_count.set(self.searchUpDir)

		self.searchAll("sender")


	def preferencesChanged(self, sender):
		if sender.getTitle() == "Extensions":
			newPath = GetFolder()
			if newPath != None:
				self.extensionsDirectory = newPath
				self.d.extensions_path = newPath
				self.searchExtensionsDirectory(newPath)
		elif sender.getTitle() == "Scripts":
			newPath = GetFolder()
			if newPath != None:
				self.scriptsDirectory = newPath
				self.d.scripts_path = newPath
				self.searchScriptsDirectory(newPath)
		self.rememberLast = self.d.remember_count.get()
		self.searchLocal = self.d.local_search_checkbox.get()
		self.searchUpDir = self.d.local_search_count.get()
		self.writePreferences(sender)
		self.searchAll(sender)


	def writePreferences(self, sender):
		# Gets preferences from window and writes to file
		config = configparser.ConfigParser()
		config.read(self.preferencesFile)

		if self.d.extensions_path.get() != "default":
			config['PATHS']["extensionsDir"] = self.d.extensions_path.get()
		if self.d.scripts_path.get() != "default":
			config['PATHS']["scriptsDir"] = self.d.scripts_path.get()
		config['REMEMBER'] = {"rememberLast" : self.d.remember_count.get()}
		config['SEARCHLOCAL'] = {
			"value" : self.d.local_search_checkbox.get(),
			"searchUpDir" : self.d.local_search_count.get(),
			}

		with open(self.preferencesFile, 'w') as configfile:
			config.write(configfile)


	# LAST SCRIPT
	# Read/Write remembers the last script that was run so it can be quickly re-run

	def lastScriptCreate(self):
		if not os.path.exists(self.lastScriptFile):
			config = configparser.ConfigParser()
			config["DEFAULT"]["lastFiles"] = ""
			with open(self.lastScriptFile, 'w') as configfile:
				config.write(configfile)


	def lastScriptRead(self):
		if os.path.exists(self.lastScriptFile):
			config = configparser.ConfigParser()
			config.read(self.lastScriptFile)
			l = config["DEFAULT"]["lastFiles"]
			l = l.split(",")
			self.w.list.set(l)
			self.w.list.setSelection([0])
		else:
			self.lastScriptCreate()
		

	def lastScriptWrite(self, sender, file):
		if file != None:
			config = configparser.ConfigParser()
			config.read(self.lastScriptFile)

			l = config["DEFAULT"]["lastFiles"]
			l = l.split(",")
			if file.split("/")[-1] in l:
				l.remove(file.split("/")[-1])
			l.insert(0, file.split("/")[-1])
			l = l[:self.rememberLast]
			config["DEFAULT"]["lastFiles"] = ",".join(l)

			with open(self.lastScriptFile, 'w') as configfile:
				config.write(configfile)


	# # # # # # # #
	# FUNCTIONS
	# # # # # # # #

	def searchAll(self, sender):
		self.scripts = {"preferences" : ""}  # tabula rasa
		if self.searchLocal == True:
			self.searchNearFont(self.searchUpDir)
		self.searchExtensionsDirectory(self.extensionsDirectory)
		self.searchScriptsDirectory(self.scriptsDirectory)


	def searchNearFont(self, searchUpDirectories):
		fontDirectories = []
		if len(AllFonts()) > 0:
			for font in AllFonts():
				if font.path not in fontDirectories:
					fontDirectories.append(font.path)
		s = self.scripts
		for fontDirectory in fontDirectories:
			fontDirectoryUp = "/".join(fontDirectory.split("/")[:-(searchUpDirectories)])
			for dir, subdir, files in os.walk(fontDirectoryUp):
				for file in files:
					if ".py" in file:
						if ".pyc" not in file:
							if file not in s:
								s[file] = os.path.join(dir, file)
							else:
								if s[file] != os.path.join(dir, file):	 # avoid duplicate paths			
									# add number to scripts with idential file names
									count = 1
									fileCount = "%s (%s).py" % (file.split(".")[0], count)
									while fileCount in s:
										count += 1
										fileCount = "%s (%s).py" % (file.split(".")[0], count)
									s[fileCount] = os.path.join(dir, file)


	def searchScriptsDirectory(self, scriptsDirectory):
		if not os.path.exists(scriptsDirectory):
			print("scripts folder not found: %s" % (scriptsDirectory))
		else:
			s = self.scripts
			for dir, subdir, files in os.walk(scriptsDirectory):
				for file in files:
					if ".py" in file:
						if ".pyc" not in file:
							if file not in s:
								s[file] = os.path.join(dir, file)
							else:
								if s[file] != os.path.join(dir, file):
									# add number to scripts with idential file names
									count = 1
									fileCount = "%s (%s).py" % (file.split(".")[0], count)
									while fileCount in s:
										count += 1
										fileCount = "%s (%s).py" % (file.split(".")[0], count)
									s[fileCount] = os.path.join(dir, file)


	def searchExtensionsDirectory(self, extensionsDirectory):
		if not os.path.exists(extensionsDirectory):
			print("extensions folder not found: %s" % (extensionsDirectory))
		else:
			s = self.scripts
			for ext in os.listdir(extensionsDirectory):
				if ".roboFontExt" in ext:
					if os.path.exists(os.path.join(extensionsDirectory, ext, "info.plist")):
						with open(os.path.join(extensionsDirectory, ext, "info.plist"),'rb') as f:
							pl = plistlib.load(f)

						if pl["launchAtStartUp"] == 0: # not launched at startup
							for i in pl["addToMenu"]:
								extName = i["preferredName"]
								extPath = i["path"]
								extFullPath = os.path.join(extensionsDirectory, ext, "lib", extPath)
								if not os.path.exists(extFullPath):
									print("%s missing path: %s" % (extName, extFullPath))
								else:
									s[extName] = extFullPath


	# # # # # # # # # # # # # #
	# Searching/Finding/Running
	# # # # # # # # # # # # # #

	def previousScript(self, sender):
		if len(self.w.list) > 1:
			if self.w.list.getSelection() == []:
				self.w.list.setSelection([0])
			else:
				i = self.w.list.getSelection()[0]
				if i > 0:
					self.w.list.setSelection([i-1])
				else:
					self.w.list.setSelection([len(self.w.list.get())-1])


	def nextScript(self, sedner):
		if len(self.w.list) > 1:
			if self.w.list.getSelection() == []:
				self.w.list.setSelection([0])
			else:
				i = self.w.list.getSelection()[0]
				if i+1 < len(self.w.list.get()):
					self.w.list.setSelection([i+1])
				else:
					self.w.list.setSelection([0])


	def searchScripts(self, sender):
		i = sender.get()
		sub_list = []
		for s in self.scripts:
			if i.lower().replace(" ", "") in s.lower().replace(" ", ""):
				sub_list.append(s)
		sub_list.sort()
		self.w.list.set(sub_list)
		self.w.list.setSelection([0])


	def executeScript(self, file, sender):
		with open(file) as f:
			try:
				code = compile(f.read(), file, 'exec')
				exec(code, globals())
			except Exception as e:
				print("Error. Script will not run. %s" % (e))
		self.lastScriptWrite(sender, file)


	def runScript(self, sender):
		if self.w.list.getSelection():
			if self.w.list.get()[self.w.list.getSelection()[0]] == "preferences":
				self.togglePreferencesDrawer(sender)
			else:		
				self.closeWindow(sender)
				script_file = self.w.list.get()[self.w.list.getSelection()[0]]
				script_path = self.scripts[script_file]
				if not os.path.exists(script_path):
					print("script not found at path:", script_path)
				else:
					self.executeScript(script_path, sender)


	def openScriptInScriptingWindow(self, sender):
		if self.w.list.getSelection():
			if self.w.list.get()[self.w.list.getSelection()[0]] != "preferences":
				self.closeWindow(sender)
				script_file = self.w.list.get()[self.w.list.getSelection()[0]]
				script_path = self.scripts[script_file]
				if not os.path.exists(script_path):
					print("script not found at path:", script_path)
				else:
					OpenScriptWindow(script_path)

	
	def closeWindow(self, sender):
		self.w.close()


if __name__ == "__main__":
	scriptLauncher()
