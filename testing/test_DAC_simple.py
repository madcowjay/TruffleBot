# (very) simple test for DAC - sends a voltage to each channel

from drivers import pydac8532

# set up 16 bit DAC
dac = pydac8532.DAC8532()

# a couple constants/examples
maxVal  = 1*2**16-1
value   = .9 * maxVal
dac.SendDACAValue(0)
dac.SendDACBValue(value)
