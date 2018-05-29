import serial, time

class pulser():
	def __init__(self, channel, port, baudrate, parity, stopbits, bytesize):
		self.channel=channel
		self.port=port
		self.baudrate=baudrate
		self.parity=parity
		self.stopbits=stopbits
		self.bytesize=bytesize

	def openPort(self):
		try:
			self.ser = serial.Serial(port=self.port,
									 baudrate=self.baudrate,
									 parity=self.parity,
									 stopbits=self.stopbits,
									 bytesize=self.bytesize)
			if(self.ser.isOpen()):
					print("Connected to Serial Port address : " + self.port)
			else:
					print('uh oh')
		except:
			print("Serial port " + self.port + " not found.")
			pass

	def setVoltage(self,V):
		command = "VSET{channel}:{volt:.2f}"
		V = float(V)
		command = command.format(channel=1, volt=V)
		self.ser.write(command.encode('utf-8'))
		time.sleep(0.1)

	def setCurrent(self,I):
		command = "ISET{channel}:{current:.2f}"
		I = float(I)
		command = command.format(channel=1, current=I)
		self.ser.write(command.encode('utf-8'))
		time.sleep(0.1)

	def setIV(self,V,I):
		self.setVoltage(V)
		time.sleep(0.1)
		self.setCurrent(I)
		time.sleep(0.1)

	def setOutput(self,out):
		if out=="ON":
			self.ser.write("OUT1".encode('utf-8'))
		else:
			self.ser.write("OUT0".encode('utf-8'))
		time.sleep(0.1)

	def closePort(self):
		self.ser.close()
		if not self.ser.isOpen():
		   print("Serial port closed.")
		else:
		   print('uh oh')
