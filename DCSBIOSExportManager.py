from glob import glob
import json
import os
import socket
import struct
import threading
import time
from tkinter import messagebox

class DCSBIOSExportManager:
	"""
	DCSBIOSExportManager is responsible for managing the export of DCS BIOS data. It handles the configuration,
	loading of JSON data, parsing of DCS BIOS packets, and updating a storage array with the received data.
	It also provides methods to retrieve and interpret the data for specific controls.
	Attributes:
		config: Configuration settings.
		jsonData: Loaded JSON data from DCS BIOS.
		storageArray: A bytearray representing 64KB of memory space.
		lock: A threading lock for synchronizing access to the storage array.
		running: A boolean indicating if the continuous update thread is running.
		outputSocket: The UDP socket used for receiving DCS BIOS data.
		messages: A dictionary of status messages.
		updateCounterControl: The control used to track updates.
		outputString: A string representing the current status of data reception.
	Methods:
		getOutputSocket(): Configures and returns the UDP socket for receiving DCS BIOS data.
		loadJsonData(): Loads JSON data from the specified directory.
		parseDCSBIOSPacket(data): Parses a DCS BIOS packet and returns the parsed data.
		updateStorageArrayContinuously(socketInstance): Continuously updates the storage array with received data.
		updateStorageArray(storageArray, parsedData): Updates the storage array with parsed data.
		retrieveString(storageArray, startAddress, maxLength): Retrieves a string from the storage array.
		interpretData(jsonData, storageArray, listControlsToGet): Interprets data from the storage array based on JSON definitions.
		getControlState(listControlsToGet): Retrieves the state of specified controls.
		start(): Starts the continuous update thread.
		stop(): Stops the continuous update thread.
	"""
	def __init__(self, config):
		self.config = config
		self.jsonData = self.loadJsonData()
		self.storageArray = bytearray(65536)  # 64KB memory space
		self.lock = threading.Lock()
		self.running = False
		self.outputSocket = self.getOutputSocket()
		self.messages = {
			'base' : 'DCS BIOS data stream: ',
			'notReceiving': 'Not receiving data',
			'receiving': 'Receiving data',
			'error': 'Error',
		}
		self.updateCounterControl = 'MetadataEnd/_UPDATE_COUNTER'
		self.outputString = ''

	def getOutputSocket(self):
		# Configuration
		UDP_IP = '0.0.0.0'
		UDP_PORT = 5010
		MULTICAST_GROUP = '239.255.50.10'
		# Create a UDP socket for reading DCS BIOS data.
		outputSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		outputSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# Bind the socket to the address and port
		outputSocket.bind((UDP_IP, UDP_PORT))
		group = socket.inet_aton(MULTICAST_GROUP)
		mreq = struct.pack('4sL', group, socket.INADDR_ANY)
		outputSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

		# Set the socket to non-blocking mode
		outputSocket.setblocking(False)

		return outputSocket

	def loadJsonData(self):
		jsonDirectory = ''
		if self.config.get('dcsSavedGamesOverride', ''):
			jsonDirectory = os.path.join(self.config['dcsSavedGamesOverride'], 'Scripts', 'DCS-BIOS', 'doc', 'json')
			jsonDirectory = jsonDirectory.replace('%USERPROFILE%', os.environ['USERPROFILE'])
			if not os.path.exists(dir):
				# No valid path found.
				raise FileNotFoundError(f"Directory not found: {jsonDirectory}")
		else:
			# Look in the default paths.
			dcsSavedGamesPaths = [
				f'%USERPROFILE%\\Saved Games\\DCS',
				f'%USERPROFILE%\\Saved Games\\DCS.openbeta',
			]
			for path in dcsSavedGamesPaths:
				dir = os.path.join(path, 'Scripts', 'DCS-BIOS', 'doc', 'json')
				dir = dir.replace('%USERPROFILE%', os.environ['USERPROFILE'])
				# Take the first path found that exists.
				if os.path.exists(dir):
					jsonDirectory = dir
					break

			if not jsonDirectory:
				# No valid path found.
				raise FileNotFoundError(f"Directory not found.: {jsonDirectory}")

		jsonData = {}

		for filepath in glob(os.path.join(jsonDirectory, '*.json')):
			filename = os.path.basename(filepath)
			with open(filepath, 'r') as file:
				jsonData[filename] = json.load(file)

		return jsonData

	def parseDCSBIOSPacket(self, data):
		parsedData = {}
		index = 4  # Skip the first 4 bytes (frame sync)
		while index < len(data):
			# Read address (2 bytes, little-endian)
			address = data[index] | (data[index + 1] << 8)
			index += 2

			# Read count/size (2 bytes, little-endian)
			count = data[index] | (data[index + 1] << 8)
			index += 2

			# Read the data (count bytes)
			parsedData[address] = data[index:index + count]
			index += count

		return parsedData

	def updateStorageArrayContinuously(self, socketInstance):
		"""Thread function to update the storage array."""
		blockingErrors = 0
		while self.running:
			try:
				data, _ = socketInstance.recvfrom(2048) # See MAX_PAYLOAD SIZE in DCS-BIOS\lib\ConnectionManager.lua
				#print('data', data)
				parsedData = self.parseDCSBIOSPacket(data)
				with self.lock:
					self.updateStorageArray(self.storageArray, parsedData)
				updateCounter = self.getControlState(self.updateCounterControl)[0][2]
				self.outputString = f'{self.messages["base"]}{self.messages["receiving"]} {updateCounter}'

				# On successful receive, reset the blocking error counter.
				blockingErrors = 0
			except BlockingIOError as e:
				# No data available, continue the loop
				# If we get more than 2 blocking errors in a row, we're probably not getting any data at all, so we should show "no data".
				blockingErrors += 1
				if blockingErrors > 2:
					self.outputString = f'{self.messages["base"]}{self.messages["notReceiving"]}'
				pass
			except Exception as e:
				self.outputString = f'{self.messages["base"]}{self.messages["error"]}'
				messagebox.showerror("Error", f"Error while receiving DCS BIOS data packets: {e}\nPlease restart DCSAutoMate.")
				self.stop()
				break

			time.sleep(0.01)  # Small delay to prevent CPU overuse

	def updateStorageArray(self, storageArray, parsedData):
		for address, data in parsedData.items():
			storageArray[address:address + len(data)] = data

	def retrieveString(self, storageArray, startAddress, maxLength):
		stringData = storageArray[startAddress:startAddress + maxLength]
		return ''.join(chr(b) for b in stringData if b != 0)

	def interpretData(self, jsonData, storageArray, listControlsToGet):
		results = {}
		for filename, moduleData in jsonData.items():
			if isinstance(moduleData, dict):
				for category, controls in moduleData.items():
					if isinstance(controls, dict):
						for controlName, controlData in controls.items():
							identifier = controlData.get('identifier', controlName)
							for output in controlData.get('outputs', []):
								address = output['address']
								maxLength = output.get('max_length', 0)
								valueType = output['type']
								description = controlData.get('description', controlName)

								# Construct the full control reference
								controlReference = f"{filename[:-5]}/{identifier}"

								if controlReference not in listControlsToGet:
									continue

								if valueType == 'string':
									value = self.retrieveString(storageArray, address, maxLength)
								elif valueType == 'integer':
									mask = output['mask']
									shiftBy = output['shift_by']
									value = (storageArray[address] | (storageArray[address + 1] << 8)) & mask
									value >>= shiftBy
									value = int(value)
								else:
									continue

								results[controlReference] = (controlReference, description, value)

		# Order results based on listControlsToGet
		orderedResults = [results[ref] for ref in listControlsToGet if ref in results]
		return orderedResults

	def getControlState(self, listControlsToGet):
		"""
		Retrieve the state of a specific control.
		Returns list of all listControlsToGet as tuples: [(<identifier>, <description>, <value>), (...)]
		e.g. [('MetadataStart/_ACFT_NAME', 'Aircraft Name (or NONE), null-terminated', 'F-4E-45MC              ')]
		"""
		# If a single string is passed, convert it to a list with one element.
		if isinstance(listControlsToGet, str):
			listControlsToGet = [listControlsToGet]
		with self.lock:
			return self.interpretData(self.jsonData, self.storageArray, listControlsToGet)

	 # Check if a control exists in the JSON data
	def controlExists(self, controlName):
		for filename, moduleData in self.jsonData.items():
			if isinstance(moduleData, dict):
				for category, controls in moduleData.items():
					if isinstance(controls, dict):
						for cName, controlData in controls.items():
							identifier = controlData.get('identifier', cName)
							controlReference = f'{filename[:-5]}/{identifier}'
							if controlReference == controlName:
								return True
		return False

	def start(self):
		"""Start the continuous update thread."""
		self.running = True
		self.thread = threading.Thread(target=self.updateStorageArrayContinuously, args=(self.outputSocket,))
		self.thread.daemon = True # Daemonize the thread so it stops with the main program
		self.thread.start()
		self.outputString = f'{self.messages["base"]}{self.messages["receiving"]}'

	def stop(self):
		"""Stop the continuous update thread."""
		#print("Stopping DBE thread...")
		self.running = False
		try:
			self.outputSocket.shutdown(socket.SHUT_RDWR)
			self.outputSocket.close()
		except Exception as e:
			#print(f"Error shutting down socket: {e}")
			pass

		self.outputString = f'{self.messages["base"]}{self.messages["notReceiving"]}'

		#print("Waiting for thread to join...")
		self.thread.join(timeout=0)  # FIXME Immediately kill the thread if it doesn't join.  It's not joining, and I'm not sure why, so this prevents the app from hanging on exit until it times out.
		if self.thread.is_alive():
			#print("Thread did not finish in time, forcing exit.")
			pass

		#print("DBE thread stopped.")
