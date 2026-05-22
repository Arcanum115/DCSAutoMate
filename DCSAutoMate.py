import os
import datetime
import inspect
import argparse # Command line parameters.
import json
import math
import socket
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont, filedialog
import importlib
import os
import traceback
import win32com.client # Used for text-to-speech.
import time

# pydirectinput is used for sending keyboard commands to DCS, and pygetwindow is used to find the DCS window.
import pydirectinput
import pygetwindow as gw

# Import the classes from the new files
from DCSBIOSExportManager import DCSBIOSExportManager
from DCSAutoMateExportManager import DCSAutoMateExportManager


###############################################################################
###############################################################################
###############################################################################

class DCSAutoMateApp:
	SETTINGS_FILE = 'DCSAutoMateSettings.json'
	CONFIG_FILE = 'DCSAutoMateConfig.json'

	# Theme definitions
	THEMES = {
		'light': {
			'bg': '#e8edf2',
			'fg': '#1a1a2e',
			'text_bg': '#ffffff',
			'text_fg': '#1a1a2e',
			'button_bg': '#4a6fa5',
			'button_fg': '#ffffff',
			'button_hover': '#3a5f95',
			'button_disabled_bg': '#a0b4cc',
			'button_disabled_fg': '#e0e0e0',
			'label_bg': '#e8edf2',
			'label_fg': '#1a1a2e',
			'frame_bg': '#e8edf2',
			'panel_bg': '#f0f3f7',
			'labelframe_bg': '#f0f3f7',
			'labelframe_fg': '#4a6fa5',
			'menu_bg': '#e8edf2',
			'menu_fg': '#1a1a2e',
			'entry_bg': '#ffffff',
			'entry_fg': '#1a1a2e',
			'listbox_bg': '#ffffff',
			'listbox_fg': '#1a1a2e',
			'select_bg': '#4a6fa5',
			'select_fg': '#ffffff',
			'scrollbar_bg': '#d0d8e4',
			'output_bg': '#1a1a2e',
			'output_fg': '#4ade80',
			'accent': '#4a6fa5',
			'accent_fg': '#ffffff',
			'border': '#b8c5d4',
			'header_bg': '#4a6fa5',
			'header_fg': '#ffffff',
			'status_ok': '#22c55e',
			'status_warn': '#f59e0b',
			'status_error': '#ef4444',
			'separator': '#b8c5d4',
		},
		'dark': {
			'bg': '#0a0e17',
			'fg': '#c8d6e5',
			'text_bg': '#0d1117',
			'text_fg': '#c8d6e5',
			'button_bg': '#1a3a5c',
			'button_fg': '#4ade80',
			'button_hover': '#1e4d7a',
			'button_disabled_bg': '#1a2332',
			'button_disabled_fg': '#4a5568',
			'label_bg': '#0a0e17',
			'label_fg': '#8892a0',
			'frame_bg': '#0a0e17',
			'panel_bg': '#0d1321',
			'labelframe_bg': '#0d1321',
			'labelframe_fg': '#4ade80',
			'menu_bg': '#0d1321',
			'menu_fg': '#c8d6e5',
			'entry_bg': '#131b2e',
			'entry_fg': '#e2e8f0',
			'listbox_bg': '#0d1117',
			'listbox_fg': '#c8d6e5',
			'select_bg': '#1a3a5c',
			'select_fg': '#4ade80',
			'scrollbar_bg': '#131b2e',
			'output_bg': '#050a12',
			'output_fg': '#4ade80',
			'accent': '#4ade80',
			'accent_fg': '#0a0e17',
			'border': '#1a2744',
			'header_bg': '#0d1321',
			'header_fg': '#4ade80',
			'status_ok': '#4ade80',
			'status_warn': '#fbbf24',
			'status_error': '#f87171',
			'separator': '#1a2744',
		},
	}

	def __init__(self, root):
		log('Starting DCSAutoMate...')
		self.config = self.getConfig()

		self.root = root
		self.root.title('DCS AutoMate')
		self.root.geometry('1280x960')
		self.root.minsize(900, 600)
		self.root.protocol("WM_DELETE_WINDOW", self.onClose)

		# Create the menu bar
		menuBar = tk.Menu(self.root)
		self.root.config(menu=menuBar)
		configMenu = tk.Menu(menuBar, tearoff=0)
		menuBar.add_cascade(label='Config', menu=configMenu)
		configMenu.add_command(label='Edit Config', command=self.openConfigWindow)

		# View menu with dark mode toggle
		viewMenu = tk.Menu(menuBar, tearoff=0)
		menuBar.add_cascade(label='View', menu=viewMenu)
		self.darkModeVar = tk.BooleanVar(value=self.config.get('darkMode', False))
		viewMenu.add_checkbutton(label='Dark Mode', variable=self.darkModeVar, command=self.toggleDarkMode)

		# ── HEADER BAR ──────────────────────────────────────────
		headerFrame = tk.Frame(root, height=50)
		headerFrame.grid(row=0, column=0, columnspan=2, sticky='ew')
		headerFrame.grid_propagate(False)

		self.headerTitle = tk.Label(headerFrame, text='  DCS AUTOMATE', anchor='w',
			font=('Consolas', 16, 'bold'))
		self.headerTitle.pack(side='left', padx=15, fill='y')

		self.headerSubtitle = tk.Label(headerFrame, text='COCKPIT AUTOMATION SYSTEM',
			anchor='w', font=('Consolas', 9))
		self.headerSubtitle.pack(side='left', padx=5, fill='y')

		# Status indicator in header
		self.headerStatus = tk.Label(headerFrame, text='  READY  ',
			font=('Consolas', 9, 'bold'))
		self.headerStatus.pack(side='right', padx=15, fill='y')

		# ── SEPARATOR ───────────────────────────────────────────
		self.headerSep = tk.Frame(root, height=2)
		self.headerSep.grid(row=1, column=0, columnspan=2, sticky='ew')

		# ── MAIN CONTENT AREA ───────────────────────────────────
		contentFrame = tk.Frame(root)
		contentFrame.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)

		# ── LEFT PANEL: Controls ────────────────────────────────
		leftPanel = tk.Frame(contentFrame, width=320)
		leftPanel.pack(side='left', fill='y', padx=(0, 10))
		leftPanel.pack_propagate(False)

		# Module selection panel
		modulePanel = tk.LabelFrame(leftPanel, text=' MODULE ', font=('Consolas', 9, 'bold'),
			padx=12, pady=8)
		modulePanel.pack(fill='x', pady=(0, 8))

		tk.Label(modulePanel, text='Script File:', font=('Consolas', 9), anchor='w').pack(fill='x', pady=(2, 4))
		self.moduleDropdown = ttk.Combobox(modulePanel, state='readonly', font=('Consolas', 10))
		self.moduleDropdown.bind('<<ComboboxSelected>>', self.onModuleChange)
		self.moduleDropdown.pack(fill='x', pady=(0, 6))

		tk.Label(modulePanel, text='Script:', font=('Consolas', 9), anchor='w').pack(fill='x', pady=(2, 4))
		self.scriptDropdown = ttk.Combobox(modulePanel, state='readonly', font=('Consolas', 10))
		self.scriptDropdown.bind('<<ComboboxSelected>>', self.onScriptChange)
		self.scriptDropdown.pack(fill='x', pady=(0, 4))

		# Variables panel
		varsPanel = tk.LabelFrame(leftPanel, text=' OPTIONS ', font=('Consolas', 9, 'bold'),
			padx=12, pady=8)
		varsPanel.pack(fill='x', pady=(0, 8))

		self.varContainer = tk.Frame(varsPanel)
		self.varContainer.pack(fill='x', pady=4)
		self.varControls = {}

		# Control buttons panel
		controlPanel = tk.LabelFrame(leftPanel, text=' CONTROL ', font=('Consolas', 9, 'bold'),
			padx=12, pady=8)
		controlPanel.pack(fill='x', pady=(0, 8))

		buttonFrame = tk.Frame(controlPanel)
		buttonFrame.pack(fill='x', pady=4)

		self.startButton = tk.Button(buttonFrame, text='START', command=self.runScript,
			state='disabled', font=('Consolas', 11, 'bold'),
			relief='flat', cursor='hand2', width=10, height=1)
		self.startButton.pack(side='left', padx=(0, 8), ipady=4)

		self.stopButton = tk.Button(buttonFrame, text='STOP', command=self.stopScript,
			state='disabled', font=('Consolas', 11, 'bold'),
			relief='flat', cursor='hand2', width=10, height=1)
		self.stopButton.pack(side='left', ipady=4)

		# ── RIGHT PANEL: Status + Output ────────────────────────
		rightPanel = tk.Frame(contentFrame)
		rightPanel.pack(side='left', fill='both', expand=True)

		# Status area at top of right panel
		statusFrame = tk.Frame(rightPanel)
		statusFrame.pack(fill='x', pady=(0, 8))

		# DCS BIOS status
		biosPanel = tk.LabelFrame(statusFrame, text=' DCS-BIOS ', font=('Consolas', 9, 'bold'),
			padx=10, pady=6)
		biosPanel.pack(side='left', fill='both', expand=True, padx=(0, 5))

		self.DBEStatusLabel = tk.Label(biosPanel, text='', font=('Consolas', 9), anchor='w', justify='left')
		self.DBEStatusLabel.pack(fill='x')

		# Realtime data panel
		dataPanel = tk.LabelFrame(statusFrame, text=' REALTIME DATA ', font=('Consolas', 9, 'bold'),
			padx=10, pady=6)
		dataPanel.pack(side='left', fill='both', expand=True, padx=(5, 0))

		self.realtimeDataFrame = dataPanel  # Keep reference for theme compatibility
		self.realtimeDataLabel = tk.Label(dataPanel, text='No data to show.', font=('Consolas', 9),
			justify='left', anchor='w')
		self.realtimeDataLabel.pack(fill='x')

		# Output console
		outputPanel = tk.LabelFrame(rightPanel, text=' OUTPUT CONSOLE ', font=('Consolas', 9, 'bold'),
			padx=4, pady=4)
		outputPanel.pack(fill='both', expand=True)

		scrollbarY = tk.Scrollbar(outputPanel, orient='vertical', width=12)
		scrollbarX = tk.Scrollbar(outputPanel, orient='horizontal', width=12)
		self.outputBox = tk.Text(outputPanel, wrap='none',
			yscrollcommand=scrollbarY.set, xscrollcommand=scrollbarX.set,
			borderwidth=0, highlightthickness=0, padx=8, pady=8)
		scrollbarY.config(command=self.outputBox.yview)
		scrollbarX.config(command=self.outputBox.xview)

		scrollbarY.pack(side='right', fill='y')
		scrollbarX.pack(side='bottom', fill='x')
		self.outputBox.configure(font=('Consolas', 10), wrap='word', tabs=('1c', '6c'))
		self.outputBox.pack(fill='both', expand=True)

		# Configure grid weights
		self.root.grid_rowconfigure(2, weight=1)
		self.root.grid_columnconfigure(0, weight=1)

		self.stopFlag = threading.Event()

		self.onProgramStart()

		self.updateUIState()

		# Apply theme after all widgets are created
		self.applyTheme()

	def getTheme(self):
		return self.THEMES['dark'] if self.config.get('darkMode', False) else self.THEMES['light']

	def toggleDarkMode(self):
		self.config['darkMode'] = self.darkModeVar.get()
		# Save the config so it persists
		with open(self.CONFIG_FILE, 'w') as file:
			file.write(json.dumps(self.config, indent=4))
		self.applyTheme()

	def applyTheme(self):
		theme = self.getTheme()

		# Style the ttk widgets first
		style = ttk.Style()
		style.theme_use('clam')

		style.configure('TCombobox',
			fieldbackground=theme['entry_bg'],
			background=theme['button_bg'],
			foreground=theme['entry_fg'],
			selectbackground=theme['select_bg'],
			selectforeground=theme['select_fg'],
			arrowcolor=theme['accent'],
			bordercolor=theme['border'],
			lightcolor=theme['entry_bg'],
			darkcolor=theme['entry_bg'],
		)
		style.configure('TRadiobutton',
			background=theme['panel_bg'],
			foreground=theme['fg'],
			focuscolor=theme['panel_bg'],
			indicatorcolor=theme['entry_bg'],
		)
		style.map('TCombobox',
			fieldbackground=[('readonly', theme['entry_bg'])],
			foreground=[('readonly', theme['entry_fg'])],
			bordercolor=[('focus', theme['accent'])],
		)
		style.map('TRadiobutton',
			background=[('active', theme['panel_bg'])],
			indicatorcolor=[('selected', theme['accent'])],
		)

		# Apply to all widgets recursively
		self._applyThemeToWidget(self.root, theme)

		# Apply special header styling
		self.headerTitle.config(bg=theme['header_bg'], fg=theme['header_fg'])
		self.headerSubtitle.config(bg=theme['header_bg'], fg=theme['header_fg'])
		self.headerStatus.config(bg=theme['header_bg'], fg=theme['status_ok'])
		self.headerTitle.master.config(bg=theme['header_bg'])
		self.headerSep.config(bg=theme['accent'])

		# Style the buttons specially
		self.startButton.config(bg=theme['accent'], fg=theme['accent_fg'],
			activebackground=theme['button_hover'], activeforeground=theme['accent_fg'],
			disabledforeground=theme['button_disabled_fg'])
		self.stopButton.config(bg=theme.get('status_error', '#ef4444'), fg='#ffffff',
			activebackground='#dc2626', activeforeground='#ffffff',
			disabledforeground=theme['button_disabled_fg'])

		# Style output box
		self.outputBox.config(bg=theme['output_bg'], fg=theme['output_fg'],
			insertbackground=theme['accent'])

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
					selectcolor=theme['entry_bg'], font=('Consolas', 9))
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
			pass  # Some widgets may not support all config options

		# Recursively apply to children
		for child in widget.winfo_children():
			self._applyThemeToWidget(child, theme)

	def onProgramStart(self):
		# Start the DCS BIOS Export Manager, which begins a thread to monitor the DCS BIOS output data.
		self.dbe = DCSBIOSExportManager(self.config)
		self.dbe.start()

		# Start the DCSAutoMateExport manager, which begins a thread to receive data from the DCSAutoMateExport.lua script.
		self.DAMExport = DCSAutoMateExportManager(self.config)
		self.DAMExport.start()

		# Get the current settings from the file.
		self.settings = self.getSettings()
		#print(self.settings)

		# Get the list of modules (file names) from the script *.py files.
		self.modules = self.getModules()
		self.updateModulesDropdown(self.modules)

		lastUsedModule = self.getLastUsedModule()

		# Set the last used module, if any.
		if lastUsedModule and lastUsedModule in self.modules:
			self.moduleDropdown.set(lastUsedModule)
		else:
			self.moduleDropdown.current(0)
		self.moduleName = self.moduleDropdown.get()

		self.onModuleChange(None)

		self.updateDataMonitoring()

	# Called when the program is closed.  Stops the cockpit state manager and closes the program.
	def onClose(self):
		#print("Stopping DBE...")
		self.dbe.stop()  # Stop the DCSBIOSExportManager
		self.DAMExport.stop()  # Stop the DCSAutoMateExportManager
		#print("Destroying main window...")
		self.root.destroy()  # Destroy the main window
		#print("Main window destroyed.")

	def updateDataMonitoring(self):
		self.DBEStatusLabel.config(text=self.dbe.outputString)
		self.realtimeDataLabel.config(text=self.DAMExport.outputString)

		self.root.update_idletasks()

		# Schedule next UI update
		self.root.after(100, self.updateDataMonitoring)

	# Called when the module dropdown is changed.  Updates the script dropdown with the scripts from the selected module.
	def onModuleChange(self, event):
		# Get the new moduleName from the dropdown and set it in self.
		self.moduleName = self.moduleDropdown.get()
		# Load the script metadata for this module from the script file.
		self.scriptData = self.getScriptData(self.moduleName)

		# Update the script dropdown with the data.
		self.updateScriptDropdown(self.scriptData)

		# Set the last used script, if any.
		lastUsedScriptName = self.getLastUsedScriptName(self.moduleName)
		if lastUsedScriptName:
			self.scriptDropdown.set(lastUsedScriptName)
		else:
			self.scriptDropdown.current(0)

		self.onScriptChange(None)

	def onScriptChange(self, event):
		# Get the new scriptName from the dropdown and set it in self.
		self.scriptName = self.scriptDropdown.get()

		# Create the radio buttons and set them to some values based on the last used settings.
		self.scriptVars = self.getScriptVars(self.scriptData, self.scriptName)
		lastUsedVars = self.getLastUsedVars(self.moduleName, self.scriptName)
		if lastUsedVars:
			setScriptVars = lastUsedVars
		else:
			setScriptVars = {}
		self.updateScriptVarsRadioButtons(self.scriptVars, setScriptVars)

		self.onVarsRadioButtonChange(None)

	def updateScriptVarsRadioButtons(self, scriptVars, setScriptVars):
		for widget in self.varContainer.winfo_children():
			widget.destroy()
		theme = self.getTheme()
		for varName, options in scriptVars.items():
			frame = tk.Frame(self.varContainer, bg=theme['panel_bg'])
			frame.pack(fill='x', pady=3)
			tk.Label(frame, text=f'{varName}:', font=('Consolas', 9, 'bold'),
				bg=theme['panel_bg'], fg=theme['labelframe_fg']).pack(side='left', padx=(0, 8))
			var = tk.StringVar(value=setScriptVars.get(varName, options[0]))
			for option in options:
				rb = ttk.Radiobutton(frame, text=option, variable=var, value=option)
				rb.pack(side='left', padx=4)
			self.varControls[varName] = var
			# Add a trace to save settings when an option changes
			var.trace_add("write", lambda *args: self.onVarsRadioButtonChange(None))
		self.updateUIState()

	def onVarsRadioButtonChange(self, event):
		# Save the current settings.
		self.saveSettings()

	def getAircraftName(self):
		control = 'MetadataStart/_ACFT_NAME'
		aircraftName = self.dbe.getControlState(control)
		if aircraftName:
			return aircraftName[0][2].strip()
		else:
			return 'N/A'

	def getMissionTime(self):
		return self.dbe.detectTimeOfDay()

	def saveSettings(self):
		try:
			self.settings['lastUsedModule'] = self.moduleName
			self.settings['lastUsedScripts'][self.moduleName] = self.scriptName
			vars = self.getSelectedVars()

			foundItem = False
			for item in self.settings['lastUsedVars']:
				if item['module'] == self.moduleName and item['script'] == self.scriptName:
					item['vars'] = vars
					foundItem = True
					break
			if not foundItem:
				self.settings['lastUsedVars'].append(
					{
						'module': self.moduleName,
						'script': self.scriptName,
						'vars': vars,
					}
				)

			# If there was an error reading the settings file last time we tried to, don't try to save settings.
			if not self.settingsError:
				with open(self.SETTINGS_FILE, 'w') as file:
					json.dump(self.settings, file, indent=4)
		except Exception as e:
			messagebox.showerror("Error", f"Error saving settings: {e}")

	def getSettings(self):
		self.settingsError = False
		settings = {
			'lastUsedModule': '',
			'lastUsedScripts': {},
			'lastUsedVars': []
		}
		try:
			if os.path.exists(self.SETTINGS_FILE):
				with open(self.SETTINGS_FILE, 'r') as f:
					settings = json.load(f)
		except Exception as e:
			# Set a flag to indicate that there was an error loading the settings file.
			self.settingsError = True
			# Show an error message in a popup window
			messagebox.showerror("Error", f"Error loading settings from {self.SETTINGS_FILE}: {e}.\nPlease check the file for syntax errors, or delete it to create a new one.")

		return settings

	def updateSettings(self, moduleName, scriptName, vars, setLastUsed=False):
		for item in self.settings['lastUsedVars']:
			if item.get('module') == moduleName and item.get('script') == scriptName:
				#item.set(vars)
				pass
		if setLastUsed:
			if self.settings['lastUsed'].get(moduleName):
				self.settings['lastUsed'][moduleName] = scriptName
			else:
				self.settings['lastUsed'].append({moduleName: scriptName})

		self.saveSettings()

	# Returns the last used module data from the settings file, or an empty string if not found.
	def getLastUsedModule(self):
		if self.settings['lastUsedModule']:
			return self.settings['lastUsedModule']
		else:
			return ''

	# Returns the name of the last used script, or empty string if not found.
	def getLastUsedScriptName(self, moduleName):
		for key in self.settings['lastUsedScripts']:
			if key == moduleName:
				return self.settings['lastUsedScripts'][key]
		return ''

	# Returns the dict of the selected vars {varName: varValue} for the last used script, or an empty dict if not found.
	def getLastUsedVars(self, moduleName, scriptName):
		for item in self.settings['lastUsedVars']:
			if item.get('module') == moduleName and item.get('script') == scriptName:
				return item['vars']
		return {}

	def openConfigWindow(self):
		theme = self.getTheme()
		configWindow = tk.Toplevel(self.root)
		configWindow.title('Edit Config')
		configWindow.sizeX = 700
		configWindow.sizeY = 600
		configWindow.geometry(f'{configWindow.sizeX}x{configWindow.sizeY}')

		# Make the config window a child of the main window
		configWindow.transient(self.root)

		# Center the config window on the main window
		self.root.update_idletasks()
		x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (configWindow.sizeX // 2)
		y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (configWindow.sizeY // 2)
		configWindow.geometry(f"+{x}+{y}")

		debugVar = tk.BooleanVar(value=self.config.get('debug', False))
		disableSpeechVar = tk.BooleanVar(value=self.config.get('disableSpeech', False))
		dcsWindowUseTitleVar = tk.BooleanVar(value=self.config.get('dcsWindowUseTitle', False))
		dcsWindowTitleOverrideVar = tk.StringVar(value=self.config.get('dcsWindowTitleOverride', ''))
		dcsSavedGamesOverrideVar = tk.StringVar(value=self.config.get('dcsSavedGamesOverride', ''))
		dcsExePathOverrideVar = tk.StringVar(value=self.config.get('dcsExePathOverride', ''))
		darkModeVar = tk.BooleanVar(value=self.config.get('darkMode', False))

		# Config header
		cfgHeader = tk.Frame(configWindow, height=40)
		cfgHeader.pack(fill='x')
		cfgHeader.pack_propagate(False)
		tk.Label(cfgHeader, text='  CONFIGURATION', font=('Consolas', 12, 'bold'),
			bg=theme['header_bg'], fg=theme['header_fg']).pack(fill='both', expand=True, anchor='w')
		tk.Frame(configWindow, height=2, bg=theme['accent']).pack(fill='x')

		# Content area
		contentArea = tk.Frame(configWindow)
		contentArea.pack(fill='both', expand=True, padx=15, pady=10)

		padding = {'padx': 5, 'pady': 4}
		labelFont = ('Consolas', 9)

		# General section
		genPanel = tk.LabelFrame(contentArea, text=' GENERAL ', font=('Consolas', 9, 'bold'), padx=10, pady=6)
		genPanel.pack(fill='x', pady=(0, 8))

		tk.Checkbutton(genPanel, text='Debug - Disables sending data to DCS', variable=debugVar, font=labelFont).pack(anchor='w', **padding)
		tk.Checkbutton(genPanel, text='Disable Text-to-Speech output', variable=disableSpeechVar, font=labelFont).pack(anchor='w', **padding)
		tk.Checkbutton(genPanel, text='Dark Mode', variable=darkModeVar, font=labelFont).pack(anchor='w', **padding)

		# DCS Window section
		dcsPanel = tk.LabelFrame(contentArea, text=' DCS WINDOW ', font=('Consolas', 9, 'bold'), padx=10, pady=6)
		dcsPanel.pack(fill='x', pady=(0, 8))

		tk.Checkbutton(dcsPanel, text='Find DCS window by window title (otherwise use exe path)', variable=dcsWindowUseTitleVar, font=labelFont).pack(anchor='w', **padding)

		tk.Label(dcsPanel, text='DCS executable path (blank = auto-detect from registry):', font=labelFont, anchor='w').pack(fill='x', **padding)
		exeFrame = tk.Frame(dcsPanel)
		exeFrame.pack(fill='x', **padding)
		tk.Entry(exeFrame, textvariable=dcsExePathOverrideVar, font=labelFont).pack(side='left', fill='x', expand=True, padx=(0, 5))
		tk.Button(exeFrame, text='Browse', font=labelFont, command=lambda: dcsExePathOverrideVar.set(filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")]))).pack(side='right')

		tk.Label(dcsPanel, text='DCS window title (blank = "Digital Combat Simulator"):', font=labelFont, anchor='w').pack(fill='x', **padding)
		tk.Entry(dcsPanel, textvariable=dcsWindowTitleOverrideVar, font=labelFont).pack(fill='x', **padding)

		# Paths section
		pathPanel = tk.LabelFrame(contentArea, text=' PATHS ', font=('Consolas', 9, 'bold'), padx=10, pady=6)
		pathPanel.pack(fill='x', pady=(0, 8))

		tk.Label(pathPanel, text='DCS Saved Games folder (blank = auto-detect):', font=labelFont, anchor='w').pack(fill='x', **padding)
		sgFrame = tk.Frame(pathPanel)
		sgFrame.pack(fill='x', **padding)
		tk.Entry(sgFrame, textvariable=dcsSavedGamesOverrideVar, font=labelFont).pack(side='left', fill='x', expand=True, padx=(0, 5))
		tk.Button(sgFrame, text='Browse', font=labelFont, command=lambda: dcsSavedGamesOverrideVar.set(filedialog.askdirectory())).pack(side='right')

		# Action buttons
		buttonFrame = tk.Frame(configWindow)
		buttonFrame.pack(pady=10)
		saveBtn = tk.Button(buttonFrame, text='SAVE', command=lambda: self.saveConfig(
			debugVar, disableSpeechVar, dcsWindowUseTitleVar, dcsExePathOverrideVar,
			dcsWindowTitleOverrideVar, dcsSavedGamesOverrideVar, darkModeVar, configWindow),
			font=('Consolas', 10, 'bold'), relief='flat', width=12)
		saveBtn.pack(side='left', padx=5, ipady=4)
		cancelBtn = tk.Button(buttonFrame, text='CANCEL', command=configWindow.destroy,
			font=('Consolas', 10, 'bold'), relief='flat', width=12)
		cancelBtn.pack(side='left', padx=5, ipady=4)

		# Apply theme to the config window
		self._applyThemeToWidget(configWindow, theme)
		# Special button styling
		saveBtn.config(bg=theme['accent'], fg=theme['accent_fg'],
			activebackground=theme['button_hover'], activeforeground=theme['accent_fg'])
		cancelBtn.config(bg=theme['button_bg'], fg=theme['button_fg'],
			activebackground=theme['button_hover'], activeforeground=theme['button_fg'])

		# Make the window modal
		configWindow.grab_set()
		self.root.wait_window(configWindow)

	def saveConfig(self, debugVar, disableSpeechVar, dcsWindowUseTitleVar, dcsExePathOverrideVar, dcsWindowTitleOverrideVar, dcsSavedGamesOverrideVar, darkModeVar, configWindow):
		self.config['debug'] = debugVar.get()
		self.config['disableSpeech'] = disableSpeechVar.get()
		self.config['dcsWindowUseTitle'] = dcsWindowUseTitleVar.get()
		self.config['dcsExePathOverride'] = dcsExePathOverrideVar.get()
		self.config['dcsWindowTitleOverride'] = dcsWindowTitleOverrideVar.get()
		self.config['dcsSavedGamesOverride'] = dcsSavedGamesOverrideVar.get()
		self.config['darkMode'] = darkModeVar.get()

		with open('DCSAutoMateConfig.json', 'w') as file:
			file.write(json.dumps(self.config, indent=4))

		# Update the dark mode toggle and apply theme
		self.darkModeVar.set(darkModeVar.get())
		self.applyTheme()

		configWindow.destroy()

	def updateUIState(self):
		theme = self.getTheme()
		moduleSelected = bool(self.moduleDropdown.get())
		scriptSelected = bool(self.scriptDropdown.get())
		canStart = moduleSelected and scriptSelected
		self.startButton.config(state='normal' if canStart else 'disabled')
		self.stopButton.config(state='disabled')
		# Update button colors based on state
		if canStart:
			self.startButton.config(bg=theme['accent'], fg=theme['accent_fg'])
		else:
			self.startButton.config(bg=theme['button_disabled_bg'], fg=theme['button_disabled_fg'])

	def getDefaultConfig(self):
		return {
			'debug': False,
			'disableSpeech': False,
			'dcsWindowUseTitle': False,
			'dcsExePathOverride': '',
			'dcsWindowTitleOverride': '',
			'dcsSavedGamesOverride': '',
			'darkMode': False,
		}

	def loadConfigFile(self):
		config = self.getDefaultConfig()
		try:
			# If the config file doesn't exist, create it with the default config.
			if not os.path.isfile(self.CONFIG_FILE):
				with open('DCSAutoMateConfig.json', 'w') as file:
					file.write(json.dumps(config, indent=4))
		except Exception as e:
				messagebox.showerror("Error", f"Error writing default config to {self.CONFIG_FILE}: {e}.")

		try:
			with open(self.CONFIG_FILE) as file:
				config = json.load(file)
		except:
			messagebox.showerror("Error", f"Error loading config from {self.CONFIG_FILE}: {e}.\nPlease check the file for syntax errors, or delete it to create a new one.")

		return config

	def getConfig(self):
		# First, get the config from the .json file.  If the file doesn't exist, this will create it with the defaults.  Anything set up here may be overridden later by command-line parameters.
		config = self.loadConfigFile()

		# Initialize parser for command line arguments.
		parser = argparse.ArgumentParser(
			prog = 'DCSAutoMate',
			description = 'Sends scripted commands to DCS, allowing complete cockpit scripting and automation.',
		)
		parser.add_argument(
			'--debug',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, script will be run normally, but without actually sending any commands to DCS."
		)
		parser.add_argument(
			'--disableSpeech',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, text-to-speech commands in the script will not be executed."
		)
		parser.add_argument(
			'--dcsWindowUseTitle',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, will make DCSAutoMate look for the DCS window by title, instead of by exe path."
		)
		parser.add_argument(
			'--dcsWindowTitleOverride',
			action = 'store',
			help = "If passed, specifies the title of the DCS window to send commands to (default is \"Digital Combat Simulator\").  This title is case-insensitive and can appear anywhere in the full window title string."
		)
		parser.add_argument(
			'--dcsSavedGamesOverride',
			action = 'store',
			help = "If passed, specifies the full path to the DCS Saved Games folder.  Defaults to trying first %%USERPROFILE%%\\Saved Games\\DCS and then %%USERPROFILE%%\\Saved Games\\DCS.openbeta."
		)

		args = parser.parse_args()
		#print(args.debug)
		if args.debug:
			config['debug'] = args.debug
		if args.disableSpeech:
			config['disableSpeech'] = args.disableSpeech
		if args.dcsWindowUseTitle:
			config['dcsWindowUseTitle'] = args.dcsWindowUseTitle
		if args.dcsWindowTitleOverride:
			config['dcsWindowTitleOverride'] = args.dcsWindowTitleOverride
		if args.dcsSavedGamesOverride:
			config['dcsSavedGamesOverride'] = args.dcsSavedGamesOverride

		return config

	def getModules(self):
		scriptPath = './DCSAutoMateScripts'
		modules = [f[:-3] for f in os.listdir(scriptPath) if f.endswith('.py')]
		return modules

	def updateModulesDropdown(self, modules):
		self.moduleDropdown['values'] = modules
		if modules:
			self.moduleDropdown.current(0)
		self.updateUIState()

	# Loads the script metadata array from the script file by calling the getScriptData() function in the file.
	# Complete script metadata array is stored in self.scriptData.
	def getScriptData(self, moduleName):
		try:
			module = [importlib.import_module(f'DCSAutoMateScripts.{moduleName}')]
			importlib.reload(module[0])
			scriptData = module[0].getScriptData()

		except Exception as e:
			messagebox.showerror('Error', f'Error loading module: {e}')
		return scriptData

	def updateScriptDropdown(self, scriptData):
		self.scriptDropdown['values'] = [s['name'] for s in scriptData['scripts']]
		if scriptData['scripts']:
			self.scriptDropdown.current(0)
		self.updateUIState()

	# Loads the vars dict for this script from the script metadata array.
	def getScriptVars(self, scriptData, scriptName):
		for script in scriptData['scripts']:
			if script['name'] == scriptName:
				return script['vars']
		return {}

	def getSelectedVars(self):
		if self.varControls:
			return {var: varControl.get() for var, varControl in self.varControls.items()}
		else:
			return {}

	def updateOutput(self, text, flush=False):
		if text != '':
			self.outputBox.insert(tk.END, text.encode('utf-8'))
			self.outputBox.see(tk.END)  # Automatically scroll to the bottom

		if flush:
			self.outputBox.see(tk.END)  # Automatically scroll to the bottom
			self.root.update_idletasks() # Forces the output textbox to update.

	def runScript(self):
		self.saveSettings()
		moduleName = self.moduleDropdown.get()
		scriptName = self.scriptDropdown.get()
		vars = {var: varControl.get() for var, varControl in self.varControls.items()}
		try:
			module = [importlib.import_module(f'DCSAutoMateScripts.{moduleName}')]
			importlib.reload(module[0])
			scriptData = module[0].getScriptData()

			# Find the selected script and its corresponding function
			selectedScript = next(script for script in scriptData['scripts'] if script['name'] == scriptName)
			functionName = selectedScript['function']
			scriptFunction = getattr(module[0], functionName) # This is the function in the script file that will be called to generate the sequence.  e.g. ColdStart(), HotStart(), Test(), etc.

			seq = scriptFunction(self.config, vars)
			self.outputBox.delete(1.0, tk.END)
			self.stopFlag.clear()
			self.startButton.config(state='disabled')
			self.stopButton.config(state='normal')

			try:
				scriptInfo = module[0].getInfo()
				if scriptInfo:
					self.updateOutput(f'Script info: {scriptInfo}\n\n')
			except:
				pass

			seqExe = seqExecute(self.root, self.config, self.dbe, self.updateOutput, self.stopFlag)
			seqExe.execute(seq)
			self.updateUIState()
		except Exception as e:
			self.outputBox.insert(tk.END, 'Error occurred:\n')
			self.outputBox.insert(tk.END, traceback.format_exc())
			self.updateUIState()

	def stopScript(self):
		self.stopFlag.set()
		self.updateOutput('\n--- Script execution stopped by user. ---\n', flush=True)
		self.updateUIState()


###############################################################################
###############################################################################
###############################################################################

######
# Seq must be a List of Dictionaries.  Each Dictionary must have {time, cmd, ...}, other keys are needed based on the command, see code.
######
class seqExecute:
	def __init__(self, root, config, dbe, updateOutput, stopFlag):
		self.root = root # The UI root object.  Needed to force updates during long loops to prevent Windows from thinking the app is frozen.
		self.config = config
		self.dbe = dbe
		self.updateOutput = updateOutput # Callback function to send output to.
		self.stopFlag = stopFlag

		self.inputSocket = self.getDcsInputSocket()

	def getDcsInputSocket(self):
		# Create UDP socket to send DCS BIOS commands.
		inputSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		return inputSocket

	def getDcsWindow(self):
		dcsWindow = None
		# If we're in debug mode, just return None since we won't be sending any commands to DCS.
		if self.config['debug']:
			return dcsWindow

		# If the selected method to find the DCS window is by title, try to find it.
		if self.config['dcsWindowUseTitle']:
			if self.config['dcsWindowTitleOverride']:
				dcsWindowTitle = self.config['dcsWindowTitleOverride']
			else:
				dcsWindowTitle = 'Digital Combat Simulator'
			self.updateOutput(f'Trying to find DCS window by title: "{dcsWindowTitle}"...\n', flush=True)
			matches = gw.getWindowsWithTitle(dcsWindowTitle)
			log(f'Found {len(matches)} windows with title "{dcsWindowTitle}"')
			if matches:
				dcsWindow = matches[0]
				self.updateOutput('Found DCS window by title\n', flush=True)

			if not dcsWindow:
				self.updateOutput('Could not find DCS window.  Please ensure DCS is running, and/or set correct title in config window.\n', flush=True)

			return dcsWindow

		# Else try to find the DCS window by exe path.
		else:
			dcsExePath = None
			if self.config['dcsExePathOverride']:
				log(f'Using DCS exe path override: {self.config["dcsExePathOverride"]}')
				dcsExePath = self.config['dcsExePathOverride']
				self.updateOutput(f'Trying to find DCS window by exe path: {dcsExePath}...\n', flush=True)
			else:
				log('Using default DCS exe path')
				self.updateOutput(f'Trying to find DCS window by exe path: *\\bin\\DCS.exe or *\\bin-mt\\DCS.exe...\n', flush=True)

			try:
				import ctypes
				from ctypes import wintypes

				import psutil
				import win32api
				import win32con
				import win32security

				def isProcessAdmin(processId):
					try:
						hProcess = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, processId)
						hToken = win32security.OpenProcessToken(hProcess, win32con.TOKEN_QUERY)
						elevation = win32security.GetTokenInformation(hToken, win32security.TokenElevation)
						# elevation is an int; 1 means elevated, 0 means not elevated
						if elevation == 1:
							return 'elevated'
						else:
							return 'nonelevated'
					except Exception as e:
						log('Error checking token elevation:', e)
						return 'unknown' # If we can't determine the elevation, return unknown.  We'll assume it's elevated though.

				def getProcessIdFromHwnd(hWnd):
					processID = wintypes.DWORD()
					ctypes.windll.user32.GetWindowThreadProcessId(hWnd, ctypes.byref(processID))
					return processID.value

				def getProcessPath(processId):
					hProcess = ctypes.windll.kernel32.OpenProcess(0x1000, False, processId)
					if hProcess:
						try:
							buf = ctypes.create_unicode_buffer(512)
							size = wintypes.DWORD(512)
							if ctypes.windll.psapi.GetModuleFileNameExW(hProcess, None, buf, size):
								return buf.value
						finally:
							ctypes.windll.kernel32.CloseHandle(hProcess)
					return None

				# Check each window's process path to see if it matches the DCS exe path.
				windows = gw.getAllWindows()
				for window in windows:
					if window._hWnd:
						pid = getProcessIdFromHwnd(window._hWnd)
						procPath = getProcessPath(pid)
						#log(f'Window: {window.title}, PID: {pid}, Path: {procPath}')
						if dcsExePath and procPath and procPath.lower() == dcsExePath.lower():
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: {dcsExePath}\n', flush=True)
							break
						elif procPath and procPath.lower().endswith(r'\bin\dcs.exe'):
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: *\\bin\\DCS.exe\n', flush=True)
							break
						elif procPath and procPath.lower().endswith(r'\bin-mt\dcs.exe'):
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: *\\bin-mt\\DCS.exe\n', flush=True)
							break

				# If we found the window, check to see if DCS is running as admin, and if DCSAutoMate is not, show a warning.
				if dcsWindow:
					log(f'Found DCS window with Process Path: {procPath}')
					dcsIsAdmin = isProcessAdmin(pid)
					log(f'DCS UAC elevation: {dcsIsAdmin}')
					dcsAutoMateIsAdmin = 'elevated' if ctypes.windll.shell32.IsUserAnAdmin() else 'nonelevated'
					log(f'DCSAutoMate UAC elevation: {dcsAutoMateIsAdmin}')
					# If DCS is running as admin (or unknown) and DCSAutoMate is not, show a warning.  If DCS is admin but DCSAutoMate is not, DCSAutoMate may not be able to send keystrokes to the DCS window with DirectInput.
					if dcsAutoMateIsAdmin == 'nonelevated' and dcsIsAdmin in ['elevated', 'unknown']:
						self.updateOutput('Warning: DCSAutoMate is not running as Administrator, but DCS is (or can\'t detect).  If keyboard input is not sent to DCS, try running DCSAutoMate as Administrator.', flush=True)

				# If we didn't find the window, show an error.
				else:
					self.updateOutput('Could not find DCS window. Please ensure DCS is running.\n', flush=True)
					return dcsWindow

			except Exception as e:
				self.updateOutput(f'Error finding DCS window: {e}\n', flush=True)

			return dcsWindow

	def getSecToMin(self, numSeconds):
		mins = int(math.floor(numSeconds / 60))
		secs = int(numSeconds - (mins * 60))
		return f'{mins}m{secs:02}s'

	# speakerId: 0 = MS David, 1 = MS Hazel, 2 = MS Zira
	# This code adapted from: https://stackoverflow.com/questions/31167967/python-3-4-text-to-speech-with-sapi
	# For more docs, see: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723609(v=vs.85)
	def getTtsSpeaker(self, speakerId = 1):
		speaker = win32com.client.Dispatch("SAPI.SpVoice")
		voices = speaker.GetVoices()
		#for voice in voices:
			#self.updateOutput(voice.GetAttribute("Name"))
		#self.updateOutput(voices.Item(speakerId).GetAttribute("Name")) # speaker name
		speaker.Voice
		speaker.SetVoice(voices.Item(speakerId)) # set voice (see Windows Text-to-Speech settings)
		speaker.Rate
		speaker.SetRate(3) # -10 is slowest, 10 is fastest, 0 is default.
		speaker.Volume
		speaker.SetVolume(75) # 0-100, 0 is quietest, 100 is default.
		return speaker

	# If asyncFlag is false, program execution will stop while speaking.
	def speak(self, speaker, string, asyncFlag = True):
		if not self.config['disableSpeech']:
			SVSFlag = 1 if asyncFlag is True else 0 # Makes the speaking asyncronous so it doesn't hold up the script.  See https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)
			speaker.speak(string, SVSFlag)

	def execute(self, seq):
		if self.config['debug']:
			self.updateOutput('RUNNING IN DEBUG MODE, nothing will be sent to the game\n', flush=True)

		self.dcsWindow = self.getDcsWindow()
		if not self.config['debug'] and not self.dcsWindow:
			return

		self.updateOutput(f"Beginning script execution.\n", flush=True)

		speaker = self.getTtsSpeaker()

		# Look through the script to find how many keyboard commands will be executed.
		numScriptKeyboardCommands = sum(1 for row in seq if row['cmd'] == 'scriptKeyboard') # https://stackoverflow.com/a/16455812
		if numScriptKeyboardCommands:
			self.updateOutput(f'Found {numScriptKeyboardCommands} keyboard commands in script.  Stay in cockpit until last keyboard command is executed.\n', flush=True)
			self.speak(speaker, 'Stay in cockpit until last keyboard command is executed.', asyncFlag=False) # We want to make sure this message is read before any other speech in the script gets played.

		rowNum = 0
		self.executedScriptKeyboardCommands = 0
		startTime = time.time() # Start the timer immediately before starting the execution loop.
		cmdStartTime = time.time() # Start the timer for this command.
		timers = {} # A dictionary to track the currently running timers.
		while not self.stopFlag.is_set():
			# When our counter gets past the last row, break out of the loop.
			if rowNum >= len(seq):
				break

			currentTime = time.time()
			elapsedTime = currentTime - startTime
			cmdElapsedTime = currentTime - cmdStartTime

			# Get the current command.
			command = seq[rowNum]
			# If the time since we started is greater than the command we're executing, run that command and go on to the next one.
			if cmdElapsedTime > command['time']:
				cmd = command['cmd']
				msg = command.get('msg', '')
				displayTime = round(elapsedTime, 1)
				displayCmdTime = round(command['time'], 1)
				self.updateOutput(f'Time: {displayTime}, Cmd: {displayCmdTime}\t\t', flush=True)

				if cmd == 'scriptKeyboard':
					self.handleScriptKeyboard(command)
				elif cmd == 'scriptSpeech':
					arg = command['arg']
					msg = command['msg']
					self.updateOutput(f'Speaking:\t"{arg}"', flush=True)
					self.speak(speaker, arg)
				elif cmd == 'scriptCockpitState':
					self.handleScriptCockpitState(command)
				elif cmd == 'scriptTimerStart' or cmd == 'scriptTimerEnd':
					self.handleScriptTimer(command, timers)
				elif cmd != '':
					arg = command['arg']
					msg = command['msg']
					self.updateOutput(f'DCS-BIOS command:\t{cmd} {arg}', flush=True)
					if not self.config['debug']:
						self.inputSocket.sendto(bytes(str(cmd) + ' ' + str(arg) + '\n', "utf-8"), ('127.0.0.1', 7778))

				if msg != '':
					if cmd:
						self.updateOutput(f' - {msg}', flush=True)
					else:
						self.updateOutput(f'Message:\t{msg}', flush=True)

				# After all the command-related text is printed, if we've executed the last keyboard command, print and say that.
				if numScriptKeyboardCommands and self.executedScriptKeyboardCommands == numScriptKeyboardCommands:
					self.updateOutput('\nLast keyboard command executed, you may safely leave the cockpit.', flush=True)
					self.speak(speaker, 'Last keyboard command executed, you may safely leave the cockpit.')
					self.executedScriptKeyboardCommands = -1 # Set this to -1 to prevent this conditional from firing again.

				self.updateOutput('\n', flush=True)

				# Go on to the next command.
				rowNum += 1
				cmdStartTime = time.time() # Reset the timer for the next command.

			self.root.update()
			#time.sleep(0.01) # Sleep for a short time to save CPU cycles, there's no need to run this loop continuously as fast as possible.

		self.updateOutput('Script complete\n', flush=True)
		self.speak(speaker, 'Script complete', asyncFlag=False)

	def handleScriptKeyboard(self, command):
		#print('in handleScriptKeyboard', command)
		keyString = command['arg']
		keySplit = keyString.lower().split(' ') # Split the key string into key and action.
		key = keySplit[0]
		action = keySplit[1] if len(keySplit) > 1 else 'press' # If no action, default to 'press'.

		# Map of alternate key names for pydirectinput, so users can use familiar key names from DCS controls.
		keyMap = {
			'altleft': [
				'lalt',
				'leftalt',
			],
			'altright': [
				'ralt',
				'rightalt',
			],
			'ctrlleft': [
				'lctrl',
				'leftctrl',
			],
			'ctrlright': [
				'rctrl',
				'rightctrl',
			],
			'shiftleft': [
				'lshift',
				'leftshift',
			],
			'shiftright': [
				'rshift',
				'rightshift',
			],
			'winleft': [
				'lwin',
				'leftwin',
			],
			'winright': [
				'rwin',
				'rightwin',
			],
			'pagedown': [
				'pgdn',
			],
			'pageup': [
				'pgup',
			],
			'add': {
				'numadd',
				'num+',
			},
			'subtract': {
				'numsubtract',
				'num-',
			},
			'multiply': {
				'nummultiply',
				'num*',
			},
			'divide': {
				'numdivide',
				'num/',
			},
			'decimal': {
				'numdecimal',
				'num.',
			},
		}

		# Check if the key is in any of the keyMap lists.
		if len(key) > 1 and key not in keyMap:
			for mapKey, aliases in keyMap.items():
				if key in aliases:
					key = mapKey
					break

		#print('in handleScriptKeyboard', key, action)
		self.updateOutput(f'Keyboard command:\t{keyString}', flush=True)

		# Add the numpad keys to the pydirectinput.KEYBOARD_MAPPING dictionary.  These are supported by pyautogui, but pyautogui.press() doesn't work in DCS.  They are commented out in pydirectinput, but seem to work fine if we add them back in.
		pydirectinput.KEYBOARD_MAPPING['num0'] = 0x52
		pydirectinput.KEYBOARD_MAPPING['num1'] = 0x4F
		pydirectinput.KEYBOARD_MAPPING['num2'] = 0x50
		pydirectinput.KEYBOARD_MAPPING['num3'] = 0x51
		pydirectinput.KEYBOARD_MAPPING['num4'] = 0x4B
		pydirectinput.KEYBOARD_MAPPING['num5'] = 0x4C
		pydirectinput.KEYBOARD_MAPPING['num6'] = 0x4D
		pydirectinput.KEYBOARD_MAPPING['num7'] = 0x47
		pydirectinput.KEYBOARD_MAPPING['num8'] = 0x48
		pydirectinput.KEYBOARD_MAPPING['num9'] = 0x49
		pydirectinput.KEYBOARD_MAPPING['numenter'] = 0x9C + 1024

		if not self.config['debug']:
			try:
				# If the DCS window isn't active, activate it (focus and bring to top).
				if not self.dcsWindow.isActive:
					self.dcsWindow.activate() # .focus() doesn't work, but .activate() does.  Then you need to wait a short time.
					time.sleep(0.06) # See pywinauto timings.py after_setfocus_wait, default is 0.06 seconds, and that seems to work here.

				#log(f'Sending key: {key}, action: {action}')
				if action == 'keydown' or action == 'down':
					sentKey = pydirectinput.keyDown(key)
				elif action == 'keyup' or action == 'up':
					sentKey = pydirectinput.keyUp(key)
				elif action == 'press':
					sentKey = pydirectinput.press(key)
				#log(f'sentKey: {sentKey}')

				if not sentKey:
					self.updateOutput(f"\nUnknown error sending key command to DCS.\nYou'll probably need to restart the script.\n", flush=True)
					self.stopFlag.set()
			except Exception as e:
				self.updateOutput(f"\nError sending key command to DCS: {e}\nYou'll probably need to restart the script.\n", flush=True)
				self.stopFlag.set()

		self.executedScriptKeyboardCommands += 1

	def handleScriptCockpitState(self, command):
		"""
		This will start looping, watching the current control state.  When the control state meets the command condition and value, start a timer.  If the control state ever fails to meet the condition, reset the timer.  When the control value has been in the command condition for the duration, exit the loop.
		"""
		# Ensure required parameters are provided
		if 'control' not in command or 'value' not in command:
			raise ValueError('Missing required parameters for scriptCockpitState: control and value must be provided')

		control = command['control']
		condition = command.get('condition', '=') # Default to '='
		value = command['value']
		duration = command.get('duration', 0) # Default to 0 seconds (immediate)

		# Throw an exception if the control doesn't exist in the DCS BIOS control list.
		if not self.dbe.controlExists(control):
			raise ValueError(f'Control "{control}" does not exist in the DCS BIOS control list.  Make sure to use the full control name, including the module name.')

		# Throw an exception if anything but int or str are passed (such as float).  DCS BIOS outputs are only int or str.
		if not isinstance(value, int) and not isinstance(value, str):
			raise TypeError('Only int or str are supported for scriptCockpitState values')

		valueType = 'str' if isinstance(value, str) else 'int' # NOTE Don't call this variable 'type' or it will override the built-in type function, and calls to type(value) will give unexpected error messages.  Ask me how I know.

		displayDuration = f' for {duration} sec' if duration else ''
		self.updateOutput(f'Wait for cockpit state:\t{control} {condition} {value}{displayDuration}... ', flush=True)
		controlState = None
		#self.updateOutput('\n')
		#self.updateOutput(f'scriptCockpitState, control: {control}, condition: {condition}, value: {value}, duration: {duration}')

		stateStartTime = None
		while not self.stopFlag.is_set():
			stateCurrentTime = time.time()

			conditionMet = False
			if not self.config['debug']:
				controlState = self.dbe.getControlState(control)[0][2]
				# Cast the controlState to the correct type based on the value type.
				controlState = int(controlState) if valueType == 'int' else str(controlState)
				#self.updateOutput(f'current controlState: {controlState}\n')

				# If valueType is int, compare them with math operators.
				if valueType == 'int':
					if condition == '=':
						conditionMet = controlState == value
					elif condition == '<':
						conditionMet = controlState < value
					elif condition == '<=':
						conditionMet = controlState <= value
					elif condition == '>':
						conditionMet = controlState > value
					elif condition == '>=':
						conditionMet = controlState >= value
					else:
						raise ValueError(f'Invalid condition for scriptCockpitState: {condition} not supported for int values')
				# If valueType is str, compare them with string operators.
				elif valueType == 'str':
					if condition == '=':
						conditionMet = controlState == value
					elif condition == 'startsWith':
						conditionMet = controlState.startswith(value)
					elif condition == 'endsWith':
						conditionMet = controlState.endswith(value)
					elif condition == 'contains':
						conditionMet = value in controlState
					else:
						raise ValueError(f'Invalid condition for scriptCockpitState: {condition} not supported for str values')

			if conditionMet or self.config['debug']:
				# If we don't have a timer already running, start one.
				if not stateStartTime:
					stateStartTime = time.time()
				# Check the elapsed time from when we started the timer.
				stateElapsedTime = stateCurrentTime - stateStartTime
				# If the elapsed time is greater than the duration, then the condition has been met for the required amount of time.  Break out of the loop.
				#self.updateOutput('stateElapsedTime', stateElapsedTime)
				if stateElapsedTime >= duration:
					break
			else:
				# Not meeting condition, so delete the timer.
				stateStartTime = None

			self.root.update()
			#time.sleep(0.01) # Sleep for a short time to save CPU cycles.

		self.updateOutput(f'Condition met', flush=True)

	def handleScriptTimer(self, command, timers):
		cmd = command['cmd'] # 'scriptTimerStart' or 'scriptTimerEnd'
		name = command['name']
		duration = command.get('duration', None) # 'end' action will not have a duration.

		if cmd == 'scriptTimerStart':
			self.updateOutput(f'Start timer:\t{name}, {duration} sec', flush=True)
			timers[name] = {
				'startTime': time.time(),
				'duration': duration,
			}
		elif cmd == 'scriptTimerEnd':
			remainingTime = self.getSecToMin(round(timers[name]['duration'] - (time.time() - timers[name]['startTime'])))
			self.updateOutput(f'Waiting for timer:\t{name}, {remainingTime} remaining... ', flush=True)
			while not self.stopFlag.is_set():
				currentTime = time.time()
				elapsedTime = currentTime - timers[name]['startTime']
				if elapsedTime >= timers[name]['duration']:
					self.updateOutput(f'Timer done', flush=True)
					break

				self.root.update()
				#time.sleep(0.01) # Sleep for a short time to save CPU cycles.


###############################################################################
###############################################################################
###############################################################################

# Initialize log file
logFilePath = 'DCSAutoMateLog.txt'
with open(logFilePath, 'w') as logFile:
	logFile.write('')  # Create an empty log file

def log(*args):
	# Get caller information
	frame = inspect.currentframe().f_back
	fileName = os.path.basename(frame.f_code.co_filename)
	lineNumber = frame.f_lineno

	# Create timestamp
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	# Format log message
	message = ' '.join(map(str, args))

	# Write to log file
	with open(logFilePath, 'a') as log_file:
		log_file.write(f'{timestamp} - {fileName}:{lineNumber} - {message}\n')


if __name__ == '__main__':
	# When running this program as an exe, we need to have its own path appended to the sys.path in order for it to find script files in the DCSAutoMateScripts subfolder.
	applicationPath = os.path.dirname(sys.executable)
	sys.path.append(applicationPath)

	root = tk.Tk()
	app = DCSAutoMateApp(root)
	root.mainloop()
