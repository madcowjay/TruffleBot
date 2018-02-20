import pydac8532

dac = pydac8532.DAC8532()

dac.SendDACAValue(0*2**16)
dac.SendDACBValue((1*2**16)-1)


