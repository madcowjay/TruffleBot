import drivers.pydac8532

dac = pydac8532.DAC8532()

ref_voltage = 3.269

set_voltage = 0
while set_voltage >= 0:
	set_voltage = input('Enter new DC value:')
	to_send = (set_voltage/ref_voltage)*2**16
	if to_send >= 2**16:
		to_send = 2**16-1
	dac.SendDACBValue(to_send)

dac.PowerDownDACB()
