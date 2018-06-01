# generic imports
import os, time, threading, sys, configparser
from   colorama import init, Fore, Back, Style
import wiringpi as wp
import numpy    as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from   lib.getch import *
from   optparse import OptionParser

# console colors
init() #colorama
bg  = Back.GREEN; br  = Back.RED; bb  = Back.BLUE; by  = Back.YELLOW; bc  = Back.CYAN; bm  = Back.MAGENTA
fg  = Fore.GREEN; fr  = Fore.RED; fb  = Fore.BLUE; fy  = Fore.YELLOW; fc  = Fore.CYAN; fm  = Fore.MAGENTA
fbk = Fore.BLACK; fw  = Fore.WHITE
sr  = Style.RESET_ALL

# Process command line arguments
usage = 'python3 test.py [OPTION]...'
parser = OptionParser(usage)
parser.add_option('-d','--debug',action='store_true',dest='debugFlag',help='display debug messages while running',default=False)
parser.add_option('-c','--config-file',dest='configfile',help='use the indicated configuration file, if not invoked, default.cfg is used',default='default.cfg')
(options, args) = parser.parse_args()
configFilePath = options.configfile
if options.debugFlag: os.environ['DEBUG'] = 'True'

# Load these after DEBUG status has been determined
import lib.pyads1256
import lib.pydac8532
import lib.pylps22hb
import lib.sensor_board

config = configparser.RawConfigParser()
config.read(configFilePath)
print('\nLoading config file: ' + configFilePath)

LED1_PIN = int(config.get('GPIO', 'LED1_PIN'))
LED2_PIN = int(config.get('GPIO', 'LED2_PIN'))
TX0_PIN  = int(config.get('GPIO', 'TX0_PIN'))
TX1_PIN  = int(config.get('GPIO', 'TX1_PIN'))
PRESS0_PIN = int(config.get('GPIO', 'PRESS0_PIN'))
PRESS1_PIN = int(config.get('GPIO', 'PRESS1_PIN'))
PRESS2_PIN = int(config.get('GPIO', 'PRESS2_PIN'))
PRESS3_PIN = int(config.get('GPIO', 'PRESS3_PIN'))
PRESS4_PIN = int(config.get('GPIO', 'PRESS4_PIN'))
PRESS5_PIN = int(config.get('GPIO', 'PRESS5_PIN'))
PRESS6_PIN = int(config.get('GPIO', 'PRESS6_PIN'))
PRESS7_PIN = int(config.get('GPIO', 'PRESS7_PIN'))
DAC_CS_PIN = int(config.get('GPIO', 'DAC_CS_PIN'))
ADC_CS_PIN    = int(config.get('GPIO', 'ADC_CS_PIN'))
ADC_DRDY_PIN  = int(config.get('GPIO', 'ADC_DRDY_PIN'))
ADC_RESET_PIN = int(config.get('GPIO', 'ADC_RESET_PIN'))
ADC_PDWN_PIN  = int(config.get('GPIO', 'ADC_PDWN_PIN'))

DAC_SPI_CHANNEL   = int(config.get('DAC', 'DAC_SPI_CHANNEL'))
DAC_SPI_FREQUENCY = int(config.get('DAC', 'DAC_SPI_FREQUENCY'))

LPS_SPI_CHANNEL   = int(config.get('LPS', 'LPS_SPI_CHANNEL'))
LPS_SPI_FREQUENCY = int(config.get('LPS', 'LPS_SPI_FREQUENCY'))

# set up board
board = lib.sensor_board.SENSOR_BOARD(LED1_PIN, LED2_PIN, TX0_PIN, TX1_PIN)
wp.wiringPiSetupPhys
wp.pinMode(26, wp.INPUT) #I actually snipped this pin off the header, but in case you don't...
led1_freq = 1 #Hz
led2_freq = 1 #Hz

# set up pressure sensors - if you don't use all of them, you should still set all
#    of the pins as output and high
all_cs = [PRESS0_PIN, PRESS1_PIN, PRESS2_PIN, PRESS3_PIN, PRESS4_PIN, PRESS5_PIN, PRESS6_PIN, PRESS7_PIN]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)
lps = []
lps_status = []
for index in range(len(all_cs)):
	lps.append(lib.pylps22hb.LPS22HB(LPS_SPI_CHANNEL, LPS_SPI_FREQUENCY, all_cs[index]))
	lps[index].OneShot()
	if lps[index].ReadID() == '0xb1':
		lps_status.append(fg+' LPS' + str(index) + ' UP ' +sr)
	else:
		lps_status.append(fr+'LPS' + str(index) + ' DOWN' +sr)
