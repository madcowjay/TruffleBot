import pyads1256
import time

# setup ADC
ads = pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

ref_voltage = 4.49

# sample ADC
ads.SetInputMux(ads.MUX_AIN0,ads.MUX_AINCOM)  # these two values can be any two ADC Inputs
ads.SyncAndWakeup()
while True:
	result = (ads.ReadADC())
	percentage = float(result)/(2**24)
	voltage = percentage*2*ref_voltage-ref_voltage
	print('Result: %d, Percentage: %.2f, Voltage: %.5f' %(result, percentage, voltage))
	time.sleep(.2)