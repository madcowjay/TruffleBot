# This is an example transmitter code
import lib.TB_pulser
import time
import numpy as np

p = lib.TB_pulser.pulser() # get pulser instance
p.openPort() #Open communication port

# transmitted code
#num_bits=15 # number of bits to generate
#message=np.random.randint(0,2,num_bits)
message=np.array([1, 0, 1, 0, 0])
message=np.tile(message,2)
# set initial parameters
p.setVoltage(0) #sets voltage and current to 0V and 1A
p.setCurrent(1)
p.setOutput("ON")
# transmit messages
for i in range(len(message)):
	print("Bit " + str(message[i]))
	p.setVoltage(message[i]*5) # sets voltage to bits*12V
								# motor needs 12V, 1A to operate
	time.sleep(2)

p.setOutput("OFF")
p.closePort()
print("Transfer completed")
