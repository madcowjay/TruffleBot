import pydac8532

dac = pydac8532.DAC8532()

dac.SendDACAValue(.5*2**16)
dac.SendDACBValue(.9*2**16)


