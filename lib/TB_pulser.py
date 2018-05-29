import serial, time

class pulser():
	def __init__(self, channel, port, baudrate, parity, stopbits, bytesize):
		self.channel  = channel
		self.port     = port
		self.baudrate = baudrate

		if   parity == 'NONE'  : self.parity = serial.PARITY_NONE
		elif parity == 'EVEN'  : self.parity = serial.PARITY_EVEN
		elif parity == 'ODD'   : self.parity = serial.PARITY_ODD
		elif parity == 'MARK'  : self.parity = serial.PARITY_MARK
		elif parity == 'SPACE' : self.parity = serial.PARITY_SPACE

		if   stopbits == '1'   : self.stopbits = serial.STOPBITS_ONE
		elif stopbits == '1.5' : self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
		elif stopbits == '2'   : self.stopbits = serial.STOPBITS_TWO

		if   bytesize == '5'   : self.bytesize = serial.FIVEBITS
		elif bytesize == '6'   : self.bytesize = serial.SIXBITS
		elif bytesize == '7'   : self.bytesize = serial.SEVENBITS
		elif bytesize == '8'   : self.bytesize = serial.EIGHTBITS

	def openPort(self):
		try:
			print(self.channel, self.port, self.baudrate, self.parity, self.stopbits, self.bytesize)
			print(type(self.channel))
			print(type(self.port))
			print(type(self.baudrate))
			print(type(self.parity))
			print(type(self.stopbits))
			print(type(self.bytesize))

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
