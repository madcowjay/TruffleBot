"""
Updated 2018/04/25
  -Python3 only supported now
  -added timestamp to log file
                                    -JW
"""

import socket, traceback
import lib.pyads1256
import lib.pydac8532
import wiringpi as wp
import time
from   multiprocessing import Queue
import threading
import numpy as np
import os
import sys
import pickle
import lib.board_utils as bu

#this is the worker function that runs in a separate thread if the pi is registered to transmit
def pulser(pattern, duration, padding):
	pcomm = None
	# while not pcomm=='stop':
	time.sleep(padding)
	for i in pattern:
		# print(i)
		start_time = time.time()
		if i==1:
			print('pulse on')
			bu.pulse(1,duration)
		else:
			time.sleep(duration)
		if not pulseq.empty():
			pcomm = pulseq.get()
			if pcomm=='stop':
				break
	print('pulser ended')

#==========================================================================================================
# setting up stuff
print(time.asctime(time.localtime(time.time())))

## set up adc and dac
ads = lib.pyads1256.ADS1256()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

dac = lib.pydac8532.DAC8532()
dac.SendDACAValue(0.62 * 2**16)

# pulsing queue
pulseq = Queue()

#set up socket and options
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
bind(('', 5000))


#init variables that need it
outstring = ''
chunk_num = 0
data_len = 0
log = {}
elapsed =[]
channels= 8 # change for other boards

try:
	with open('txpattern.pickle','rb') as f:
		tx_message = pickle.load(f)
	tx_pattern = np.array([int(n) for n in tx_message.split()])
	print('tx recieved')
	print(tx_pattern)
except Exception as e:
	print(e)
	tx_pattern = None

#==========================================================================================================

#listen for commands -- main function
print("Listening for broadcasts...")
bu.ledAct(1,2,1) # blink LED 1 at 1 Hz
end_flag = False
while not end_flag:
	try:
		#get commands
		message, address = s.recvfrom(8192)
		commands = message.split()
		print(commands)

		if commands[0]==b'collect':
			bu.ledAct(2,2,4) # blink LED 2 at 4 Hz
			sample_num = int(commands[1])
			spacing = float(commands[2])
			pulse_duration = float(commands[3])
			padding = float(commands[4])

			#init array to store data
			data = np.zeros([sample_num,channels],dtype='int32')

			#heat the sensors up, pause for a second
			# print("Heating...")
			# for i in range(500):
			# 	dac.SendDACAValue(49151)
			# 	time.sleep(0.01)
			# print("Sensors heated")


			#start thread to generate pattern
			if tx_pattern!= None:
				t = threading.Thread(target=pulser,args=(tx_pattern,pulse_duration, padding))
				if not t.isAlive():
					t.start()
					print('started pulser')

			for i in range(sample_num):
				start_time = time.time()
				# collect samples from feach sensor on board
				print('collecting %s'%i)

				#heat up heater
				# dac.SendDACAValue(49151)
				# time.sleep(0.04) #adc interval
				print("Sampling...")
				sam_1 = ads.getADCsample(ads.MUX_AIN0,ads.MUX_AINCOM)
				sam_2 = ads.getADCsample(ads.MUX_AIN1,ads.MUX_AINCOM)
				sam_3 = ads.getADCsample(ads.MUX_AIN2,ads.MUX_AINCOM)
				sam_4 = ads.getADCsample(ads.MUX_AIN3,ads.MUX_AINCOM)
				sam_5 = ads.getADCsample(ads.MUX_AIN4,ads.MUX_AINCOM)
				sam_6 = ads.getADCsample(ads.MUX_AIN5,ads.MUX_AINCOM)
				sam_7 = ads.getADCsample(ads.MUX_AIN6,ads.MUX_AINCOM)
				sam_8 = ads.getADCsample(ads.MUX_AIN7,ads.MUX_AINCOM)
				# print("Sampled all")
				#
				# # dac.SendDACAValue(49151)
				#
				# print("saving samples to array")
				sample = np.array([sam_1,sam_2,sam_3,sam_4,sam_5,sam_6,sam_7,sam_8], dtype='int32')
				# print("sample array created")
				data[i] = sample # save the array of samples to the data dict, with key as sample num
				# print('saved to dict')

				elapsed_time = time.time() - start_time
				elapsed.append(elapsed_time)
				print('elapsed: %s, spacing: %s, sleep: %s'%(elapsed_time,spacing,spacing-elapsed_time))
				time.sleep(spacing-elapsed_time) #TODO: change back to spacing-elapsed_time
				print("loop end")
			#record end time
			end_time = time.time()

			print("adding to log")
			#add info to logfile
			log['Data'] = data
			log['End Time'] = end_time
			log['Average Elapsed'] = sum(elapsed)/float(len(elapsed))
			log['PID'] = os.getpid()
			log['TxPattern'] = tx_pattern

			#serialize data to be sent over network
			print(log)
			with open('/home/pi/TruffleBot/log/sendfile.pickle','wb') as f:
				pickle.dump(log,f)
				print('pickled!')


			#send the end flag to trigger data collection on host
			s.sendto('end_flag'.encode('utf-8'),address)
			pulseq.put('stop')
			print('end')
			end_flag=True
			bu.ledAct(2,0) #turn off LED 2

	except Exception as e:
			print(e)
bu.ledAct(1,0)
