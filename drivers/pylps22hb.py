"""
Driver for SPI interface on LPS22HB pressure Sensor.
February 2018 - Jason Webster
"""

from __future__ import print_function
import time
import wiringpi as wp
import numpy as np

DEBUG = True
def debug_print(string):
    if DEBUG:
        print("DEBUG: " + string)


class LPS22HB:
    """ Wiring Diagram
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

    # These options can be adjusted to facilitate specific operation of the
    # LPS22HB, the defaults are designed to be compatible with the Waveforms
    # High Precision AD/DA board
    SPI_MODE        = 1
    SPI_CHANNEL     = 1
    SPI_FREQUENCY   = 10000000 # The LPS22HB supports 10 MHz
    #DRDY_TIMEOUT    = 0.5 # Seconds to wait for DRDY when communicating
    #DATA_TIMEOUT    = 0.00001 # 10uS delay for sending data

    # The RPI GPIO to use for chip selects and ready polling
    # TODO - change to array
    CS0_PIN     = 33
    CS1_PIN     = 32
    CS2_PIN     = 00 #23 - SPI CLK
    CS3_PIN     = 22
    CS4_PIN     = 35
    CS5_PIN     = 36
    CS6_PIN     = 00 #19 - SPI MOSI
    CS7_PIN     = 18
    #DRDY_PIN    = 11
    #RESET_PIN   = 13
    #PDWN_PIN    = 12

    """
    16 bit commands (typically)
    bit0:     R~W 0 to write to device, 1 to read
    bit 1-7:  Address AD(6:0) MSb first
    bit 8-15: Data DI(7:0) or DO(7:0) MSb first
    """

    # Register addresses
    REG_INTERRUPT_CFG  = 0x0B #R/W Interrupt register
    REG_THIS_P_L       = 0x0C #R/W Pressure threshold register
    REG_THIS_P_H       = 0x0D #R/W Pressure threshold register
    REG_WHO_AM_I       = 0x0F # R  Who am I
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
































    # Commands
    CMD_WAKEUP  = 0x00 # Completes SYNC and exits standby mode
    CMD_RDATA   = 0x01 # Read data
    CMD_RDATAC  = 0x03 # Start read data continuously
    CMD_SDATAC  = 0x0F # Stop read data continuously
    CMD_RREG    = 0x10 # Read from register
    CMD_WREG    = 0x50 # Write to register
    CMD_SELFCAL = 0xF0 # Offset and gain self-calibration
    CMD_SELFOCAL= 0xF1 # Offset self-calibration
    CMD_SELFGCAL= 0xF2 # Gain self-calibration
    CMD_SYSOCAL = 0xF3 # System offset calibration
    CMD_SYSGCAL = 0xF4 # System gain calibration
    CMD_SYNC    = 0xFC # Synchronize the A/D conversion
    CMD_STANDBY = 0xFD # Begin standby mode
    CMD_RESET   = 0xFE # Reset to power-on values

    """
    Status Register Configuration - logically OR all desired options together
    to form a 1 byte command and write it to the STATUS register

    STATUS REGISTER - ADDRESS 0x00
    Bits 7-4 ID3, ID2, ID1, ID0 Factory Programmed Identification Bits
    (Read Only)

    Bit 3 ORDER: Data Output Bit Order

        0 = Most Significant Bit First (default)
        1 = Least Significant Bit First

        Input data is always shifted in most significant byte and bit first.
        Output data is always shifted out most significant byte first. The
        ORDER bit only controls the bit order of the output data within the
        byte.

    Bit 2 ACAL: Auto-Calibration

        0 = Auto-Calibration Disabled (default)
        1 = Auto-Calibration Enabled

        When Auto-Calibration is enabled, self-calibration begins at the
        completion of the WREG command that changes the PGA (bits 0-2 of ADCON
        register), DR (bits 7-0 in the DRATE register) or BUFEN (bit 1 in the
        STATUS register) values.

    Bit 1 BUFEN: Analog Input Buffer Enable

        0 = Buffer Disabled (default)
        1 = Buffer Enabled

    Bit 0 DRDY: Data Ready (Read Only)

        This bit duplicates the state of the DRDY pin, which is inverted logic.
    """
    STATUS_BUFFER_ENABLE    = 0x02
    STATUS_AUTOCAL_ENABLE   = 0x04
    STATUS_ORDER_LSB        = 0x08


    """
    A/D Control Register - Address 0x02

    Bit 7 Reserved, always 0 (Read Only)

    Bits 6-5 CLK1, CLK0: D0/CLKOUT Clock Out Rate Setting

        00 = Clock Out OFF
    01 = Clock Out Frequency = fCLKIN (default)
    10 = Clock Out Frequency = fCLKIN/2
    11 = Clock Out Frequency = fCLKIN/4

    When not using CLKOUT, it is recommended that it be turned off. These
    bits can only be reset using the RESET pin.

    Bits 4-3 SDCS1, SCDS0: Sensor Detect Current Sources

    00 = Sensor Detect OFF (default)
    01 = Sensor Detect Current = 0.5uA
    10 = Sensor Detect Current = 2uA
    11 = Sensor Detect Current = 10uA

    The Sensor Detect Current Sources can be activated to verify the
    integrity of an external sensor supplying a signal to the ADS1255/6.
    A shorted sensor produces a very small signal while an open-circuit
    sensor produces a very large signal.

    Bits 2-0 PGA2, PGA1, PGA0: Programmable Gain Amplifier Setting
        000 = 1 (default)
        001 = 2
        010 = 4
        011 = 8
        100 = 16
        101 = 32
        110 = 64
        111 = 64
    """
    # Gain levels
    AD_GAIN_1      = 0x00
    AD_GAIN_2      = 0x01
    AD_GAIN_4      = 0x02
    AD_GAIN_8      = 0x03
    AD_GAIN_16     = 0x04
    AD_GAIN_32     = 0x05
    AD_GAIN_64     = 0x06

    # Sensor Detect Current Sources
    AD_SDCS_500pA   = 0x08
    AD_SDCS_2uA     = 0x10
    AD_SDCS_10uA    = 0x18

    # Clock divider
    AD_CLK_EQUAL    = 0x20
    AD_CLK_HALF     = 0x40
    AD_CLK_FOURTH   = 0x60

    # Mux channel selection
    MUX_AIN0 = 0x0
    MUX_AIN1 = 0x1
    MUX_AIN2 = 0x2
    MUX_AIN3 = 0x3
    MUX_AIN4 = 0x4
    MUX_AIN5 = 0x5
    MUX_AIN6 = 0x6
    MUX_AIN7 = 0x7
    MUX_AINCOM = 0x8


    # The RPI GPIO to use for chip select and ready polling
    def __init__(self):
        debug_print('pydads1256 initializing with:')
        debug_print('   SPI_MODE      = %d' % self.SPI_MODE)
        debug_print('   SPI_CHANNEL   = %d' % self.SPI_CHANNEL)
        debug_print('   SPI_FREQUENCY = ' + format(self.SPI_FREQUENCY,','))
        debug_print('   CS_PIN    = %d' %self.CS_PIN)
        debug_print('   DRDY_PIN  = %d' %self.DRDY_PIN)
        debug_print('   RESET_PIN = %d' %self.RESET_PIN)
        debug_print('   PDWN_PIN  = %d' %self.PDWN_PIN)
        # Set up the wiringpi object to use physical pin numbers
        wp.wiringPiSetupPhys()

        # Initialize the DRDY pin
        wp.pinMode(self.DRDY_PIN, wp.INPUT)

        # Initialize the reset pin
        wp.pinMode(self.RESET_PIN, wp.OUTPUT)
        wp.digitalWrite(self.RESET_PIN, wp.HIGH)

        # Initialize PDWN pin
        wp.pinMode(self.PDWN_PIN, wp.OUTPUT)
        wp.digitalWrite(self.PDWN_PIN, wp.HIGH)

        # Initialize CS pin
        wp.pinMode(self.CS_PIN, wp.OUTPUT)
        wp.digitalWrite(self.CS_PIN, wp.HIGH)

        # Initialize the wiringpi SPI setup
        #spi_success = wp.wiringPiSPISetup(self.SPI_CHANNEL, self.SPI_FREQUENCY)
        spi_success = wp.wiringPiSPISetupMode(self.SPI_CHANNEL, self.SPI_FREQUENCY, self.SPI_MODE)  #JKR
        debug_print("SPI success " + str(spi_success))

    def delayMicroseconds(self, delayus):
        wp.delayMicroseconds(delayus)

    def chip_select(self):
        wp.digitalWrite(self.CS_PIN, wp.LOW)

    def chip_release(self):
        wp.digitalWrite(self.CS_PIN, wp.HIGH)

    def WaitDRDY(self):
        """
        Delays until DRDY line goes low, allowing for automatic calibration
        """
        start = time.time()
        elapsed = time.time() - start

        # Waits for DRDY to go to zero or TIMEOUT seconds to pass
        drdy_level = wp.digitalRead(self.DRDY_PIN)
        while (drdy_level == wp.HIGH) and (elapsed < self.DRDY_TIMEOUT):
            elapsed = time.time() - start
            drdy_level = wp.digitalRead(self.DRDY_PIN)

        if elapsed >= self.DRDY_TIMEOUT:
            print("WaitDRDY() Timeout\r\n")

    def SendString(self, mystring):
        debug_print("  Entered SendString: " + mystring)
        result = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, mystring)
        debug_print("    SendString read: " + str(result[1]))



    def SendByte(self, mybyte):
        """
        Sends a byte to the SPI bus
        """
        debug_print("  Entered SendByte")
        #debug_print("    Sending: " + str(mybyte) + " (hex " + hex(mybyte) + ")")
        if DEBUG:
        	print('DEBUG:     Sending: ', end='')
        	print(str(mybyte).rjust(3), end='')
        	print(' (hex \\x%02x)' % (mybyte))
        mydata = chr(mybyte)
        print(mybyte)
        print(type(mybyte))
        print(mydata)
        print(type((mydata)))
        print('try: %s' % mydata)
        print('success')
        result = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, "%s" % mydata)   # notice workaround for single byte transfers JKR
        #debug_print("    Read " + str(result[1]))
        debug_print('    Received:    ' + str(result))

    def ReadByte(self):
        """
        Reads a byte from the SPI bus
        :returns: byte read from the bus
        """
        MISObyte = wp.wiringPiSPIDataRW(self.SPI_CHANNEL, chr(0xFF))
        return ord(MISObyte[1]) #JKR

    def DataDelay(self):
        """
        Delay from last SCLK edge to first SCLK rising edge

        Master clock rate is typically 7.68MHz, this is adjustable through the
        SCLK_FREQUENCY variable

        Datasheet states that the delay between requesting data and reading the
        bus must be minimum 50x SCLK period, this function reads data after
        60 x SCLK period.
        """
        timeout = (60 / self.SCLK_FREQUENCY)


        start = time.time()
        elapsed = time.time() - start

        # Wait for TIMEOUT to elapse
        while elapsed < self.DATA_TIMEOUT:
            elapsed = time.time() - start


    def ReadReg(self, start_reg, num_to_read):
        debug_print(" Entered ReadReg")
        """"
        Read the provided register, implements:

        RREG: Read from Registers

        Description: Output the data from up to 11 registers starting with the
        register address specified as part of the command. The number of
        registers read will be one plus the second byte of the command. If the
        count exceeds the remaining registers, the addresses will wrap back to
        the beginning.

        1st Command Byte: 0001 rrrr where rrrr is the address of the first
        register to read.

        2nd Command Byte: 0000 nnnn where nnnn is the number of bytes to read
        1. See the Timing Characteristics for the required delay between the
        end of the RREG command and the beginning of shifting data on DOUT: t6.
        """

        result = []

        # Pull the SPI bus low
        self.chip_select()

        # Send the byte command
        self.SendByte(self.CMD_RREG | start_reg)
        self.SendByte(0x00)

        # Wait for appropriate data delay
        self.DataDelay()

        # Read the register contents
        read = self.ReadByte()
        temp = (str(read))
        debug_print('  Read from register: ' + temp)

        # Release the SPI bus
        self.chip_release()

        return read

    def WriteReg(self, start_register, data):
        """
        Writes data to the register, implements:

        WREG: Write to Register

        Description: Write to the registers starting with the register
        specified as part of the command. The number of registers that
        will be written is one plus the value of the second byte in the
        command.

        1st Command Byte: 0101 rrrr where rrrr is the address to the first
        register to be written.

        2nd Command Byte: 0000 nnnn where nnnn is the number of bytes-1 to be
        written

        TODO: Implement multiple register write
        """

        # Select the ADS chip
        self.chip_select()

        # Tell the ADS chip which register to start writing at
        self.SendByte(self.CMD_WREG | start_register)

        # Tell the ADS chip how many additional registers to write
        self.SendByte(0x00)

        # Send the data
        self.SendByte(data)

        # Release the ADS chip
        self.chip_release()


    def ConfigADC(self):

        debug_print("configuring ADC")

        self.chip_select()

        self.SendByte(self.CMD_WREG | 0x00)  # start write at addr 0x00

        self.SendByte(self.REG_DRATE)  # end write at addr REG_DRATE

        self.SendByte(self.STATUS_AUTOCAL_ENABLE)   # status register
        self.SendByte(0x08)                         # input channel parameters
        self.SendByte(self.AD_GAIN_2)               # ADCON control register, gain
        self.SendByte(self.DRATE_500)               # data rate

        self.chip_release()

        self.DataDelay()


    def SetInputMux(self,possel,negsel):
        debug_print("setting mux position")

        self.chip_select()
        self.SendByte(self.CMD_WREG | 0x01)
        self.SendByte(0x00)
        self.SendByte( (possel<<4) | (negsel<<0) )
        self.chip_release()

    def SetInputMux_quick(self,possel,negsel):
        debug_print("setting mux position")

        # self.chip_select()
        self.SendByte(self.CMD_WREG | 0x01)
        self.SendByte(0x00)
        self.SendByte( (possel<<4) | (negsel<<0) )
        # self.chip_release()

    def SyncAndWakeup(self):
        debug_print("sync+wakeup")

        self.chip_select()
        self.SendByte(self.CMD_SYNC)
        self.chip_release()
        self.delayMicroseconds(10)

        self.chip_select()
        self.SendByte(self.CMD_WAKEUP)
        self.chip_release()
        self.delayMicroseconds(10)

    def SyncAndWakeup_quick(self):
        debug_print("sync+wakeup")

        # self.chip_select()
        self.SendByte(self.CMD_SYNC)
        self.chip_release()
        self.delayMicroseconds(10)

        self.chip_select()
        self.SendByte(self.CMD_WAKEUP)
        self.chip_release()
        # self.delayMicroseconds(10)


    def SetGPIOoutputs(self,D0,D1,D2,D3):
        debug_print("set GPIO outputs")

        IObits = D3*0x8 + D2*0x4 + D1*0x2 + D0*0x1

        self.WriteReg(self.REG_IO,IObits)


    def ReadADC(self):
        """
        Reads ADC data, implements:

        RDATA: Read Data

        Description: Issue this command after DRDY goes low to read a single
        conversion result. After all 24 bits have been shifted out on DOUT,
        DRDY goes high. It is not necessary to read back all 24 bits, but DRDY
        will then not return high until new data is being updated. See the
        Timing Characteristics for the required delay between the end of the
        RDATA command and the beginning of shifting data on DOUT: t6
        """

        # Pull the SPI bus low
        self.chip_select()

        # Wait for data to be ready
        self.WaitDRDY()

        # Send the read command
        self.SendByte(self.CMD_RDATA)

        # Wait through the data pause
        self.DataDelay()

        # The result is 24 bits
        #result.append(self.ReadByte())
        result1 = self.ReadByte()
        result2 = self.ReadByte()
        result3 = self.ReadByte()
        debug_print('ReadADC result bytes: ' + hex(result1) + ' ' + hex(result2) + ' ' + hex(result3))

        # Release the SPI bus
        self.chip_release()

        # Concatenate the bytes
        total  = (result1 << 16) + (result2 << 8) + result3

        return total

    def ReadADC_quick(self):
        """
        Reads ADC data, implements:

        RDATA: Read Data

        Description: Issue this command after DRDY goes low to read a single
        conversion result. After all 24 bits have been shifted out on DOUT,
        DRDY goes high. It is not necessary to read back all 24 bits, but DRDY
        will then not return high until new data is being updated. See the
        Timing Characteristics for the required delay between the end of the
        RDATA command and the beginning of shifting data on DOUT: t6
        """

        # Pull the SPI bus low
        # self.chip_select()

        # Wait for data to be ready
        # self.WaitDRDY()

        # Send the read command
        self.SendByte(self.CMD_RDATA)

        # Wait through the data pause
        self.DataDelay()

        # The result is 24 bits
        #result.append(self.ReadByte())
        result1 = self.ReadByte()
        result2 = self.ReadByte()
        result3 = self.ReadByte()
        debug_print('ReadADC result bytes: ' + hex(result1) + ' ' + hex(result2) + ' ' + hex(result3))

        # Release the SPI bus
        # self.chip_release()

        # Concatenate the bytes
        total  = (result1 << 16) + (result2 << 8) + result3

        return total

    def CycleReadADC(self,sel_list):
        c=0 # init counter var
        data = np.zeros(len(sel_list),dtype='i32') #create an array to hold the sample vars
        self.chip_select()

        self.SetInputMux_quick(sel_list[c][0],sel_list[c][1]) #select the first entry in list

        for i in range(len(sel_list)):
            c+=1 #update the counter
            self.WaitDRDY() #wait for the drdy to go low
            try:
                self.SetInputMux_quick(sel_list[c][0],sel_list[c][1]) #set the mux to the next sample
            except:
                pass #this should catch the last sample where we have no data to set the mux as, but still need to read the last piece
            time.sleep(command_delay)
            self.SyncAndWakeup_quick()
            time.sleep(command_delay)
            data[c-1] = self.ReadADC_quick()
        self.chip_release()
        return data

    def getADCsample(self,a_pos,a_neg):
        """
        Gets a sample from the ADC
        NOTE: this is configured to switch devices that all use the common ground
        """
        debug_print('getADCSample')
        self.SetInputMux(a_pos,a_neg)
        self.SyncAndWakeup()
        myconversion = int(self.ReadADC())
        return myconversion

    def ReadID(self):
        """
        Read the ID from the ADS chip
        :returns: numeric identifier of the ADS chip
        """
        debug_print("ReadID")
        self.WaitDRDY()
        myid = self.ReadReg(self.REG_STATUS, 1)
        debug_print(" readID: myid = " + str(myid>>4))
        return (myid >> 4)