lps_rate = 2 # Hz
lps_mode = 0 # 0 = temperature and pressure, 1 = registers

# set up ADC
ads = lib.pyads1256.ADS1256()
if ads.ReadID()==3:
	adc_status = fg+' ADC UP '+sr
else: adc_status = fr+'ADC DOWN'+sr
ads.ConfigADC()
ads.SyncAndWakeup()
adc_ref_voltage = 2.5
adc_gain = 2
adc_rate = 2 # Hz
adc_mode = 0 # 0 = voltage, 1 = percent of range

# set up 16 bit DAC
dac = lib.pydac8532.DAC8532(DAC_SPI_CHANNEL, DAC_SPI_FREQUENCY, DAC_CS_PIN)
dac_ref_voltage = 3.3
dac_max_val  = 1*2**16-1
dac.SendDACAValue(0)
dac.SendDACBValue(0)
daca = 0
dacb = 0

# Function to get keyboard interrupts (cross-platform)
def input_thread(stop_event):
	getch()
	stop_event.set()

# Helper function to read ADC: handles discrete vs. continuous
def read_adc(n, channels):
	print(sr)
	if n == 'c':
		print('press any key to stop')
		voltages = []
		percents = []
		twos_comps = []
		t_stop = threading.Event()
		t = threading.Thread(target=input_thread, args=(t_stop,))
		t.start()
		while not ( t_stop.is_set() ):
			voltage, percent, twos_comp = read_adc_once(channels)
			voltages.append(voltage)
			percents.append(percent)
			twos_comps.append(twos_comp)
			global adc_rate
			time.sleep(1/adc_rate)
		if len(channels)  == 1:
			print('\nignoring first data point...')
			voltages = voltages[1:]; percents = percents[1:]; twos_comps = twos_comps[1:]
			print('average values were: {:>22} V   {:>20} %   {} raw'.format(sum(voltages)/len(voltages), sum(percents)/len(percents), sum(twos_comps)/len(twos_comps)))
			print('   high values were: {:>22} V   {:>20} %   {} raw'.format(max(voltages), max(percents), max(twos_comps)))
			print('    low values were: {:.22} V   {:>20} %   {} raw'.format(min(voltages), min(percents), min(twos_comps)))
			plt.plot(voltages);   plt.savefig('log/voltages');   plt.close()
			plt.plot(percents);   plt.savefig('log/percents');   plt.close()
			plt.plot(twos_comps); plt.savefig('log/twos_comps'); plt.close()
			print('saved plots to log directory')
	else:
		try:
			j = int(n)
			while j:
				read_adc_once(channels)
				j -= 1
		except ValueError:
			print('Please enter a valid selection')

