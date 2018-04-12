import drivers.pydac8532
import drivers.pyads1256
import time
import numpy as np

# set up DAC
dac = drivers.pydac8532.DAC8532()
DAC_ref_voltage = 3.269
DAC_set_voltage = 1.4 #recommended on datasheet

# setup ADC
ads = drivers.pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()
ADC_ref_voltage = 4.49

# heat up heater
dac.SendDACAValue((DAC_set_voltage/DAC_ref_voltage)*2**16)
time.sleep(0.04) #adc interval
print("Sampling...")
sam_1 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN1)
sam_2 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN2)
sam_3 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN5)
sam_4 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN6)
sam_5 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN0)
sam_6 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN3)
sam_7 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN4)
sam_8 = ads.getADCsample(ads.MUX_AINCOM,ads.MUX_AIN7)
print("Sampled all")

sample = np.array([sam_1,sam_2,sam_3,sam_4,sam_5,sam_6,sam_7,sam_8], dtype='i32')
for c in sample:
	print c
	percentage = float(c)/(2**24)
	voltage = percentage*2*ADC_ref_voltage
	print('Result: %d, Percentage: %.2f, Voltage: %.5f' %(c, percentage, voltage))
#dac.PowerDownDACA()
