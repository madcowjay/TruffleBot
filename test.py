from __future__ import print_function
from six.moves import _thread
import random
from pi_utils.getch import *
import os
from drivers import *
from colorama import init, Fore, Back, Style
init()

low = 1
high = 10
count = 0

def input_thread(a_list):
	getch()
	a_list.append(True)

os.system('clear')
print(Fore.RED)
print('---------------------------------------------------------------------------------')
print('                                 Main Menu')
print('x - exit       l - st low number       h - set high number      r - random number')
print('s - status     m - message             z - loop test')
print('---------------------------------------------------------------------------------')

while True:
	count += 1
	c = getch()
	os.system('clear')
	print(Fore.GREEN)
	print('---------------------------------------------------------------------------------')
	print('                                 Main Menu')
	print('x - exit       l - st low number       h - set high number      r - random number')
	print('s - status     m - message             z - loop test')
	print('---------------------------------------------------------------------------------')

	if   c == 'x':
		break
	elif c == 'm':
		print('blah blah blah')
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
#		flag = True
#		while flag:
#			try:
#				print('...')
#			except KeyboardInterrupt:
#				print('done')
#				flag =  False
	else:
		print('Invalid selection')
print('exiting....')
