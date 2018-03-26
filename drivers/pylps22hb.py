"""
Driver for SPI interface on LPS22HB pressure Sensor.
February 2018 - Jason Webster
"""

from __future__ import print_function
import os
import time
import wiringpi as wp
import numpy as np

if os.environ["blah"] == 'True':
    DEBUG = True
else:
    DEBUG = False

def debug_print(string):
    if DEBUG:
        print("DEBUG: " + string)


class LPS22HB:
    """ Wiring Diagram for Raspberry Pi
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
     +-----+-----+---------+------+---+---Pi 2---+---+------+---------+-----+-----+
    """

    SPI_MODE        = 1
    SPI_CHANNEL     = 1
    SPI_FREQUENCY   = 10000000 # The LPS22HB supports 10 MHz only
    #DRDY_TIMEOUT    = 0.5 # Seconds to wait for DRDY when communicating
    #DATA_TIMEOUT    = 0.00001 # 10uS delay for sending data

    # The RPI GPIO to use for chip select - set when initialized
    CS_PIN = 0

    """
    16 bit commands (typically)
    bit0:     R or W - 0 to write to device, 1 to read
    bit 1-7:  Address AD(6:0) MSb first
    bit 8-15: Data DI(7:0) or DO(7:0) MSb first
    """
    READ_MASK  = 0b10000000
    WRITE_MASK = 0b00000000
    DUMMY_BYTE = 0b01010101

    # Register addresses
    REG_INTERRUPT_CFG  = 0x0B #R/W Interrupt register
    REG_THIS_P_L       = 0x0C #R/W Pressure threshold register
    REG_THIS_P_H       = 0x0D #R/W Pressure threshold register
    REG_WHO_AM_I       = 0x0F # R  Who am I = 0b10110001
    REG_CTRL_REG1      = 0x10 #R/W Control register
    REG_CTRL_REG2      = 0x11 #R/W Control register
    REG_CTRL_REG3      = 0x12 #R/W Control register
    REG_FIFO_CTRL      = 0x14 #R/W FIFO configuration register
    REG_REF_P_XL       = 0x15 #R/W Reference pressure register
    REG_REF_P_L        = 0x16 #R/W Reference pressure register
    REG_REF_P_H        = 0x17 #R/W Reference pressure register
    REG_RPDS_L         = 0x18 #R/W Pressure offset register
    REG_RPDS_H         = 0x19 #R/W Pressure offset register
    REG_RES_CONF       = 0x1A #R/W Resolution register
    REG_INT_SOURCE     = 0x25 # R  Interrupt register
    REG_FIFO_STATUS    = 0x26 # R  FIFO status register
    REG_STATUS         = 0x27 # R  Status register
    REG_PRESS_OUT_XL   = 0x28 # R  Pressure output register
    REG_PRESS_OUT_L    = 0x29 # R  Pressure output register
    REG_PRESS_OUT_H    = 0x2A # R  Pressure output register
    REG_TEMP_OUT_L     = 0x2B # R  Temperature output register
    REG_TEMP_OUT_H     = 0x2C # R  Temperature output register
    REG_LPFP_RES       = 0x33 # R  Filter reset register
    NUM_REG            = 23

    """
    CTRL_REG1 Register: 0x10

    Bit 7:
        must be set to 0
    Bits 6-4 ODR[2:0]: Data Rate Setting
        000 = Power down / one-shot mode enabled (default)
        001 = 1  Hz
        010 = 10 Hz
        011 = 25 Hz
        100 = 50 Hz
        101 = 75 Hz
    Bit 3 EN_LPFP: Enable low-pass filter
        0 = disabled (default)
        1 = enabled
    Bit 1 LPFP_CFG: Low-pass configuration register
        0 (default)
    Bit 1 BDU: Block data update
        0 = continuous update (default)
        1 = output registers not updated until MSB and LSB have been read
    Bit 0 SIM: SPI Serial Interface Mode selsction
        0 = 4-wire (default)
        1 = 3-wire

    """
    # sample rates
    DRATE_0  = 0b000 # 0  Hz (default)
    DRATE_1  = 0b001 # 1  Hz
    DRATE_10 = 0b010 # 10 Hz
    DRATE_25 = 0b011 # 25 Hz
    DRATE_50 = 0b100 # 50 Hz
    DRATE_75 = 0b101 # 75 Hz

    # Initialize the pressure sensors
    def __init__(self, cs_pin):
        debug_print('pylps22hb initializing with:')
        debug_print('   >SPI_MODE      = %d' % self.SPI_MODE)
        debug_print('   >SPI_CHANNEL   = %d' % self.SPI_CHANNEL)
        debug_print('   >SPI_FREQUENCY = ' + format(self.SPI_FREQUENCY,','))
        debug_print('   >CS_PIN        = %d' % cs_pin)

        self.CS_PIN = cs_pin

        # Set up the wiringpi object to use physical pin numbers
        wp.wiringPiSetupPhys()

        # Initialize CS pins
        wp.pinMode(self.CS_PIN, wp.OUTPUT)
        wp.digitalWrite(self.CS_PIN, wp.HIGH)

        # Initialize the wiringpi SPI setup
        #spi_success = wp.wiringPiSPISetup(self.SPI_CHANNEL, self.SPI_FREQUENCY)
        spi_success = wp.wiringPiSPISetupMode(self.SPI_CHANNEL, self.SPI_FREQUENCY, self.SPI_MODE)  #JKR
        debug_print("  SPI success " + str(spi_success))

    def delayMicroseconds(self, delayus):
        wp.delayMicroseconds(delayus)

    def chip_select(self):
        debug_print('selecting pin ' + str(self.CS_PIN))
        wp.digitalWrite(self.CS_PIN, wp.LOW)

    def chip_release(self):
        debug_print('releasing pin ' + str(self.CS_PIN))
        wp.digitalWrite(self.CS_PIN, wp.HIGH)

    #new DAC style
    def SendString(self, myString):
        if DEBUG:
            print('DEBUG:    Sending bytes:  ', end=''),
            for c in myString:
                print('c = ' + str(c) + ' or \\x%02x, ' % c, end='')
            print('')
        result = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, bytes(myString))
        debug_print(" SendString: result = " + str(result))
        return (result)

    def ReadID(self):
        """
        Read the ID from the LPS chip
        :returns: numeric identifier of the LPS chip
        """
        debug_print("ReadID")
        self.chip_select()
        time.sleep(.1)
        byte1 = self.READ_MASK | self.REG_WHO_AM_I
        byte2 = self.DUMMY_BYTE
        debug_print('   Passing these decimal bytes to SendString:   %03d %03d' % (byte1, byte2))
        result = self.SendString(bytearray((byte1,)) + bytearray((byte2,)))
        myid = hex(ord((result[1][1])))
        debug_print(" readID: myid = " + myid)
        self.chip_release()
        return (myid)

    def ReadControlRegisters(self):
        """
        Read the control registers from the LPS chip
        :returns: #TODO
        """
        debug_print("ReadTemp")
        byte0 = self.READ_MASK | self.REG_INTERRUPT_CFG
        byte1 = self.READ_MASK | self.REG_CTRL_REG1
        byte2 = self.READ_MASK | self.REG_CTRL_REG2
        byte3 = self.READ_MASK | self.REG_CTRL_REG3
        byte4 = self.DUMMY_BYTE
        self.chip_select()
        time.sleep(.5)
        map = '     0B   0C   0D   0E   0F   10   11   12   13   14   15   16   17   18   19   1A   1B   1C   1D   1E   1F   20   21   22   23   24   25   26   27   28   29   2A   2B   2C'
        # debug_print('   Passing these decimal bytes to SendString:   %03d %03d' % (byte1, byte4))
        result = self.SendString(bytearray((byte0,)) + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,))
                                 + bytearray((byte4,)) + bytearray((byte4,)) + bytearray((byte4,))  + bytearray((byte4,)) + bytearray((byte4,)))
        reges = hex(ord((result[1][1])))
        start = 0x0A
        for reg in result[1]:
            if start == 0x0A:
                print('   : ' + hex(ord(reg)))
            else:
                print(format(int(start), '02x') + ': ' + hex(ord(reg)))
            start = start + 1
        self.chip_release()
        return (reges)

    def ReadTemp(self):
        """
        Read the temperature from the LPS chip
        :returns: temperature in 2's complement
        """
        debug_print("ReadTemp")
        byte1 = self.READ_MASK | self.REG_TEMP_OUT_L
        byte2 = self.READ_MASK | self.REG_TEMP_OUT_H
        byte3 = self.DUMMY_BYTE
        self.chip_select()
        time.sleep(.5)
        debug_print('   Passing these decimal bytes to SendString:   %03d %03d' % (byte1, byte3))
        result_L = self.SendString(bytearray((byte1,)) + bytearray((byte3,)))
        mytemp_L = hex(ord((result_L[1][1])))
        debug_print(" readTemp: mytemp_L = " + mytemp_L)

        time.sleep(.5)
        debug_print('   Passing these decimal bytes to SendString:   %03d %03d %03d' % (byte3, byte3, byte3))
        result_both = self.SendString(bytearray((byte3,)) + bytearray((byte3,)) + bytearray((byte3,)))
        mytemp_L = hex(ord((result_both[1][1])))
        mytemp_H = hex(ord((result_both[1][2])))
        debug_print(" readTemp: mytemp_L = " + mytemp_L + " , mytemp_H = " + mytemp_H)
        self.chip_release()
        return (mytemp_L)
