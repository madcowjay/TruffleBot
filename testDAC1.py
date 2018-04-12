# (very) simple test for DAC - sends a voltage to each channel

import drivers.pydac8532

# set up 16 bit DAC
dac = drivers.pydac8532.DAC8532()

# a couple constants/examples
maxVal  = 1*2**16-1
value   = .25 * maxVal
dac.SendDACAValue(value)
dac.SendDACBValue(maxVal)
dac.PowerDownDACA()
dac.PowerDownDACB()
