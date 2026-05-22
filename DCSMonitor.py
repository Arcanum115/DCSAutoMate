import sys
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from DCSBIOSExportManager import DCSBIOSExportManager
from DCSAutoMateExportManager import DCSAutoMateExportManager
import pyperclip
import importlib

class DCSMonitorApp:
	CONFIG_FILE = 'DCSAutoMateConfig.json'

	# Theme definitions (same as DCSAutoMate)
	THEMES = {
		'light': {
			'bg': '#e8edf2', 'fg': '#1a1a2e', 'text_bg': '#ffffff', 'text_fg': '#1a1a2e',
			'button_bg': '#4a6fa5', 'button_fg': '#ffffff', 'button_hover': '#3a5f95',
			'button_disabled_bg': '#a0b4cc', 'button_disabled_fg': '#e0e0e0',
			'label_bg': '#e8edf2', 'label_fg': '#1a1a2e',
			'frame_bg': '#e8edf2', 'panel_bg': '#f0f3f7',
			'labelframe_bg': '#f0f3f7', 'labelframe_fg': '#4a6fa5',
			'menu_bg': '#e8edf2', 'menu_fg': '#1a1a2e',
			'entry_bg': '#ffffff', 'entry_fg': '#1a1a2e',
			'listbox_bg': '#ffffff', 'listbox_fg': '#1a1a2e',
			'select_bg': '#4a6fa5', 'select_fg': '#ffffff',
			'scrollbar_bg': '#d0d8e4',
			'output_bg': '#1a1a2e', 'output_fg': '#4ade80',
			'accent': '#4a6fa5', 'accent_fg': '#ffffff',
			'border': '#b8c5d4', 'header_bg': '#4a6fa5', 'header_fg': '#ffffff',
			'status_ok': '#22c55e', 'status_warn': '#f59e0b', 'status_error': '#ef4444',
			'separator': '#b8c5d4',
		},
		'dark': {
			'bg': '#0a0e17', 'fg': '#c8d6e5', 'text_bg': '#0d1117', 'text_fg': '#c8d6e5',
			'button_bg': '#1a3a5c', 'button_fg': '#4ade80', 'button_hover': '#1e4d7a',
			'button_disabled_bg': '#1a2332', 'button_disabled_fg': '#4a5568',
			'label_bg': '#0a0e17', 'label_fg': '#8892a0',
			'frame_bg': '#0a0e17', 'panel_bg': '#0d1321',
			'labelframe_bg': '#0d1321', 'labelframe_fg': '#4ade80',
			'menu_bg': '#0d1321', 'menu_fg': '#c8d6e5',
			'entry_bg': '#131b2e', 'entry_fg': '#e2e8f0',
			'listbox_bg': '#0d1117', 'listbox_fg': '#c8d6e5',
			'select_bg': '#1a3a5c', 'select_fg': '#4ade80',
			'scrollbar_bg': '#131b2e',
			'output_bg': '#050a12', 'output_fg': '#4ade80',
			'accent': '#4ade80', 'accent_fg': '#0a0e17',
			'border': '#1a2744', 'header_bg': '#0d1321', 'header_fg': '#4ade80',
			'status_ok': '#4ade80', 'status_warn': '#fbbf24', 'status_error': '#f87171',
			'separator': '#1a2744',
		},
	}

	def __init__(self, root):
		self.refreshRate = 1000 # milliseconds

		self.root = root
		self.root.title('DCS Monitor')
		self.root.geometry('1600x900')
		root.protocol('WM_DELETE_WINDOW', lambda: (self.dcsBiosManager.stop(), self.dcsAutoMateManager.stop(), root.destroy()))

		# Load config for dark mode setting
		self.config = self.loadConfig()

		self.jsonDirectory = os.path.join(
			os.environ['USERPROFILE'],
			'Saved Games',
			'DCS.openbeta',
			'Scripts',
			'DCS-BIOS',
			'doc',
			'json'
		)
		self.saveFile = 'DCSMonitorControls.json'

		self.dcsBiosManager = DCSBIOSExportManager({})
		self.dcsBiosManager.start()
		self.dcsAutoMateManager = DCSAutoMateExportManager({})
		self.dcsAutoMateManager.start()

		self.customControls = self.getCustomControls()
		self.modules = self.loadModules()
		self.monitoredControls = []
		self.loadMonitoredControls()
		self.createWidgets()
		self.updateControlList()

		# Add menu bar with View > Dark Mode toggle
		menuBar = tk.Menu(self.root)
		self.root.config(menu=menuBar)
		viewMenu = tk.Menu(menuBar, tearoff=0)
		menuBar.add_cascade(label='View', menu=viewMenu)
		self.darkModeVar = tk.BooleanVar(value=self.config.get('darkMode', False))
		viewMenu.add_checkbutton(label='Dark Mode', variable=self.darkModeVar, command=self.toggleDarkMode)

		# Apply theme after all widgets are created
		self.applyTheme()

		self.updateDataMonitoring()
		self.selectModule()

	def loadConfig(self):
		config = {'darkMode': False}
		try:
			if os.path.exists(self.CONFIG_FILE):
				with open(self.CONFIG_FILE, 'r') as f:
					config = json.load(f)
		except Exception:
			pass
		return config

	def getTheme(self):
		return self.THEMES['dark'] if self.config.get('darkMode', False) else self.THEMES['light']

	def toggleDarkMode(self):
		self.config['darkMode'] = self.darkModeVar.get()
		# Save back to the shared config file
		try:
			fullConfig = {}
			if os.path.exists(self.CONFIG_FILE):
				with open(self.CONFIG_FILE, 'r') as f:
					fullConfig = json.load(f)
			fullConfig['darkMode'] = self.config['darkMode']
			with open(self.CONFIG_FILE, 'w') as f:
				json.dump(fullConfig, f, indent=4)
		except Exception:
			pass
		self.applyTheme()

	def applyTheme(self):
		theme = self.getTheme()

		style = ttk.Style()
		style.theme_use('clam')
		style.configure('TCombobox',
			fieldbackground=theme['entry_bg'], background=theme['button_bg'],
			foreground=theme['entry_fg'], selectbackground=theme['select_bg'],
			selectforeground=theme['select_fg'], arrowcolor=theme['accent'],
			bordercolor=theme['border'], lightcolor=theme['entry_bg'], darkcolor=theme['entry_bg'],
		)
		style.map('TCombobox',
			fieldbackground=[('readonly', theme['entry_bg'])],
			foreground=[('readonly', theme['entry_fg'])],
			bordercolor=[('focus', theme['accent'])],
		)

		self._applyThemeToWidget(self.root, theme)
		self.root.config(bg=theme['bg'])

	def _applyThemeToWidget(self, widget, theme):
		widgetClass = widget.winfo_class()
		try:
			if widgetClass in ('Frame', 'Toplevel'):
				widget.config(bg=theme['frame_bg'])
			elif widgetClass == 'Label':
				widget.config(bg=theme['label_bg'], fg=theme['label_fg'])
			elif widgetClass == 'Button':
				widget.config(bg=theme['button_bg'], fg=theme['button_fg'],
					activebackground=theme['button_hover'], activeforeground=theme['button_fg'],
					relief='flat', borderwidth=0)
			elif widgetClass == 'Text':
				widget.config(bg=theme['output_bg'], fg=theme['output_fg'],
					insertbackground=theme['accent'], relief='flat', borderwidth=0,
					selectbackground=theme['select_bg'], selectforeground=theme['select_fg'])
			elif widgetClass == 'Listbox':
				widget.config(bg=theme['listbox_bg'], fg=theme['listbox_fg'],
					selectbackground=theme['select_bg'], selectforeground=theme['select_fg'],
					relief='flat', borderwidth=0)
			elif widgetClass == 'Entry':
				widget.config(bg=theme['entry_bg'], fg=theme['entry_fg'],
					insertbackground=theme['accent'], relief='flat', borderwidth=1,
					highlightbackground=theme['border'], highlightcolor=theme['accent'],
					highlightthickness=1)
			elif widgetClass == 'Labelframe':
				widget.config(bg=theme['panel_bg'], fg=theme['labelframe_fg'],
					relief='flat', borderwidth=1,
					highlightbackground=theme['border'], highlightcolor=theme['border'],
					highlightthickness=1)
			elif widgetClass == 'Checkbutton':
				widget.config(bg=theme['panel_bg'], fg=theme['fg'],
					activebackground=theme['panel_bg'], activeforeground=theme['fg'],
					selectcolor=theme['entry_bg'])
			elif widgetClass == 'Menu':
				widget.config(bg=theme['menu_bg'], fg=theme['menu_fg'],
					activebackground=theme['select_bg'], activeforeground=theme['select_fg'],
					borderwidth=0)
			elif widgetClass == 'Scrollbar':
				widget.config(bg=theme['scrollbar_bg'], troughcolor=theme['bg'],
					relief='flat', borderwidth=0, width=10)
			elif widgetClass == 'Tk':
				widget.config(bg=theme['bg'])
		except tk.TclError:
			pass

		for child in widget.winfo_children():
			self._applyThemeToWidget(child, theme)

	def createWidgets(self):
		controlsFrame = tk.Frame(self.root)
		controlsFrame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')

		moduleFrame = tk.Frame(controlsFrame)
		moduleFrame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
		tk.Label(moduleFrame, text='Modules:').grid(row=0, column=0, sticky='w')
		self.moduleVar = tk.StringVar()
		self.moduleDropdown = ttk.Combobox(moduleFrame, values=list(self.modules.keys()), textvariable=self.moduleVar)
		self.moduleDropdown.grid(row=0, column=1, sticky='ew')
		self.moduleDropdown.bind('<<ComboboxSelected>>', self.selectModule)

		categoryFrame = tk.Frame(controlsFrame)
		categoryFrame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
		tk.Label(categoryFrame, text='Category:').grid(row=0, column=0, sticky='w')
		self.categoryVar = tk.StringVar()
		self.categoryDropdown = ttk.Combobox(categoryFrame, textvariable=self.categoryVar)
		self.categoryDropdown.grid(row=0, column=1, sticky='ew')
		self.categoryDropdown.bind('<<ComboboxSelected>>', self.updateControlList)

		controlFrame = tk.Frame(controlsFrame)
		controlFrame.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')
		tk.Label(controlFrame, text='Controls:').grid(row=0, column=0, sticky='w')
		self.controlList = tk.Listbox(controlFrame, selectmode=tk.SINGLE)
		self.controlList.grid(row=1, column=0, sticky='nsew')
		addButton = tk.Button(controlFrame, text='Add to Monitor', command=self.addControl)
		addButton.grid(row=2, column=0, pady=5, sticky='e')

		self.refreshButton = tk.Button(controlFrame, text='Refresh Custom Controls', command=self.refreshCustomControls)
		self.refreshButton.grid(row=3, column=0, pady=5, sticky='e')
		self.refreshButton.grid_remove()  # Initially hide the button

		monitorFrame = tk.Frame(controlsFrame)
		monitorFrame.grid(row=4, column=0, padx=10, pady=5, sticky='nsew')
		tk.Label(monitorFrame, text='Monitored Controls:').grid(row=0, column=0, sticky='w')
		self.monitoredList = tk.Listbox(monitorFrame, selectmode=tk.SINGLE)
		self.monitoredList.grid(row=1, column=0, sticky='nsew')
		controlButtons = tk.Frame(monitorFrame)
		controlButtons.grid(row=2, column=0, pady=5, sticky='ew')
		topButton = tk.Button(controlButtons, text='Top', command=lambda: self.moveControlTo('top'))
		topButton.grid(row=0, column=0, padx=5)
		upButton = tk.Button(controlButtons, text='Up', command=lambda: self.moveControl(-1))
		upButton.grid(row=0, column=1, padx=5)
		downButton = tk.Button(controlButtons, text='Down', command=lambda: self.moveControl(1))
		downButton.grid(row=0, column=2, padx=5)
		bottomButton = tk.Button(controlButtons, text='Bottom', command=lambda: self.moveControlTo('bottom'))
		bottomButton.grid(row=0, column=3, padx=5)
		removeButton = tk.Button(controlButtons, text='Remove', command=self.removeControl)
		removeButton.grid(row=1, column=0, pady=5, columnspan=2)
		clearButton = tk.Button(controlButtons, text='Clear', command=self.clearControls)
		clearButton.grid(row=1, column=2, pady=5, columnspan=2)

		outputFrameBios = tk.Frame(self.root)
		outputFrameBios.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
		tk.Label(outputFrameBios, text='DCS BIOS Output:').grid(row=0, column=0, sticky='w')
		biosTextFrame = tk.Frame(outputFrameBios)
		biosTextFrame.grid(row=1, column=0, sticky='nsew')
		biosScrollY = tk.Scrollbar(biosTextFrame, orient=tk.VERTICAL)
		biosScrollX = tk.Scrollbar(biosTextFrame, orient=tk.HORIZONTAL)
		self.outputTextBios = tk.Text(biosTextFrame, state=tk.DISABLED, wrap=tk.NONE, yscrollcommand=biosScrollY.set, xscrollcommand=biosScrollX.set)
		biosScrollY.config(command=self.outputTextBios.yview)
		biosScrollX.config(command=self.outputTextBios.xview)
		biosScrollY.grid(row=0, column=1, sticky='ns')
		biosScrollX.grid(row=1, column=0, sticky='ew')
		self.outputTextBios.grid(row=0, column=0, sticky='nsew')
		copyButtonBios = tk.Button(outputFrameBios, text='Copy to Clipboard', command=self.copyToClipboardBios)
		copyButtonBios.grid(row=2, column=0, pady=5, sticky='e')

		outputFrameAutoMate = tk.Frame(self.root)
		outputFrameAutoMate.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
		tk.Label(outputFrameAutoMate, text='DCSAutoMateExport Output:').grid(row=0, column=0, sticky='w')
		autoMateTextFrame = tk.Frame(outputFrameAutoMate)
		autoMateTextFrame.grid(row=1, column=0, sticky='nsew')
		autoMateScrollY = tk.Scrollbar(autoMateTextFrame, orient=tk.VERTICAL)
		autoMateScrollX = tk.Scrollbar(autoMateTextFrame, orient=tk.HORIZONTAL)
		self.outputTextAutoMate = tk.Text(autoMateTextFrame, state=tk.DISABLED, wrap=tk.NONE, yscrollcommand=autoMateScrollY.set, xscrollcommand=autoMateScrollX.set, width=70)
		autoMateScrollY.config(command=self.outputTextAutoMate.yview)
		autoMateScrollX.config(command=self.outputTextAutoMate.xview)
		autoMateScrollY.grid(row=0, column=1, sticky='ns')
		autoMateScrollX.grid(row=1, column=0, sticky='ew')
		self.outputTextAutoMate.grid(row=0, column=0, sticky='nsew')
		copyButtonAutoMate = tk.Button(outputFrameAutoMate, text='Copy to Clipboard', command=self.copyToClipboardAutoMate)
		copyButtonAutoMate.grid(row=2, column=0, pady=5, sticky='e')

		for control in self.monitoredControls:
			self.monitoredList.insert(tk.END, control)

		self.moduleVar.set(list(self.modules.keys())[0])
		self.selectModule()

	def loadModules(self):
		modules = {}

		if os.path.exists('DCSMonitorCustomControls.py'):
			modules['CustomControls'] = {}
		for filename in os.listdir(self.jsonDirectory):
			if filename.endswith('.json') and filename != 'AircraftAliases.json':
				with open(os.path.join(self.jsonDirectory, filename), 'r') as file:
					modules[filename[:-5]] = json.load(file)

		# Sort the modules so that the special modules are at the top.
		specialModules = ['CustomControls', 'CommonData', 'MetadataStart', 'MetadataEnd']
		sortedModules = {key: modules[key] for key in specialModules if key in modules}
		sortedModules.update({k: modules[k] for k in sorted(modules.keys()) if k not in specialModules})
		return sortedModules

	def selectModule(self, *args):
		selectedModule = self.moduleVar.get()
		if selectedModule == 'CustomControls':
			self.customControls = self.getCustomControls()
			self.refreshButton.grid()  # Show the button
			self.categoryVar.set('All') # Category for custom controls is always 'All'.
			self.categoryDropdown['values'] = ['All']
			self.updateControlList()
		else:
			self.refreshButton.grid_remove()  # Hide the button
			self.categoryVar.set('All')
			moduleControls = self.modules[selectedModule]
			categories = set()
			for category in moduleControls:
				categories.add(category)
			self.categoryDropdown['values'] = ['All'] + sorted(categories)
			self.updateControlList()
			if categories:
				self.categoryVar.set('All')
				self.updateControlList()

	def getCustomControls(self):
		if os.path.exists('DCSMonitorCustomControls.py'):
			try:
				module = importlib.import_module('DCSMonitorCustomControls')
				importlib.reload(module)
				# Get the custom controls from the module.
				self.dcsMonitorCustomControls = module.DCSMonitorCustomControls()
				customControls = self.dcsMonitorCustomControls.getCustomControls() # Returns a dictionary of control names and function callbacks.
				return customControls
			except Exception as e:
				messagebox.showerror('Error', f'Error calling getCustomControls function in DCSMonitorCustomControls.py: {e}')

	def refreshCustomControls(self):
		if self.moduleVar.get() == 'CustomControls':
			self.customControls = self.getCustomControls()
			self.updateControlList()

			# If there are any controls in the monitored list that don't exist in the custom controls, remove them.
			for control in [ctrl for ctrl in self.monitoredControls if ctrl.split('/')[0] == 'CustomControls']:
				if control not in self.customControls:
					self.monitoredControls.remove(control)

	def updateControlList(self, *args):
		selectedModule = self.moduleVar.get()
		if not selectedModule:
			return

		self.controlList.delete(0, tk.END)
		if selectedModule == 'CustomControls':
			for control in sorted(self.customControls.keys()):
				self.controlList.insert(tk.END, control)
		else:
			moduleControls = self.modules[selectedModule]
			selectedCategory = self.categoryVar.get()

			controlsList = []
			for category, controls in moduleControls.items():
				for control in controls:
					if selectedCategory == 'All' or category == selectedCategory:
						controlsList.append(control)

			for control in sorted(controlsList):
				self.controlList.insert(tk.END, f'{selectedModule}/{control}')
		self.controlList.config(width=0)
		self.monitoredList.config(width=0)

	def addControl(self):
		selected = self.controlList.curselection()
		if not selected:
			return
		control = self.controlList.get(selected[0])
		if control not in self.monitoredControls:
			self.monitoredControls.append(control)
			self.monitoredList.insert(tk.END, control)
		self.monitoredList.config(width=0)
		self.saveMonitoredControls()

	def moveControl(self, direction):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		newIndex = index + direction
		if 0 <= newIndex < len(self.monitoredControls):
			self.monitoredControls[index], self.monitoredControls[newIndex] = (
				self.monitoredControls[newIndex],
				self.monitoredControls[index],
			)
			self.monitoredList.delete(0, tk.END)
			for control in self.monitoredControls:
				self.monitoredList.insert(tk.END, control)
			self.monitoredList.select_set(newIndex)
		self.saveMonitoredControls()

	def moveControlTo(self, position):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		control = self.monitoredControls.pop(index)
		if position == 'top':
			self.monitoredControls.insert(0, control)
		elif position == 'bottom':
			self.monitoredControls.append(control)
		self.monitoredList.delete(0, tk.END)
		for control in self.monitoredControls:
			self.monitoredList.insert(tk.END, control)
		self.monitoredList.select_set(0 if position == 'top' else tk.END)
		self.saveMonitoredControls()

	def removeControl(self):
		selected = self.monitoredList.curselection()
		if not selected:
			return
		index = selected[0]
		self.monitoredControls.pop(index)
		self.monitoredList.delete(index)
		self.saveMonitoredControls()

	def clearControls(self):
		self.monitoredControls.clear()
		self.monitoredList.delete(0, tk.END)
		self.saveMonitoredControls()

	def loadMonitoredControls(self):
		if os.path.exists(self.saveFile):
			with open(self.saveFile, 'r') as file:
				self.monitoredControls = json.load(file)
		# If there are any controls in the monitored list that don't exist in the custom controls, remove them.
		for control in [ctrl for ctrl in self.monitoredControls if ctrl.split('/')[0] == 'CustomControls']:
			if control not in self.customControls:
				self.monitoredControls.remove(control)

	def saveMonitoredControls(self):
		with open(self.saveFile, 'w') as file:
			json.dump(self.monitoredControls, file)

	def updateDataMonitoring(self):
		# Save the current scroll position.
		biosScrollYPos = self.outputTextBios.yview()
		biosScrollXPos = self.outputTextBios.xview()

		self.outputTextBios.config(state=tk.NORMAL)
		self.outputTextBios.delete(1.0, tk.END)

		# Get the control state data from custom controls and DCS-BIOS.
		for control in self.monitoredControls:
			if control in self.customControls:
				value = self.customControls[control](self.dcsAutoMateManager.dataStorage, dcsBiosManager=self.dcsBiosManager)
				self.outputTextBios.insert(tk.END, f'{value}\n')
			else:
				value = self.dcsBiosManager.getControlState([control])[0]
				self.outputTextBios.insert(tk.END, f'{value}\n')

		## First the custom controls.
		#for control in self.customControls:
		#	value = self.customControls[control](self.dcsAutoMateManager.dataStorage)
		#	self.outputTextBios.insert(tk.END, f'{value}\n')
		## Then the standard DCS BIOS controls.
		#biosResults = self.dcsBiosManager.getControlState(self.monitoredControls)
		#for result in biosResults:
		#	self.outputTextBios.insert(tk.END, f'{result}\n')
		self.outputTextBios.see(tk.END)
		self.outputTextBios.config(state=tk.DISABLED)
		# Restore the scroll position.
		self.outputTextBios.yview_moveto(biosScrollYPos[0])
		self.outputTextBios.xview_moveto(biosScrollXPos[0])

		# Save the current scroll position
		autoMateScrollYPos = self.outputTextAutoMate.yview()
		autoMateScrollXPos = self.outputTextAutoMate.xview()
		# Pretty-print the JSON data
		prettyPrintedData = json.dumps(self.dcsAutoMateManager.dataStorage, indent=4)
		self.outputTextAutoMate.config(state=tk.NORMAL)
		self.outputTextAutoMate.delete(1.0, tk.END)
		self.outputTextAutoMate.insert(tk.END, prettyPrintedData)
		self.outputTextAutoMate.config(state=tk.DISABLED)
		# Restore the scroll position
		self.outputTextAutoMate.yview_moveto(autoMateScrollYPos[0])
		self.outputTextAutoMate.xview_moveto(autoMateScrollXPos[0])

		self.root.after(self.refreshRate, self.updateDataMonitoring)

	def copyToClipboardAutoMate(self):
		# Get the contents of the outputTextBios text box
		outputText = self.outputTextAutoMate.get(1.0, tk.END).strip()
		# Copy the contents to the clipboard
		pyperclip.copy(outputText)
		messagebox.showinfo('Copied', 'DCSAutoMate output copied to clipboard')

	def copyToClipboardBios(self):
		# Get the contents of the outputTextBios text box
		outputText = self.outputTextBios.get(1.0, tk.END).strip()
		# Copy the contents to the clipboard
		pyperclip.copy(outputText)
		messagebox.showinfo('Copied', 'DCS BIOS output copied to clipboard')

if __name__ == '__main__':
	# When running this program as an exe, we need to have its own path appended to the sys.path in order for it to find script files in the DCSAutoMateScripts subfolder.
	applicationPath = os.path.dirname(sys.executable)
	sys.path.append(applicationPath)

	root = tk.Tk()
	app = DCSMonitorApp(root)
	root.mainloop()
