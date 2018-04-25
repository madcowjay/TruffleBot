# generic imports
import os, time, threading, sys
from   colorama import init, Fore, Back, Style
import wiringpi as wp
import numpy    as np

# project specific
from   lib.getch import *
import lib.pyads1256
import lib.pydac8532
import lib.pylps22hb
from   lib.board_utils import *

# console colors
init() #colorama
bg  = Back.GREEN; br  = Back.RED; bb  = Back.BLUE; by  = Back.YELLOW; bc  = Back.CYAN; bm  = Back.MAGENTA
fg  = Fore.GREEN; fr  = Fore.RED; fb  = Fore.BLUE; fy  = Fore.YELLOW; fc  = Fore.CYAN; fm  = Fore.MAGENTA
fbk = Fore.BLACK; fw  = Fore.WHITE
sr  = Style.RESET_ALL

# set up board
wp.wiringPiSetupPhys
wp.pinMode(26, wp.INPUT) #I actually snipped this pin off the header, but in case you don't...

# set up pressure sensors: currently just nullify them so they don't talk on the line
all_cs = [33, 32, 40, 22, 35, 36, 7, 18]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)
lps = []
lps_status = []
for index in range(len(all_cs)):
	lps.append(lib.pylps22hb.LPS22HB(all_cs[index]))
	if lps[index].ReadID() == '0C':
		lps_status.append(fg+' LPS' + str(index) + ' UP ' +sr)
	else:
		lps_status.append(fr+'LPS' + str(index) + ' DOWN' +sr)

# set up ADC
ads = lib.pyads1256.ADS1256()
ads.chip_select()
if ads.ReadID()==3:
	adc_status = fg+' ADC UP '+sr
else: adc_status = fr+'ADC DOWN'+str
ads.ConfigADC()
ads.SyncAndWakeup()
adc_ref_voltage = 2.5
adc_gain = 2

# set up 16 bit DAC
dac = lib.pydac8532.DAC8532()
dac_ref_voltage = 3.3
dac_max_val  = 1*2**16-1
dac.SendDACAValue(0)
dac.SendDACBValue(0)
daca = 0
dacb = 0

# Function to get keyboard interrupts (cross-platform)
def input_thread(a_list):
	getch()
	a_list.append(True)

# Helper function to read ADC: handles discrete vs. continuous
def read_ads(n, channels):
	print(sr)
	if n == 'c':
		a_list = []
		i = 0
	#	_thread.start_new_thread_ads(input_thread, (a_list,))
		t = threading.Thread(target=input_thread, args=(a_list,))
		t.start()
		while not a_list:
			i += 1
			read_ads_once(channels)
			time.sleep(.5)
	else:
		try:
			j = int(n)
			while j:
				read_ads_once(channels)
				j -= 1
		except:
			pass

