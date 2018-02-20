# (very) simple test for DAC - sends a voltage to each channel

import pydac8532

# set up 16 bit DAC
dac = pydac8532.DAC8532()

# a couple constants/examples
# essentially you're sending
zero    = 0
maxVal  = 1*2**16-1
halfVal = 1*2**8       //explicit declaration
value   = .75 * maxVal //derived declaration

dac.SendDACAValue(zero)
dac.SendDACBValue(maxVal)
