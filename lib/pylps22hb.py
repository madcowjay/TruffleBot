"""
Driver for SPI interface on LPS22HB pressure Sensor.
February 2018 - Jason Webster
"""

from __future__ import debug_print_function
import os, time
import wiringpi as wp
import numpy as np
from   lib.debug_print import *


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
    # SPI_CHANNEL     = 1
    # SPI_FREQUENCY   = 10000000 # The LPS22HB supports 10 MHz only


    """
    16 bit commands (typically)
    bit0:     R or W - 0 to write to device, 1 to read
    bit 1-7:  Address AD(6:0) MSb first
    bit 8-15: Data DI(7:0) or DO(7:0) MSb first
    """
    READ_MASK  = 0b10000000
    WRITE_MASK = 0b00000000
    DUMMY_BYTE = 0b11111111

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
    def __init__(self, SPI_CHANNEL, SPI_FREQUENCY, CS_PIN):

        self.SPI_CHANNEL = SPI_CHANNEL
        self.SPI_FREQUENCY = SPI_FREQUENCY
        self.CS_PIN = CS_PIN

        debug_print('pylps22hb initializing with:')
        debug_print('   >SPI_MODE      = %d' % self.SPI_MODE)
        debug_print('   >SPI_CHANNEL   = %d' % self.SPI_CHANNEL)
        debug_print('   >SPI_FREQUENCY = ' + format(self.SPI_FREQUENCY,','))
        debug_print('   >CS_PIN        = %d' % CS_PIN)



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
    def __SendBytes(self, myBytearray):
        temp = ''
        for c in myBytearray:
            temp += '\\x%02x' % c
        debug_print('Sending bytes:  ' + temp)
        result = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, bytes(myBytearray))
        debug_print(" SendBytes: result = " + str(result))
        return result

    def ReadID(self):
        """
        Read the ID from the LPS chip
        :returns: numeric identifier of the LPS chip
        """
        debug_print("ReadID")
        self.chip_select()
        byte1 = self.READ_MASK | self.REG_WHO_AM_I
        byte2 = self.DUMMY_BYTE
        result = self.__SendBytes(bytearray((byte1,byte2)))
        self.chip_release()
        myid = hex((result[1][1]))
        debug_print(" readID: myid = " + myid)
        return (myid)

    def ReadRegisters(self):
        """
        Read all the registers from the LPS chip and displays them on the screen
        :returns: bytes read from the SPI transfer
        """
        debug_print("ReadRegisters")
        byte1 = self.READ_MASK | self.REG_INTERRUPT_CFG
        byte2 = self.DUMMY_BYTE
        self.chip_select()
        result = self.__SendBytes(bytearray([byte1]+41*[byte2]))
        self.chip_release()
        index = 0x0A
        skip_registers = [0x0A, 0x0E, 0x13] + range(0x1B, 0x25) + range(0x2D, 0x33)
        for reg in result[1]:
            if index not in skip_registers:
                debug_print('  ' + format(int(index), '02X') + ': ' + format(ord(reg), '08b') + ' = '+ format(ord(reg), '02x'), end='')
                if   index == 0x0B: debug_print(' <----INTERRUPT_CFG')
                elif index == 0x0F: debug_print(' <--WHO_AM_I')
                elif index == 0x10: debug_print(' <----CTRL_REG1')
                elif index == 0x28: debug_print(' <--PRESS_OUT_XL')
                elif index == 0x29: debug_print(' <--PRESS_OUT_L')
                elif index == 0x2A: debug_print(' <--PRESS_OUT_H')
                elif index == 0x2B: debug_print(' <--TEMP_OUT_L')
                elif index == 0x2C: debug_print(' <--TEMP_OUT_H')
                else: debug_print('')
            index += 1
        return(result)

    def ReadTemp(self):
        debug_print('ReadTemp')
        self.chip_select()
        result = self.__SendBytes(bytearray([self.READ_MASK | self.REG_TEMP_OUT_L] + 2*[self.DUMMY_BYTE]))
        self.chip_release()
        temp_c = (256*float(ord(result[1][2])) + float(ord(result[1][1])))/100
        temp_f = 9*temp_c/5 + 32
        debug_print('temperature in celcius: ' + str(temp_c) + ', temperature in farenheit: ' + str(temp_f))
        return(temp_c)

    def ReadPress(self):
        debug_print('ReadPress')
        self.chip_select()
        result = self.__SendBytes(bytearray([self.READ_MASK | self.REG_PRESS_OUT_XL] + 3*[self.DUMMY_BYTE]))
        self.chip_release()
        press_hPa = (256*256*float(ord(result[1][3])) + 256*float(ord(result[1][2])) + float(ord(result[1][1])))/4096
        press_atm = .000987 * press_hPa
        debug_print('pressure in hPa: ' + str(press_hPa) + ', pressure in atmospheres: ' + str(press_atm))
        return(press_hPa)

    def OneShot(self):
        debug_print('OneShot')
        self.chip_select()
        result = self.__SendBytes(bytearray([self.WRITE_MASK | self.REG_CTRL_REG2]+[0x11]))
        self.chip_release()
        return(result)

    def SWReset(self):
        debug_print('SWReset')
        self.chip_select()
        result = self.__SendBytes(bytearray([self.WRITE_MASK | self.REG_CTRL_REG2]+[0x14]))
        self.chip_release()
        return(result)

    def Boot(self):
        debug_print('Boot')
        self.chip_select()
        result = self.__SendBytes(bytearray([self.WRITE_MASK | self.REG_CTRL_REG2]+[0x90]))
        self.chip_release()
        return(result)