# Read the ADC and display the results
def read_ads_once(channels):
	if len(channels) == 1:
		result_in_twos_comp = ads.getADCsample(channels[0], ads.MUX_AINCOM)
		result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
		voltage = (result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain
		res = float(result_in_twos_comp)
		perc = np.mod(res-2**23,2**24)/2**24
		if voltage < 0:
			print('Voltage: \t%.9f \tpercent of range: \t%.9f' %(voltage, perc))
		else:
			print('Voltage: \t %.9f \tpercent of range: \t%.9f' %(voltage, perc))
	else:
		voltages = []
		for channel in channels:
			result_in_twos_comp = ads.getADCsample(channel, ads.MUX_AINCOM)
			result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
			voltages.append((result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain)
		print(voltages)

# Helper function to read LPS: handles discrete vs. continuous
def read_lps(n, channels):
	print(sr)
	if n == 'c':
		a_list = []
		i = 0
	#	_thread.start_new_thread_ads(input_thread, (a_list,))
		t = threading.Thread(target=input_thread, args=(a_list,))
		t.start()
		while not a_list:
			i += 1
			read_lps_once(channels)
			time.sleep(.5)
	else:
		try:
			j = int(n)
			while j:
				read_lps_once(channels)
				j -= 1
		except:
			pass

# Read the LPS and display the results
def read_lps_once(channels):
	if len(channels) == 1:
		result_in_twos_comp = ads.getADCsample(channels[0], ads.MUX_AINCOM)
		result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
		voltage = (result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain
		res = float(result_in_twos_comp)
		perc = np.mod(res-2**23,2**24)/2**24
		if voltage < 0:
			print('Voltage: \t%.9f \tpercent of range: \t%.9f' %(voltage, perc))
		else:
			print('Voltage: \t %.9f \tpercent of range: \t%.9f' %(voltage, perc))
	else:
		voltages = []
		for channel in channels:
			result_in_twos_comp = ads.getADCsample(channel, ads.MUX_AINCOM)
			result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
			voltages.append((result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain)
		print(voltages)

    #lps[i].OneShot()
    #time.sleep(.1)
    #lps[i].ReadRegisters()
    #print('\ttemperature is: ' + str(lps[i].ReadTemp())),
    #print('\tpressure is:    ' + str(lps[i].ReadPress()))



# Prints status of the board in a nice table
def print_status():
	#print('---------------------------------------------------------------------------------------------' +sr)
	print('=============================================================================================' +sr)
	print('{0}   {1}   {2}   {3}   {4}   {5}   {6}   {7}'.format(lps_status[0], lps_status[1], lps_status[2], lps_status[3], lps_status[4], lps_status[5], lps_status[6], lps_status[7]))
	print('     {0}         DAC A: {1} = {3:f}V      \tDAC B: {2} = {4:f}V'.format(adc_status, daca, dacb, daca*dac_ref_voltage/2**16, dacb*dac_ref_voltage/2**16))

def adc_menu():
	print(fy)
	print_status()
	print(sr)
	print('            ' +by+fbk+ 'ADC MENU' +sr+ '     d: DAC MENU    p: PRESSURE MENU    c: CONFIG MENU    x: EXIT        ')
	print('')
	print(' 0: test #0    1: test #1    2: test #2    3: test #3    4: test #4    5: test #5')
	print(' 6: test #6    7: test #7                  a: test all    r: repeat previous test')
	print(fy+ '---------------------------------------------------------------------------------------------' +sr)
	c = getch()
	if   c == 'x': #exit program
		myExit()
	# elif c == 'a':
	# 	adc_menu()
	elif c == 'd':
		dac_menu()
	elif c == 'p':
		pressure_menu()
	elif c == 'c':
		config_menu()
	elif c == '0':
		sensor = '0'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN1])
	elif c == '1':
		sensor = '1'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN2])
	elif c == '2':
		sensor = '2'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN5])
	elif c == '3':
		sensor = '3'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN6])
	elif c == '4':
		sensor = '4'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN0])
	elif c == '5':
		sensor = '5'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN3])
	elif c == '6':
		sensor = '6'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN74])
	elif c == '7':
		sensor = '7'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN7])
	elif c == 'a':
		sensor = 'a'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_ads(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
	elif c == 'r':
		if   sensor == '0':
			read_ads(inp, [ads.MUX_AIN1])
		elif sensor == '1':
			read_ads(inp, [ads.MUX_AIN2])
		elif sensor == '2':
			read_ads(inp, [ads.MUX_AIN5])
		elif sensor == '3':
			read_ads(inp, [ads.MUX_AIN6])
		elif sensor == '4':
			read_ads(inp, [ads.MUX_AIN0])
		elif sensor == '5':
			read_ads(inp, [ads.MUX_AIN3])
		elif sensor == '6':
			read_ads(inp, [ads.MUX_AIN4])
		elif sensor == '7':
			read_ads(inp, [ads.MUX_AIN7])
		elif sensor == 'a':
			read_ads(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
	else: print('\nInvalid selection')

def dac_menu():
	print(fc)
	print_status()
	print(sr)
	print('         a: ADC MENU       ' +bc+fbk+ 'DAC MENU' +sr+ '    p: PRESSURE MENU    c: CONFIG MENU    x: EXIT        ')
	print('')
	print('        h: set voltage on channel A          j: power down channel A ')
	print('        k: set voltage on channel B          l: power down channel B ')
	print(fc+ '---------------------------------------------------------------------------------------------' +sr)
	c = getch()
	if   c == 'x': #exit program
		myExit()
	elif c == 'a':
		adc_menu()
	# elif c == 'd':
	# 	dac_menu()
	elif c == 'p':
		pressure_menu()
	elif c == 'c':
		config_menu()
	elif c == 'h:
		set_voltage = input('\nEnter new DC voltage: ')
		daca = int((float(set_voltage)/dac_ref_voltage)*2**16)
		if daca >= 2**16-1:
			daca = 2**16-1
		dac.SendDACAValue(daca)
	elif c == 'k':
		set_voltage = input('\nEnter new DC voltage: ')
		dacb = int((float(set_voltage)/dac_ref_voltage)*2**16)
		if dacb >= 2**16-1:
			dacb = 2**16-1
		dac.SendDACBValue(dacb)
	elif c == 'j':
		dac.PowerDownDACA()
		daca = 0
	elif c == 'l':
		dac.PowerDownDACB()
		dacb = 0
	else: print('\nInvalid selection')

def pressure_menu():
	print(fm)
	print_status()
	print(sr)
	print('         a: ADC MENU    d: DAC MENU       ' +bm+fbk+ 'PRESSURE MENU' +sr+ '    c: CONFIG MENU    x: EXIT        ')
	print('')
	print(' 0: test #0    1: test #1    2: test #2    3: test #3    4: test #4    5: test #5')
	print(' 6: test #6    7: test #7                  a: test all    r: repeat previous test')
	print(fm+ '---------------------------------------------------------------------------------------------' +sr)
	c = getch()
	if   c == 'x': #exit program
		myExit()
	elif c == 'a':
		adc_menu()
	elif c == 'd':
		dac_menu()
	# elif c == 'p':
	# 	pressure_menu()
	elif c == 'c':
		config_menu()
	elif c == '0':
		sensor = '0'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [0])
	elif c == '1':
		sensor = '1'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [1])
	elif c == '2':
		sensor = '2'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [2])
	elif c == '3':
		sensor = '3'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [3])
	elif c == '4':
		sensor = '4'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [4])
	elif c == '5':
		sensor = '5'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [5])
	elif c == '6':
		sensor = '6'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [6])
	elif c == '7':
		sensor = '7'
		inp = input("\nHow many samples ('c' for continuous)? ")
		read_lps(inp, [7])
	elif c == 'a':
		sensor = 'a'
		inp = input("\nHow many samples ('c' for continuous)? ")
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
		elif sensor == 'a':
			read_lps(inp, [0,1,2,3,4,5,6,7])
	else: print('\nInvalid selection')

