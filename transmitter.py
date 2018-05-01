# This is an example transmitter code
import TB_pulser
import time
import numpy as np

p=TB_pulser.pulser() # get pulser insatnce
p.openPort() #Open communication port

# transmitted code
num_bits=15 # number of bits to generate
message=np.random.randint(0,2,num_bits)

# set initial parameters
p.setVoltage(12) #sets voltage and current to 0V and 1A
time.sleep(0.1)
p.setCurrent(1)
p.setOutput("ON")
time.sleep(0.1)
# transmit messages
for i in range(len(message)):
    print("Bit ",message[i])
    p.setVoltage(message[i]*12) # sets voltage to bits*12V
                                # motor needs 12V, 1A to operate
    time.sleep(2)

p.setOutput("OFF")
print("Transfer completed")
