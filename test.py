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

def input_thread(a_list):
	getch()
	a_list.append(True)

def read_once():
	result_in_twos_comp = ads.ReadADC()
	result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
	voltage = (result*2*adc_ref_voltage) / (2**23 - 1) / adc_gain
	res = float(result_in_twos_comp)
	perc = np.mod(res-2**23,2**24)/2**24
	if voltage < 0:
		print('Voltage: \t%.9f \tpercent of range: \t%.9f' %(voltage, perc))
	else:
		print('Voltage: \t %.9f \tpercent of range: \t%.9f' %(voltage, perc))

def read(n):
	print(Style.RESET_ALL)
	if n == 'c':
		a_list = []
		i = 0
		_thread.start_new_thread(input_thread, (a_list,))
		while not a_list:
			i += 1
			read_once()
	else:
		try:
			j = int(n)
			while j:
				read_once()
				j -= 1
		except:
			pass

def print_status():
	print(' ADC id: {0:d} \tDAC A voltage: {1:d} \tDAC B voltage: {2:d}'.format(myid, daca, dacb))

def print_main_menu():
	print(Fore.GREEN)
	print('-----------------------------------------------------------------------------------------')
	print('                                        MAIN MENU')
	print_status()
	print('')
	print(' a - ADC menu       d - DAC menu                                         x - exit program')
	print('-----------------------------------------------------------------------------------------')

def print_adc_menu():
	print(Fore.RED)
	print('-----------------------------------------------------------------------------------------')
	print('                                      main/ ADC MENU')
	print_status()
	print('')
	print(' 0 - test #0   1 - test #1   2 - test #2   3 - test #3   4 - test #4   5 - test #5')
	print(' 6 - test #6   7 - test #7   a - test all  r - repeat previous test    x - exit to main')
	print('-----------------------------------------------------------------------------------------')

def print_dac_menu():
	print(Fore.BLUE)
	print('-----------------------------------------------------------------------------------------')
	print('                                      main/ DAC MENU')
	print_status()
	print('')
	print(' a - set voltage on channel A          b -set voltage on channel B ')
	print(' o - power down channel A              p -power down channel B           x - exit to main')
	print('-----------------------------------------------------------------------------------------')

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
				ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '1':
				sensor = '1'
				ads.SetInputMux(ads.MUX_AIN2, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '2':
				sensor = '2'
				ads.SetInputMux(ads.MUX_AIN5, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '3':
				sensor = '3'
				ads.SetInputMux(ads.MUX_AIN6, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '4':
				sensor = '4'
				ads.SetInputMux(ads.MUX_AIN0, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '5':
				sensor = '5'
				ads.SetInputMux(ads.MUX_AIN3, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '6':
				sensor = '6'
				ads.SetInputMux(ads.MUX_AIN4, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == '7':
				sensor = '7'
				ads.SetInputMux(ads.MUX_AIN7, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == 'a':
				sensor = 'a'
				ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				inp = input("How many samples ('c' for continuous)? ")
				read(inp)
			elif d == 'r':
				if sensor == '0':
					ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '1':
					ads.SetInputMux(ads.MUX_AIN2, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '2':
					ads.SetInputMux(ads.MUX_AIN5, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '3':
					ads.SetInputMux(ads.MUX_AIN6, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '4':
					ads.SetInputMux(ads.MUX_AIN0, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '5':
					ads.SetInputMux(ads.MUX_AIN3, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '6':
					ads.SetInputMux(ads.MUX_AIN4, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == '7':
					ads.SetInputMux(ads.MUX_AIN7, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
				elif sensor == 'a':
					ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
					ads.SyncAndWakeup()
					read(inp)
			else:
				print('Invalid selection')
	elif c == 'd':
		while True:
			print_dac_menu()
			e = getch()
			if   e == 'x':
				break
			elif e == 'a':
				print('placeholder for a')
			elif e == 'b':
				print('placeholder for b')
			elif e == 'o':
				print('placeholder for o')
			elif e == 'p':
				print('placeholder for p')
			else:
				print('Invalid selection')
	else:
		print('Invalid selection')
print('exiting....')
