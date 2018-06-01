import os, time, threading, sys, configparser
from   colorama import init, Fore, Back, Style
import wiringpi as wp
import numpy    as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from   lib.getch import *
from   optparse  import OptionParser
import lib.pylps22hb
import lib.pyads1256

LPS_SPI_CHANNEL   = 0
LPS_SPI_FREQUENCY = 10000000
PRESS0_PIN    = 33
PRESS1_PIN    = 32
PRESS2_PIN    = 40
PRESS3_PIN    = 22
PRESS4_PIN    = 35
PRESS5_PIN    = 36
PRESS6_PIN    =  7
PRESS7_PIN    = 18
ADC_CS_PIN    = 15
ADC_DRDY_PIN  = 11
ADC_RESET_PIN = 13
ADC_PDWN_PIN  = 12
ADC_SPI_CHANNEL   = 0
ADC_SPI_FREQUENCY = 1000000

ads = lib.pyads1256.ADS1256()
ads.ConfigADC()
ads.SyncAndWakeup()
adc_ref_voltage = 2.5
adc_gain = 2

#all_cs = [PRESS0_PIN, PRESS1_PIN, PRESS2_PIN, PRESS3_PIN, PRESS4_PIN, PRESS5_PIN, PRESS6_PIN, PRESS7_PIN]
all_cs = [PRESS0_PIN]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)
lps = []
for index in range(len(all_cs)):
	lps.append(lib.pylps22hb.LPS22HB(LPS_SPI_CHANNEL, LPS_SPI_FREQUENCY, all_cs[index]))
	time.sleep(.05)
	lps[index].Boot() # wake up the sensors

frequency          = 60
sample_count       = 1000
include_MOX        = 1
include_press_temp = 1
period             = 1/frequency
channels           = 8

sel_list = [[ads.MUX_AIN1, ads.MUX_AINCOM], [ads.MUX_AIN2, ads.MUX_AINCOM],
			[ads.MUX_AIN5, ads.MUX_AINCOM], [ads.MUX_AIN6, ads.MUX_AINCOM],
			[ads.MUX_AIN0, ads.MUX_AINCOM], [ads.MUX_AIN3, ads.MUX_AINCOM],
			[ads.MUX_AIN4, ads.MUX_AINCOM], [ads.MUX_AIN7, ads.MUX_AINCOM]]

# init array to store data
mox_data   = np.zeros([sample_count, channels], dtype='int32')
temp_data  = np.zeros([sample_count, channels], dtype='float32')
press_data = np.zeros([sample_count, channels], dtype='float32')
rx_time_log = np.zeros([sample_count], dtype='float32')

trial_start_time = time.time()

for i in range(sample_count):
	sample_start_time = time.time()
	rx_time_log[i] = (sample_start_time - trial_start_time)
	# collect samples from feach sensor on board
	if include_MOX:
		# sam_1 = ads.getADCsample(ads.MUX_AIN1, ads.MUX_AINCOM)
		# sam_2 = ads.getADCsample(ads.MUX_AIN2, ads.MUX_AINCOM)
		# sam_3 = ads.getADCsample(ads.MUX_AIN5, ads.MUX_AINCOM)
		# sam_4 = ads.getADCsample(ads.MUX_AIN6, ads.MUX_AINCOM)
		# sam_5 = ads.getADCsample(ads.MUX_AIN0, ads.MUX_AINCOM)
		# sam_6 = ads.getADCsample(ads.MUX_AIN3, ads.MUX_AINCOM)
		# sam_7 = ads.getADCsample(ads.MUX_AIN4, ads.MUX_AINCOM)
		# sam_8 = ads.getADCsample(ads.MUX_AIN7, ads.MUX_AINCOM)
		#
		# mox_data[i] = np.array([sam_1,sam_2,sam_3,sam_4,sam_5,sam_6,sam_7,sam_8], dtype='int32')

		ads.ChipSelect()
		samps = ads.CycleReadADC_quick(sel_list)
		mox_data[i] = np.array(samps, dtype='int32')

	if include_press_temp:
		for index in range(len(lps)):
			press_data[i][index], temp_data[i][index]  = lps[index].ReadPressAndTemp()

	while time.time() - trial_start_time < (i+1)*period:
		pass
trial_end_time = time.time()

duration = trial_end_time - trial_start_time
print('Desired Sample Rate:    {}'.format(frequency))
print('Elapsed Time:           {} s'.format(duration))
print('Effective Sample Rate:  {} Hz'.format(sample_count / duration))