# Read the ADC and display the results
def read_adc_once(channels):
	if len(channels) == 1:
		result_in_twos_comp = ads.getADCsample(channels[0], ads.MUX_AINCOM)
		result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
		voltage = (result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain
		res = float(result_in_twos_comp)
		perc = np.mod(res-2**23,2**24)/2**24
		print('Voltage: {:>22} percent of range: {:>20}'.format(voltage, perc))
		return voltage, perc, result_in_twos_comp
	else:
		voltages = []
		for channel in channels:
			result_in_twos_comp = ads.getADCsample(channel, ads.MUX_AINCOM)
			result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
			voltages.append((result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain)
		for v in voltages:
			print('  {0:+0.9f} V'.format(v), end='')
		print('')
		return 0, 0, 0

# Helper function to read LPS: handles discrete vs. continuous
def read_lps(n, channels):
	print(sr)
	if n == 'c':
		t_stop = threading.Event()
		t = threading.Thread(target=input_thread, args=(t_stop,))
		t.start()
		while not ( t_stop.is_set() ):
			read_lps_once(channels)
			global lps_rate
			time.sleep(1/lps_rate)
	else:
		try:
			j = int(n)
			while j:
				read_lps_once(channels)
				j -= 1
		except ValueError:
			print('Please enter a valid selection')

# Read the LPS and display the results
def read_lps_once(channels):
	global lps_mode
	if len(channels) == 1:
		i = channels[0]
		if lps_mode == 0:
			(press, temp) = lps[i].ReadPressAndTemp()
			print('{0:<17} hPa    {1:<5} \xb0C'.format(press, temp))
		else:
			lps[i].OneShot()
			lps[i].ReadRegisters()
	else:
		readings = []
		for channel in channels:
			if lps_mode == 0:
				(press, temp) = lps[channel].ReadPressAndTemp()
				readings.append('  {0:<17} {1:<5}'.format(press, temp))
			else:
				lps[channel].OneShot()
				readings.append(lps[channel].ReadRegisters())
		for reading in readings:
			print(reading, end='')
		print('')

# Prints status of the board in a nice table
def print_status():
	#print('---------------------------------------------------------------------------------------------' +sr)
	print('=============================================================================================' +sr)
	print('{0}   {1}   {2}   {3}   {4}   {5}   {6}   {7}'.format(lps_status[0], lps_status[1], lps_status[2], lps_status[3], lps_status[4], lps_status[5], lps_status[6], lps_status[7]))
	print('     {0}         DAC A: {1} = {3:f}V      \tDAC B: {2} = {4:f}V'.format(adc_status, daca, dacb, daca*dac_ref_voltage/2**16, dacb*dac_ref_voltage/2**16))

def adc_menu():
	sensor = '0'
	inp = '1'
	while True:
		print(fy)
		print_status()
		print(fy+ '---------------------------------------------------------------------------------------------' +sr)
		print('      ' +by+fbk+ 'ADC MENU' +sr+ '   s: PRESSURE MENU   d: DAC MENU   z: BOARD MENU   c: CONFIG MENU   x: EXIT        ')
		print('')
		print('     {0}0{1}: test #0    {0}1{1}: test #1    {0}2{1}: test #2    {0}3{1}: test #3    {0}4{1}: test #4    {0}5{1}: test #5'.format(fy, sr))
		print('     {0}6{1}: test #6    {0}7{1}: test #7        {0}l{1}: test all              {0}r{1}: repeat previous test'.format(fy, sr))
		print(fy+ '---------------------------------------------------------------------------------------------' +sr)
		c = getch()
		print('')
		# if   c == 'a':
		#     return ('a')
		if   c == 's':
			return ('s')
		elif c == 'd':
			return ('d')
		elif c == 'z':
			return ('z')
		elif c == 'c':
			return ('c')
		elif c == 'x': #exit program
			myExit()
		elif c == '0':
			sensor = '0'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN1])
		elif c == '1':
			sensor = '1'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN2])
		elif c == '2':
			sensor = '2'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN5])
		elif c == '3':
			sensor = '3'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN6])
		elif c == '4':
			sensor = '4'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN0])
		elif c == '5':
			sensor = '5'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN3])
		elif c == '6':
			sensor = '6'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN4])
		elif c == '7':
			sensor = '7'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN7])
		elif c == 'l':
			sensor = 'l'
			inp = input("How many samples ('c' for continuous)? ")
			read_adc(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
		elif c == 'r':
			if   sensor == '0':
				read_adc(inp, [ads.MUX_AIN1])
			elif sensor == '1':
				read_adc(inp, [ads.MUX_AIN2])
			elif sensor == '2':
				read_adc(inp, [ads.MUX_AIN5])
			elif sensor == '3':
				read_adc(inp, [ads.MUX_AIN6])
			elif sensor == '4':
				read_adc(inp, [ads.MUX_AIN0])
			elif sensor == '5':
				read_adc(inp, [ads.MUX_AIN3])
			elif sensor == '6':
				read_adc(inp, [ads.MUX_AIN4])
			elif sensor == '7':
				read_adc(inp, [ads.MUX_AIN7])
			elif sensor == 'l':
				read_adc(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
		else: print('Invalid selection')

def dac_menu():
	while(True):
		print(fc)
		print_status()
		print(fc+ '---------------------------------------------------------------------------------------------' +sr)
		print('   a: ADC MENU   p: PRESSURE MENU      ' +bc+fbk+ 'DAC MENU' +sr+ '   z: BOARD MENU   c: CONFIG MENU   x: EXIT        ')
		print('')
		print('             {0}h{1}: set voltage on channel A          {0}j{1}: power down channel A '.format(fc, sr))
		print('             {0}n{1}: set voltage on channel B          {0}m{1}: power down channel B '.format(fc, sr))
		print(fc+ '---------------------------------------------------------------------------------------------' +sr)
		c = getch()
		print('')
		if   c == 'a':
			return 'a'
		elif c == 's':
			return 's'
		# elif c == 'd':
		#     return 'd'
		elif c == 'z':
			return 'z'
		elif c == 'c':
			return 'c'
		elif c == 'x': #exit program
			myExit()
		elif c == 'h':
			try:
				set_voltage = input('Enter new DC voltage: ')
				global daca
				daca = int((float(set_voltage)/dac_ref_voltage)*2**16)
				if daca >= 2**16-1:
					daca = 2**16-1
				dac.SendDACAValue(daca)
			except:
				print('invalid input entered')
		elif c == 'n':
			try:
				set_voltage = input('Enter new DC voltage: ')
				global dacb
				dacb = int((float(set_voltage)/dac_ref_voltage)*2**16)
				if dacb >= 2**16-1:
					dacb = 2**16-1
				dac.SendDACBValue(dacb)
			except:
				print('invalid input entered')
		elif c == 'j':
			dac.PowerDownDACA()
			daca = 0
		elif c == 'm':
			dac.PowerDownDACB()
			dacb = 0
		else: print('Invalid selection')

def pressure_menu():
	sensor = '0'
	inp = '1'
	while(True):
		global lps_mode, lps_rate
		if lps_mode == 0:
			mode = 'pressure and temperature'
		else:
			mode = 'registers'
		print(fm)
		print_status()
		print(fm+ '---------------------------------------------------------------------------------------------' +sr)
		print(    '          mode: {2}{0:^24}{3}      continuous polling rate: {2}{1:>3} Hz{3}'.format(mode, lps_rate, fm, sr))
		print(fm+ '---------------------------------------------------------------------------------------------' +sr)
		print('   a: ADC MENU      ' +bm+fbk+ 'PRESSURE MENU' +sr+ '   d: DAC MENU   z: BOARD MENU   c: CONFIG MENU   x: EXIT        ')
		print('')
		print("            {0}m{1}: toggle mode      {0}p{1}: set continuous polling rate      {0}b{1}: boot".format(fm, sr))
		print('')
		print('      {0}0{1}: test #0    {0}1{1}: test #1    {0}2{1}: test #2    {0}3{1}: test #3    {0}4{1}: test #4    {0}5{1}: test #5'.format(fm, sr))
		if lps_mode == 0:
			print('      {0}6{1}: test #6    {0}7{1}: test #7           {0}l{1}: test all           {0}r{1}: repeat previous test'.format(fm, sr))
		else:
			print('      {0}6{1}: test #6    {0}7{1}: test #7                                 {0}r{1}: repeat previous test'.format(fm, sr))
		print(fm+ '---------------------------------------------------------------------------------------------' +sr)
		c = getch()
		print('')
		if   c == 'a':
			return 'a'
		# elif c == 's':
		#     return 's'
		elif c == 'd':
			return 'd'
		elif c == 'z':
			return 'z'
		elif c == 'c':
			return 'c'
		elif c == 'x': #exit program
			myExit()
		elif c == 'm':
			if lps_mode == 0: lps_mode = 1
			else: lps_mode = 0
		elif c == 'p':
			lps_rate  = float(input('New frequency:'))
		elif c == 'b':
			try:
				inp = int(input('Boot which sensor?'))
				lps[inp].Boot()
				time.sleep(.1)
			except:
				print('Invalid Entry')
		elif c == '0':
			sensor = '0'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [0])
		elif c == '1':
			sensor = '1'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [1])
		elif c == '2':
			sensor = '2'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [2])
		elif c == '3':
			sensor = '3'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [3])
		elif c == '4':
			sensor = '4'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [4])
		elif c == '5':
			sensor = '5'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [5])
		elif c == '6':
			sensor = '6'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [6])
		elif c == '7':
			sensor = '7'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [7])
		elif c == 'l' and lps_mode == 0:
			sensor = 'l'
			inp = input("How many samples ('c' for continuous)? ")
			read_lps(inp, [0,1,2,3,4,5,6,7])
		elif c == 'r':
			if   sensor == '0':
				read_lps(inp, [0])
			elif sensor == '1':
				read_lps(inp, [1])
			elif sensor == '2':
				read_lps(inp, [2])
			elif sensor == '3':
				read_lps(inp, [3])
			elif sensor == '4':
				read_lps(inp, [4])
			elif sensor == '5':
				read_lps(inp, [5])
			elif sensor == '6':
				read_lps(inp, [6])
			elif sensor == '7':
				read_lps(inp, [7])
			elif sensor == 'l':
				read_lps(inp, [0,1,2,3,4,5,6,7])
		else: print('Invalid selection')

