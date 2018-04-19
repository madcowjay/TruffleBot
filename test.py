from __future__ import print_function
from six.moves import _thread
import random
from pi_utils.getch import *
import os
from drivers import *
from colorama import init, Fore, Back, Style
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
ads.ConfigADC()
ads.SyncAndWakeup()

init() #colorama

ref_voltage = 2.5
gain = 2

low = 1
high = 10

def input_thread(a_list):
	getch()
	a_list.append(True)

def read_once():
	result_in_twos_comp = ads.ReadADC()
	result = -(result_in_twos_comp & 0x800000) | (result_in_twos_comp & 0x7fffff)
	voltage = (result*2*ref_voltage) / (2**23 - 1) / gain
	res = float(result_in_twos_comp)
	perc = np.mod(res-2**23,2**24)/2**24)
	print('Voltage: %.9f, percent of range: %.9f' %(voltage, perc))

def read(n):
	if n == 'c':
		a_list = []
		i = 0
		_thread.start_new_thread(input_thread, (a_list,))
		while not a_list:
			i += 1
			read_once()
	j = int(n)
	while j:
		read_once()
		j -= 1

def print_main_menu():
	os.system('clear')
	print(Fore.GREEN)
	print('---------------------------------------------------------------------------------')
	print('                                 Main Menu')
	print('ADC id: {0:d}'.format(myid))
	print('a - ADC menu   ')
	print('x - exit       ')
	print('---------------------------------------------------------------------------------')

def print_adc_menu:
	os.system('clear')
	print(Fore.RED)
	print('---------------------------------------------------------------------------------')
	print('                                 ADC Menu')
	print('ADC id: {0:d}'.format(myid))
	print('a - test all  0 ... 7 - test #0 ... #7            r - repeat previous test')
	print('x - exit to main       ')
	print('---------------------------------------------------------------------------------')

os.system('clear')
print_main_menu()
while True:
	c = getch()
	os.system('clear')
	print_main_menu()

	if   c == 'x':
		break
	elif c == '1':
		os.system('clear')
		print_adc_menu()
		while True:
			c = getch()
			os.system('clear')
			print_adc_menu()

			if   c == 'x':
				break
			elif c == '0':
				ads.SetInputMux(ads.MUX_AIN1, ads.MUX_AINCOM)
				ads.SyncAndWakeup()
				input = ("How many samples? ('c' for continuous)"")
				read(input)

	elif c == 'l':
		low = int(input('enter low number: '))
		print('new range is ' + str(low) + ' to ' + str(high))
	elif c == 'h':
		high = int(input('enter high number: '))
		print('new range is ' + str(low) + ' to ' + str(high))
	elif c == 'r':
		print(random.uniform(low, high))
	elif c == 's':
		print('current range is: ' + str(low) + ' to ' + str(high))
		print('loop iterations: {0:d}'.format(count))
	elif c == 'z':
		a_list = []
		i = 0
		_thread.start_new_thread(input_thread, (a_list,))
		while not a_list:
			i += 1
			print('.', end='')
		print('\ndone with that - i: ' + str(i))
	else:
		print('Invalid selection')
print('exiting....')
