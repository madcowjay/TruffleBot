import serial
import time

class pulser():
    def __init__(self,
                 channel=1,
                 port="/dev/ttyACM0", # Ras-Pi
                 #port = '/dev/tty.usbmodem621', # MacBook
                 baudrate=9600,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE):
        self.channel=channel
        self.port=port
        self.baudrate=baudrate
        self.parity=parity
        self.stopbits=stopbits
        #Open communication port if not already open

    def openPort(self):
        try:
            self.ser = serial.Serial(port=self.port,
                                     baudrate=self.baudrate,
                                     parity=self.parity,
                                     stopbits=self.stopbits)
            print("Connected to Serial Port address : " + self.port)
        except:
            print("Serial port " + self.port + " not found.")
            pass


    def setVoltage(self,V):
        command = "VSET{channel}:{volt:.2f}"
        V = float(V)
        command = command.format(channel=1, volt=V)
        self.ser.write(command.encode('utf-8'))

    def setCurrent(self,I):
        command = "ISET{channel}:{current:.2f}"
        I = float(I)
        command = command.format(channel=1, current=I)
        self.ser.write(command.encode('utf-8'))

    def setIV(self,V,I):
        self.setVoltage(V)
        time.sleep(0.2)
        self.setCurrent(I)

    def setOutput(self,out):
        if out=="ON":
            self.ser.write("OUT1".encode('utf-8'))
        else:
            self.ser.write("OUT0".encode('utf-8'))

    def closePort(self):
        self.ser.close()
        print("Serial port closed.")
