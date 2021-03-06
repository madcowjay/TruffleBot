"""
Updated 2018/05/06
  -SPI_CHANNEL, SPI_FREQUENCY, and CS_PIN are now set when initialized

  -Python3 only supported now
  -Cleaned up some bytearray stuff for clarity and consistency with pyads1256.py

  -Fixed bug where output was incorrect in least significant byte when most
			significant byte was nonzero due to masking error
  -Added ability to use SPI_CE0 or SPI_CE1 as CS pin
  -Reduced write times by writing all three chars with one write command vs. three
  -Cleaned up DEBUG output
  -Changed back to physical CS pin address (easy enough to modify on the fly)
  -Added DAC8532 register table
  -Expanded BUFFERSELECT to _A and _B varieties for clarity
  -Added PowerDownDACA function
  -Python2 and Python3 compatible
														 -JW
"""
import wiringpi as wp
from   lib.debug_print import *


class DAC8532:
	"A DAC8532 object"

	"""
	Wiring Diagram for Pi
	 +-----+-----+---------+------+---+---Pi 2---+---+------+---------+-----+-----+
	 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
	 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
	 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
	 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5V      |     |     |
	 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
	 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 1 | ALT0 | TxD     | 15  | 14  |
	 |     |     |      0v |      |   |  9 || 10 | 1 | ALT0 | RxD     | 16  | 15  |
	 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 1 | IN   | GPIO. 1 | 1   | 18  |
	 |  27 |   2 | GPIO. 2 |   IN | 1 | 13 || 14 |   |      | 0v      |     |     |
	 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
	 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
	 |  10 |  12 |    MOSI | ALT0 | 0 | 19 || 20 |   |      | 0v      |     |     |
	 |   9 |  13 |    MISO | ALT0 | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
	 |  11 |  14 |    SCLK | ALT0 | 0 | 23 || 24 | 1 | OUT  | CE0     | 10  | 8   |
	 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
	 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
	 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
	 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
	 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
	 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
	 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
	 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
	 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
	 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
	 +-----+-----+---------+------+---+---Pi 2---+---+------+---------+-----+-----+ """

	# These options can be adjusted to facilitate specific operation of the
	# DAC8532, the defaults are designed to be compatible with the Waveforms
	# High Precision AD/DA board
	# SPI_CHANNEL's value isn't really used in this implementation, but you should be aware that the default SPI enable pin
	#    on the Pi  - CE0 (Pin 24) or CE1 (Pin 26) will be toggled by the underlying functions during comms
	SPI_MODE        = 1
	# SPI_CHANNEL     = 0
	# SPI_FREQUENCY   = 250000
	# CS_PIN          = 16    # The physical pin to use for chip select and ready polling

	""" Register for DAC8532
	+------+------+------+------+------+----------------+------+------+------+------+------+------+
	| DB23 | DB22 | DB21 | DB20 | DB19 |      DB18      | DB17 | DB16 | DB15 | DB14 | DB13 | DB12 |
	+------+------+------+------+------+----------------+------+------+------+------+------+------+
	|  0   |  0   |  LDB |  LDA |  X   |  Buffer Select |  PD1 |  PD0 |  D15 |  D14 |  D13 |  D12 |
	+------+------+------+------+------+----------------+------+------+------+------+------+------+

	+------+------+------+------+------+----------------+------+------+------+------+------+------+
	| DB11 | DB10 | DB9  | DB8  | DB7  |      DB6       | DB5  | DB4  | DB3  | DB2  | DB1  | DB0  |
	+------+------+------+------+------+----------------+------+------+------+------+------+------+
	|  D11 |  D10 |  D9  |  D8  |  D7  |       D6       |  D5  |  D4  |  D3  |  D2  |  D1  |  D0  |
	+------+------+------+------+------+----------------+------+------+------+------+------+------+
	"""
	# DAC control bits
	LOAD_DACB      = 1 << 21
	LOAD_DACA      = 1 << 20
	BUFFERSELECT_A = 0 << 18
	BUFFERSELECT_B = 1 << 18
	PD1            = 1 << 17
	PD0            = 1 << 16

	def __init__(self, SPI_CHANNEL, SPI_FREQUENCY, CS_PIN):
		"Instantiates a DAC object with the given parameters"

		self.SPI_CHANNEL = SPI_CHANNEL
		self.SPI_FREQUENCY = SPI_FREQUENCY
		self.CS_PIN = CS_PIN

		debug_print('pydac8532 initializing with:')
		debug_print('   SPI_MODE      = %d' % self.SPI_MODE)
		debug_print('   SPI_CHANNEL   = %d' % self.SPI_CHANNEL)
		debug_print('   SPI_FREQUENCY = ' + format(self.SPI_FREQUENCY,','))
		debug_print('   CS_PIN = %d' %self.CS_PIN)

		# Set up the wiringPi object to use physical pin numbers
		wp.wiringPiSetupPhys()

		# Initialize CS pin
		wp.pinMode(self.CS_PIN, wp.OUTPUT)
		wp.digitalWrite(self.CS_PIN, wp.HIGH)

		# Initialize the wiringPi SPI setup
		spi_success = wp.wiringPiSPISetupMode(self.SPI_CHANNEL, self.SPI_FREQUENCY, self.SPI_MODE)  #JKR
		debug_print('SPI success: ' + str(spi_success))


	def __ChipSelect(self):
		wp.digitalWrite(self.CS_PIN, wp.LOW)


	def __ChipRelease(self):
		wp.digitalWrite(self.CS_PIN, wp.HIGH)


	def __SendBytes(self, myBytearray):
		temp = ''
		for c in myBytearray:
			temp += '\\x%02x' % c
		debug_print('Sending bytes:  ' + temp)
		result = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, bytes(myBytearray))
		temp = ''
		for c in result[1]:
			temp += '\\x%02x' % c
		debug_print('Result:         ' + temp)
		return result[1]


	def SendDACAValue(self, newValue):
		"Send DAC A a new value between 0 and 2^16-1"
		debug_print('Send DAC A: ' + str(int(newValue)).rjust(16))
		self.__ChipSelect() #only needed if not using CE0 or CE1, but doesn't hurt otherwise
		byte1 = ((self.LOAD_DACA | self.BUFFERSELECT_A) >> 16) & 0xFF
		byte2 = (int(newValue) >> 8) & 0xFF
		byte3 = (int(newValue)     ) & 0xFF
		self.__SendBytes(bytearray((byte1,byte2,byte3)))
		self.__ChipRelease() #only needed if not using CE0 or CE1, but doesn't hurt otherwise


	def SendDACBValue(self, newValue):
		"Send DAC B a new value between 0 and 2^16-1"
		debug_print('Send DAC B: ' + str(int(newValue)).rjust(16))
		self.__ChipSelect() #only needed if not using CE0 or CE1, but doesn't hurt otherwise
		byte1 = ((self.LOAD_DACB | self.BUFFERSELECT_B) >> 16) & 0xFF
		byte2 = (int(newValue) >> 8) & 0xFF
		byte3 = (int(newValue)     ) & 0xFF
		self.__SendBytes(bytearray((byte1,byte2,byte3)))
		self.__ChipRelease() #only needed if not using CE0 or CE1, but doesn't hurt otherwise


	def PowerDownDACA(self):
		"Powers down DAC A to high impedance"
		debug_print('Powering down DAC A')
		self.__ChipSelect() #only needed if not using CE0 or CE1, but doesn't hurt otherwise
		byte1 = (((self.LOAD_DACA | self.BUFFERSELECT_A | self.PD1 | self.PD0) >> 16) & 0xFF)
		byte2 = (0 & 0xFF)
		byte3 = (0 & 0xFF)
		self.__SendBytes(bytearray((byte1,byte2,byte3)))
		self.__ChipRelease() #only needed if not using CE0 or CE1, but doesn't hurt otherwise


	def PowerDownDACB(self):
		"Powers down DAC B to high impedance"
		debug_print('Powering down DAC B')
		self.__ChipSelect() #only needed if not using CE0 or CE1, but doesn't hurt otherwise
		byte1 = (((self.LOAD_DACB | self.BUFFERSELECT_B | self.PD1 | self.PD0) >> 16) & 0xFF)
		byte2 = (0 & 0xFF)
		byte3 = (0 & 0xFF)
		self.__SendBytes(bytearray((byte1,byte2,byte3)))
		self.__ChipRelease() #only needed if not using CE0 or CE1, but doesn't hurt otherwise