def config_menu():
	print(fr)
	print_status()
	print(sr)
	print('         a: ADC MENU    d: DAC MENU    p: PRESSURE MENU    ' +br+fbk+ 'CONFIG MENU' +sr+ '    x: EXIT        ')
	print('')
	print('                      q: toggle LED1 ON     w: toggle LED1 OFF      e: blink LED1')
	print('                      r: toggle LED1 ON     t: toggle LED1 OFF      y: blink LED1')
	print(fr+ '---------------------------------------------------------------------------------------------' +sr)
	c = getch()
	if   c == 'x': #exit program
		myExit()
	elif c == 'a':
		adc_menu()
	elif c == 'd':
		dac_menu()
	elif c == 'p':
		pressure_menu()
	# elif c == 'c':
	# 	config_menu()
	elif c == 'q':
		ledACT(1,1)
	elif c == 'w':
		ledACT(1,0)
	elif c == 'e':
		ledACT(1,2)
	elif c == 'r':
		ledACT(2,1)
	elif c == 't':
		ledACT(2,0)
	elif c == 'y':
		ledACT(2,2)
	else: print('\nInvalid selection')

def myExit():
	print('\nexiting....')
	dac.PowerDownDACA()
	dac.PowerDownDACB()
	print('Powered down DACs')
	ledAct(1,0)
	ledAct(2,0)
	print('Turned off LEDs')
	sys.exit()

while True:
	adc_menu()