def board_menu():
	while(True):
		print(fg)
		print_status()
		print(fg+ '---------------------------------------------------------------------------------------------' +sr)
		print('   a: ADC MENU   s: PRESSURE MENU   d: DAC MENU      ' +bg+fbk+ 'BOARD MENU' +sr+ '   c: CONFIG MENU   x: EXIT        ')
		print('')
		print('        {0}g{1}: toggle LED1 ON     {0}h{1}: toggle LED1 OFF      {0}j{1}: blink LED1    {0}k{1}: pulse TX0'.format(fg, sr))
		print('        {0}v{1}: toggle LED2 ON     {0}b{1}: toggle LED2 OFF      {0}n{1}: blink LED2    {0}m{1}: pulse TX1'.format(fg, sr))
		print(fg+ '---------------------------------------------------------------------------------------------' +sr)
		c = getch()

		if   c == 'a':
			return 'a'
		elif c == 's':
			return 's'
		elif c == 'd':
			return 'd'
		# elif c == 'z':
		#     return 'z'
		elif c == 'c':
			return 'c'
		elif c == 'x': #exit program
			myExit()
		elif c == 'g':
			board.ledAct(1,1)
		elif c == 'h':
			board.ledAct(1,0)
		elif c == 'j':
			global led1_freq
			board.ledAct(1,2,led1_freq)
		elif c == 'v':
			board.ledAct(2,1)
		elif c == 'b':
			board.ledAct(2,0)
		elif c == 'n':
			global led2_freq
			board.ledAct(2,2,led2_freq)
		elif c == 'k':
			inp = input("For how long? ")
			board.pulse(0,int(inp))
		elif c == 'm':
			inp = input("For how long? ")
			board.pulse(1,int(inp))
		else: print('Invalid selection')

