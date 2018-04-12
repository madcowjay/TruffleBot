import drivers.pyads1256
import time

# setup ADC
ads = drivers.pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
print('my id is:' + str(myid))
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

ref_voltage = 2.5

# sample ADC
ads.SetInputMux(ads.MUX_AIN2,ads.MUX_AINCOM)
ads.SyncAndWakeup()
while True:
	result_in_twos_comp = (ads.ReadADC())
	result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
	voltage = (result*2*ref_voltage) / (2**23 - 1)
	print('Result_in_twos_comp: %x, Result in decimal: %d, Voltage: %.5f' %(result_in_twos_comp, result, voltage))
	time.sleep(.2)
