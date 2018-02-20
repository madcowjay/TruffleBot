import pydac8532
import pyads1256
import time

# set up DAC
dac = pydac8532.DAC8532()
DAC_ref_voltage = 3.269
DAC_set_voltage = 0

# setup ADC
ads = pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()
ADC_ref_voltage = 4.49

# sample ADC and output to DAC
ads.SetInputMux(ads.MUX_AIN0,ads.MUX_AINCOM)
ads.SyncAndWakeup()
while True:
	result = (ads.ReadADC())
	percentage = float(result)/(2**24)
	voltage = percentage*2*ADC_ref_voltage-ADC_ref_voltage
	print('Result: %d, Percentage: %.2f, Voltage: %.5f' %(result, percentage, voltage))
	dac.SendDACBValue(percentage*2**16)