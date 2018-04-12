# (very) simple test for LPS - sends a voltage to each channel
import time
import wiringpi as wp
import os

import drivers.pylps22hb
import drivers.pyads1256 #need to make sure it's CS is HIGH

ads = drivers.pyads1256.ADS1256()

wp.wiringPiSetupPhys

#need to set pin 26 as input, because it's tied to MISO on the TruffleBot
wp.pinMode(26, wp.INPUT)

#set all CS pins high for the pressure sensors, let the initializer reverse that if used.
all_cs = [33, 32, 40, 22, 35, 36, 7, 18]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)

#my_cs = [33, 32, 40, 22, 35, 36, 7, 18]
#my_cs = [32, 18] #TruffleBot2
#my_cs = [33, 22, 18] #TruffleBot1
my_cs = all_cs

ads.chip_select()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

ref_voltage = 4.5

lps = []
for i in range(len(my_cs)):
    lps.append(drivers.pylps22hb.LPS22HB(my_cs[i]))
    print('Press' + str(i) + ' id:      ' + lps[i].ReadID()),
    #lps[i].ReadRegisters()
    #lps[i].OneShot()
    #time.sleep(.1)
    #lps[i].ReadRegisters()
    #print('\ttemperature is: ' + str(lps[i].ReadTemp())),
    #print('\tpressure is:    ' + str(lps[i].ReadPress()))

#sample ADC
# for j in [ads.MUX_AIN0, ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN7]:
#     ads.SetInputMux(j,ads.MUX_AINCOM)
#     ads.SyncAndWakeup()
#     print(j)
#     for i in range(0,1):
#     	result = (ads.ReadADC())
#     	percentage = float(result)/(2**24)
#     	voltage = percentage*2*ref_voltage-ref_voltage
#     	print('Result: %d, Percentage: %.2f, Voltage: %.5f' %(result, percentage, voltage))
#     	time.sleep(.2)
