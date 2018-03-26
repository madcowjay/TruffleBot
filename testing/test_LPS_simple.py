# (very) simple test for LPS - sends a voltage to each channel
import time
import wiringpi as wp
import os

os.environ["blah"] = "True"

from drivers import pylps22hb
from drivers import pyads1256 #need to make sure it's CS is HIGH


#my_cs = [33, 32, 40, 22, 35, 36, 7, 18]
#my_cs = [32, 18] #TruffleBot2
#my_cs = [33, 22, 18] #TruffleBot1
my_cs = [33]
ads = pyads1256.ADS1256()

wp.pinMode(26, wp.INPUT)

ads.chip_select()
myid = ads.ReadID()
print('my id is:' + str(myid))
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

ref_voltage = 4.5

lps = []
for i in range(len(my_cs)):
    lps.append(pylps22hb.LPS22HB(my_cs[i]))
    #print('Press' + str(i) + ' id:      ' + lps[i].ReadID())
    lps[i].ReadRegisters()
    lps[i].Boot()
    lps[i].ReadRegisters()
    #print(lps[i].OneShot())
    # lps[i].ReadRegisters()

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
