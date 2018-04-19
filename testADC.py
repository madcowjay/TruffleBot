import drivers.pyads1256
import drivers.pylps22hb
import time
import wiringpi as wp
import numpy as np

wp.wiringPiSetupPhys
wp.pinMode(26, wp.INPUT)

all_cs = [33, 32, 40, 22, 35, 36, 7, 18]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)

# setup ADC
ads = drivers.pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
print('my id is:' + str(myid))
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

ref_voltage = 2.5
gain = 2

ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
ads.SyncAndWakeup()

def read(n):
	while n:
		result_in_twos_comp = ads.ReadADC()
		result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
		voltage = (result*2*ref_voltage) / (2**23 - 1) / gain
		res = float(result_in_twos_comp)
		perc = np.mod(res-2**23,2**24)/2**24
		print('Voltage: %.9f, percent of range: %.9f' %(voltage, perc))
		n -= 1
