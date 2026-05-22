import socket
import struct
import threading
import time
from tkinter import messagebox


class DCSAutoMateExportManager:
	"""
	Manages the export of data from DCS (Digital Combat Simulator) and processes it for display or further use.
	Attributes:
		config: Configuration settings for the manager.
		lock: A threading lock to ensure thread-safe operations.
		running: A boolean indicating whether the data update thread is running.
		dataStorage: A dictionary to store key/value pairs of data exported from DCS.
		outputSocket: The UDP socket used to receive data from DCS.
		messages: A dictionary containing messages for different states (e.g., no data, error).
		outputString: A string to store the formatted output data.
	Methods:
		getOutputSocket(): Configures and returns the UDP socket for receiving DCS data.
		parseData(data): Parses the received data and returns it as a dictionary.
		parseValue(value): Parses individual values from the data.
		formatTimeHHMMSS(seconds): Formats time in seconds to HH:MM:SS format.
		updateDataStorageContinuously(socketInstance): Continuously updates the data storage with received data.
		buildOutputString(): Builds a formatted string from the stored data.
		start(): Starts the continuous data update thread.
		stop(): Stops the continuous data update thread.
	"""

	def __init__(self, config):
		self.config = config
		self.lock = threading.Lock()
		self.running = False
		self.dataStorage = {} # Dict to store key/value pairs of data exported from DCS.
		self.outputSocket = self.getOutputSocket()
		self.messages = {
			'noData': "No data to show.",
			'error': 'Error',
		}
		self.outputString = ''

	def getOutputSocket(self):
		# Configuration
		UDP_IP = '0.0.0.0'
		UDP_PORT = 6121
		MULTICAST_GROUP = '239.255.61.21'
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

	def parseData(self, data):
		decodedData = data.decode('utf-8')
		dcsData = {}
		for item in decodedData.split(';'):
			if '=' in item:
				key, value = item.split('=', 1)
				keys = key.split('.')
				tempDict = dcsData
				for k in keys[:-1]:
					tempDict = tempDict.setdefault(k, {})
				tempDict[keys[-1]] = self.parseValue(value)
		return dcsData

	def parseValue(self, value):
		try:
			return float(value) if '.' in value else int(value)
		except ValueError:
			if value.lower() == 'true':
				return True
			elif value.lower() == 'false':
				return False
			return value

	def formatTimeHHMMSS(self, seconds):
		h = seconds // 3600
		m = (seconds % 3600) // 60
		s = seconds % 60
		return f"{int(h):02}:{int(m):02}:{int(s):02}"

	def updateDataStorageContinuously(self, socketInstance):
		"""Thread function to update the data storage."""
		blockingErrors = 0
		while self.running:
			try:
				data, _ = socketInstance.recvfrom(16384) # This needs to be large enough to handle the largest UDP packet size that is exported from DCSAutoMateExport.lua.
				#print('data', data)
				parsedData = self.parseData(data)
				#print('parsedData', parsedData)
				with self.lock:
					self.dataStorage = parsedData

				self.outputString = self.buildOutputString()

				# On successful receive, reset the blocking error counter.
				blockingErrors = 0
			except BlockingIOError:
				# No data available, continue the loop
				# If we get more than 10 blocking errors in a row, we're probably not getting any data at all, so we should show "no data".
				blockingErrors += 1
				if blockingErrors > 10:
					self.outputString = self.messages['noData']
			except Exception as e:
				self.outputString = self.messages['error']
				messagebox.showerror("Error", f"Error while receiving DCSAutoMateExport data: {e}\nPlease restart DCSAutoMate.")
				self.stop()
				break

			# We get data from DCSAutoMateExport.lua every second, so we don't need to loop this as fast as possible.  However, sleep(1) is too slow and we'll miss data packets.
			time.sleep(0.1)  # Small delay to prevent CPU overuse

	def buildOutputString(self):
		#print('inBuildOutputString', self.dataStorage)
		outputString = ''
		try:
			altMSL = self.dataStorage['LoGetAltitudeAboveSeaLevel']
			altAGL = self.dataStorage['LoGetAltitudeAboveGroundLevel']
			altRadar = self.dataStorage['LoGetRadarAltimeter']
			altObj = self.dataStorage['LoGetHeightWithObjects']
			airspeedTAS = self.dataStorage['LoGetTrueAirSpeed']
			airspeedIAS = self.dataStorage['LoGetIndicatedAirSpeed']

			missionStartTime = self.dataStorage['LoGetMissionStartTime']
			missionElapsedTime = self.dataStorage['LoGetModelTime']
			missionTimeSeconds = missionStartTime + missionElapsedTime
			missionTimeString = self.formatTimeHHMMSS(missionTimeSeconds)

			moduleName = self.dataStorage['LoGetSelfData']['Name']

			outputString += f"Aircraft: {moduleName}\n"

			outputString += f"Mission time: {missionTimeString}\n"
			if missionTimeString >= '06:00:00' and missionTimeString <= '20:00:00':
				outputString += "It's between 0600 and 2000, probably daytime.\n"
			else:
				outputString += "It's between 2000 and 0600, probably nighttime.\n"

			if altAGL < 5:
				outputString += "You're probably on the ground.\n"
			elif altAGL - altMSL < 2 and altMSL > 15 and altMSL < 25 and airspeedTAS < 40:
				outputString += "You're probably on the carrier deck.\n"
			else:
				outputString += "You're probably in the air.\n"

			# Single-engined planes will only have RPM for left engine.
			if self.dataStorage['LoGetEngineInfo']['RPM']['left'] > 0:
				outputString += "Engine is running.\n"
			else:
				outputString += "Engine is off.\n"

			if moduleName == 'AH-64D_BLK_II':
				longbowEquipped = False
				for stationId, stationData in self.dataStorage['LoGetPayloadInfo']['Stations'].items():
					if stationData['CLSID'] == '{AN_APG_78}' and stationData['count'] > 0:
						longbowEquipped = True
						break
				if longbowEquipped:
					outputString += "Longbow radar equipped.\n"
				else:
					outputString += "Longbow radar not equipped.\n"

		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet, so show "no data".
			outputString = self.messages['noData']

		# Trim the last newline character if it exists
		outputString = outputString.rstrip('\n')
		return outputString

	def start(self):
		"""Start the continuous update thread."""
		self.running = True
		self.thread = threading.Thread(target=self.updateDataStorageContinuously, args=(self.outputSocket,))
		self.thread.daemon = True # Daemonize the thread so it stops with the main program
		self.thread.start()

	def stop(self):
		"""Stop the continuous update thread."""
		#print("Stopping DAME thread...")
		self.running = False
		try:
			self.outputSocket.shutdown(socket.SHUT_RDWR)
			self.outputSocket.close()
		except Exception as e:
			#print(f"Error shutting down socket: {e}")
			pass

		#print("Waiting for thread to join...")
		self.thread.join(timeout=0)  # FIXME Immediately kill the thread if it doesn't join.  It's not joining, and I'm not sure why, so this prevents the app from hanging on exit until it times out.
		if self.thread.is_alive():
			#print("Thread did not finish in time, forcing exit.")
			pass

		#print("DAME thread stopped.")
