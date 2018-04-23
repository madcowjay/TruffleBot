# backward compatibility
from __future__ import print_function
from six.moves  import _thread

# generic imports
import os, time
from colorama import init, Fore, Back, Style
import wiringpi as wp
import numpy as np

# project specific
from pi_utils.getch1 import *
import drivers.pyads1256
import drivers.pydac8532
import drivers.pylps22hb

# set up environment
init() #colorama

# set up board
wp.wiringPiSetupPhys
wp.pinMode(26, wp.INPUT) #I actually snipped this pin off the header, but in case you don't...

# set up pressure sensors - currently just nullify them so they don't talk on the line
all_cs = [33, 32, 40, 22, 35, 36, 7, 18]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)

# set up ADC
ads = drivers.pyads1256.ADS1256()
ads.chip_select()
myid = ads.ReadID()
ads.ConfigADC()
ads.SyncAndWakeup()
adc_ref_voltage = 2.5
adc_gain = 2

# set up 16 bit DAC
dac = drivers.pydac8532.DAC8532()
dac_max_val  = 1*2**16-1
dac.SendDACAValue(0)
dac.SendDACBValue(0)
daca = 0
dacb = 0

# Function to get keyboard interrupts (cross-platform)
def input_thread(a_list):
	getch()
	a_list.append(True)

# Read the ADC and display the results
def read_once(channels):
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

# Helper function to read ADC - handles discrete vs. continuous
def read(n, channels):
	print(Style.RESET_ALL)
	if n == 'c':
		a_list = []
		i = 0
		_thread.start_new_thread(input_thread, (a_list,))
		while not a_list:
			i += 1
			read_once(channels)
	else:
		try:
			j = int(n)
			while j:
				read_once(channels)
				j -= 1
		except:
			pass

# Prints status of the board in a nice table
def print_status():
	print('#########################################################################################')
	print(' ADC id: {0:d} \tDAC A voltage: {1:d} \tDAC B voltage: {2:d}'.format(myid, daca, dacb))

def print_main_menu():
	print(Fore.GREEN)
	print_status()
	print('-----------------------------------------------------------------------------------------')
	print('                                        MAIN MENU')
	print('')
	print(' a - ADC menu       d - DAC menu                                         x - exit program')
	print('#########################################################################################')

def print_adc_menu():
	print(Fore.RED)
	print_status()
	print('-----------------------------------------------------------------------------------------')
	print('                                      main/ ADC MENU')
	print('')
	print(' 0 - test #0   1 - test #1   2 - test #2   3 - test #3   4 - test #4   5 - test #5')
	print(' 6 - test #6   7 - test #7   a - test all  r - repeat previous test    x - exit to main')
	print('#########################################################################################')

def print_dac_menu():
	print(Fore.BLUE)
	print_status()
	print('-----------------------------------------------------------------------------------------')
	print('                                      main/ DAC MENU')
	print('')
	print(' a - set voltage on channel A          b -set voltage on channel B ')
	print(' o - power down channel A              p -power down channel B           x - exit to main')
	print('#########################################################################################')

while True:
	print_main_menu()
	c = getch()
	if   c == 'x':
		break
	elif c == 'a':
		inp = ''
		while True:
			print_adc_menu()
			d = getch()
			if   d == 'x':
				break
			elif d == '0':
				sensor = '0'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN1])
			elif d == '1':
				sensor = '1'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN2])
			elif d == '2':
				sensor = '2'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN5])
			elif d == '3':
				sensor = '3'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN6])
			elif d == '4':
				sensor = '4'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN0])
			elif d == '5':
				sensor = '5'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN3])
			elif d == '6':
				sensor = '6'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN74])
			elif d == '7':
				sensor = '7'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN7])
			elif d == 'a':
				sensor = 'a'
				inp = input("\nHow many samples ('c' for continuous)? ")
				read(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
			elif d == 'r':
				if   sensor == '0':
					read(inp, [ads.MUX_AIN1])
				elif sensor == '1':
					read(inp, [ads.MUX_AIN2])
				elif sensor == '2':
					read(inp, [ads.MUX_AIN5])
				elif sensor == '3':
					read(inp, [ads.MUX_AIN6])
				elif sensor == '4':
					read(inp, [ads.MUX_AIN0])
				elif sensor == '5':
					read(inp, [ads.MUX_AIN3])
				elif sensor == '6':
					read(inp, [ads.MUX_AIN4])
				elif sensor == '7':
					read(inp, [ads.MUX_AIN7])
				elif sensor == 'a':
					read(inp, [ads.MUX_AIN1, ads.MUX_AIN2, ads.MUX_AIN5, ads.MUX_AIN6, ads.MUX_AIN0, ads.MUX_AIN3, ads.MUX_AIN4, ads.MUX_AIN7])
			else:
				print('Invalid selection')
	elif c == 'd':
		while True:
			print_dac_menu()
			e = getch()
			if   e == 'x':
				break
			elif e == 'a':
				inp = input('\nEnter new value for DAC A: ')
				daca = int(inp) #TODO either want entries as percent or voltage
				dac.SendDACAValue(daca)
			elif e == 'b':
				inp = input('\nEnter new value for DAC B: ')
				dacb = int(inp) #TODO either want entries as percent or voltage
				dac.SendDACAValue(dacb)
			elif e == 'o':
				dac.PowerDownDACA()
				daca = 0
			elif e == 'p':
				dac.PowerDownDACB()
				dacb = 0
			else:
				print('Invalid selection')
	else:
		print('Invalid selection')
print('exiting....')