def config_menu():
	global led1_freq, led2_freq, adc_rate, lps_rate
	while(True):
		print(fr)
		print_status()
		print('    LED1 : {0} Hz      ADC Continuous: {1} Hz'.format(led1_freq, adc_rate))
		print('    LED2 : {0} Hz      LPS Continuous: {1} Hz'.format(led2_freq, lps_rate))
		print(fr+ '---------------------------------------------------------------------------------------------' +sr)
		print('   a: ADC MENU   s: PRESSURE MENU   d: DAC MENU   z: BOARD MENU      ' +br+fbk+ 'CONFIG MENU' +sr+ '   x: EXIT        ')
		print('')
		print('        {0}f{1}: LED1 frequency       {0}g{1}: ADC polling'.format(fr, sr))
		print('        {0}v{1}: LED2 frequency       {0}b{1}: LPS polling'.format(fr, sr))
		print(fr+ '---------------------------------------------------------------------------------------------' +sr)
		c = getch()
		print('')
		if   c == 'a':
			return 'a'
		elif c == 's':
			return 's'
		elif c == 'd':
			return 'd'
		elif c == 'z':
			return 'z'
		# elif c == 'c':
		#     return 'c'
		elif c == 'x': #exit program
			myExit()
		elif c == 'f':
			led1_freq = int(input('New frequency: '))
		elif c == 'v':
			led2_freq = int(input('New frequency: '))
		elif c == 'g':
			adc_rate  = int(input('New frequency:'))
		elif c == 'b':
			lps_rate  = int(input('New frequency:'))
		else: print('Invalid selection')
def myExit():
	print('exiting....')
	dac.PowerDownDACA()
	dac.PowerDownDACB()
	print('Powered down DACs')
	board.ledAct(1,0)
	board.ledAct(2,0)
	print('Turned off LEDs')
	sys.exit()

# This starts the whole loop
menu = 'a'
while True:
	if   menu == 'a':
		menu = adc_menu()
	elif menu == 's':
		menu = pressure_menu()
	elif menu == 'd':
		menu = dac_menu()
	elif menu == 'z':
		menu = board_menu()
	elif menu == 'c':
		menu = config_menu()
	else:
		print('Something went wrong')
		menu = 'a'
