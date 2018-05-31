import os, sys, time, socket, pickle, threading, configparser
import numpy as np
import wiringpi as wp
from   multiprocessing import Queue
from   optparse import OptionParser

# process command line arguments
usage = 'python3 client.py [OPTION]...'
parser = OptionParser(usage)
parser.add_option('-d','--debug',action='store_true',dest='debugFlag',help='display debug messages while running',default=False)
parser.add_option('-c','--config-file',dest='configfile',help='use the indicated configuration file, if not invoked, default.cfg is used',default='default.cfg')
(options, args) = parser.parse_args()
config_file = options.configfile
if options.debugFlag: os.environ['DEBUG'] = 'True'
print('loaded confgiuration file: {}'.format(config_file))

# Load these after DEBUG status has been determined
import lib.pyads1256
import lib.pydac8532
import lib.pylps22hb
import lib.TB_pulser
import lib.sensor_board

config = configparser.RawConfigParser()
config.read(config_file)

LED1_PIN      = int(config.get('GPIO', 'LED1_PIN'))
LED2_PIN      = int(config.get('GPIO', 'LED2_PIN'))
TX0_PIN       = int(config.get('GPIO', 'TX0_PIN'))
TX1_PIN       = int(config.get('GPIO', 'TX1_PIN'))
PRESS0_PIN    = int(config.get('GPIO', 'PRESS0_PIN'))
PRESS1_PIN    = int(config.get('GPIO', 'PRESS1_PIN'))
PRESS2_PIN    = int(config.get('GPIO', 'PRESS2_PIN'))
PRESS3_PIN    = int(config.get('GPIO', 'PRESS3_PIN'))
PRESS4_PIN    = int(config.get('GPIO', 'PRESS4_PIN'))
PRESS5_PIN    = int(config.get('GPIO', 'PRESS5_PIN'))
PRESS6_PIN    = int(config.get('GPIO', 'PRESS6_PIN'))
PRESS7_PIN    = int(config.get('GPIO', 'PRESS7_PIN'))
DAC_CS_PIN    = int(config.get('GPIO', 'DAC_CS_PIN'))
ADC_CS_PIN    = int(config.get('GPIO', 'ADC_CS_PIN'))
ADC_DRDY_PIN  = int(config.get('GPIO', 'ADC_DRDY_PIN'))
ADC_RESET_PIN = int(config.get('GPIO', 'ADC_RESET_PIN'))
ADC_PDWN_PIN  = int(config.get('GPIO', 'ADC_PDWN_PIN'))

ADC_SPI_CHANNEL     =   int(config.get('ADC', 'ADC_SPI_CHANNEL'))
ADC_SPI_FREQUENCY   =   int(config.get('ADC', 'ADC_SPI_FREQUENCY'))

DAC_SPI_CHANNEL     =   int(config.get('DAC', 'DAC_SPI_CHANNEL'))
DAC_SPI_FREQUENCY   =   int(config.get('DAC', 'DAC_SPI_FREQUENCY'))
DAC_voltage_percent = float(config.get('DAC', 'voltage_percent'))

LPS_SPI_CHANNEL     =   int(config.get('LPS', 'LPS_SPI_CHANNEL'))
LPS_SPI_FREQUENCY   =   int(config.get('LPS', 'LPS_SPI_FREQUENCY'))

trials      =   int(config.get('experiment-parameters', 'trials'))       #trials
duration    =   int(config.get('experiment-parameters', 'duration'))     #seconds
pulsewidth  = float(config.get('experiment-parameters', 'pulsewidth'))   #seconds
samplerate  = float(config.get('experiment-parameters', 'samplerate'))   #hz

client_dir     = config.get('paths', 'client_dir')
client_log_dir = config.get('paths', 'client_log_dir')
client_file    = config.get('files', 'client_file')
log_file       = config.get('files', 'log_file')

broadcast_port = int(config.get('ports', 'broadcast_port'))

include_MOX        = config.getboolean('include-sensor-types', 'MOX')
include_press_temp = config.getboolean('include-sensor-types', 'press/temp')

channel  = int(config.get('pulser', 'channel'))
port     = config.get('pulser', 'port')
baudrate = int(config.get('pulser', 'baudrate'))
parity   = config.get('pulser', 'parity')
stopbits = config.get('pulser', 'stopbits')
bytesize = config.get('pulser', 'bytesize')
voltage  = int(config.get('pulser', 'voltage'))

sb = lib.sensor_board.SENSOR_BOARD(LED1_PIN, LED2_PIN, TX0_PIN, TX1_PIN)
sb.ledAct(1,0) # turn them both off to start
sb.ledAct(2,0)

p = lib.TB_pulser.pulser(channel, port, baudrate, parity, stopbits, bytesize)

def pulser_thread(tx_pattern, pulsewidth, tx_time_log):
	start_time = time.time()
	for i in range(len(tx_pattern)):
		current_time = time.time()
		tx_time_log[i] = (current_time - start_time)
		p.setVoltage(tx_pattern[i] * voltage) # set voltage to bits * voltage
		while time.time() - start_time < (i+1)*pulsewidth:
			pass
	p.setOutput("OFF")
	p.closePort()
	print("Transfer completed")
	print('tx time log: ' + str(tx_time_log))

#== Setup ======================================================================
print('\n\n\n') # for logfile
print(time.asctime(time.localtime(time.time())))

# set up adc and dac
ads = lib.pyads1256.ADS1256()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

# turn heater on for duration of experiment
dac = lib.pydac8532.DAC8532(DAC_SPI_CHANNEL, DAC_SPI_FREQUENCY, DAC_CS_PIN)
dac.SendDACAValue(DAC_voltage_percent * 2**16 - 1)

# set up pressure sensors - if you don't use all of them, you should still set all
#    of the pins as output and high
all_cs = [PRESS0_PIN, PRESS1_PIN, PRESS2_PIN, PRESS3_PIN, PRESS4_PIN, PRESS5_PIN, PRESS6_PIN, PRESS7_PIN]
for cs in all_cs:
	wp.pinMode(cs, wp.OUTPUT)
	wp.digitalWrite(cs, wp.HIGH)
lps = []
for index in range(len(all_cs)):
	lps.append(lib.pylps22hb.LPS22HB(LPS_SPI_CHANNEL, LPS_SPI_FREQUENCY, all_cs[index]))
	time.sleep(.05)
	lps[index].Boot() # wake up the sensors

# pulsing queue
pulseq = Queue()

# set up socket and options
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(('', broadcast_port))

# initialize variables
outstring = ''
chunk_num = 0
data_len = 0
log = {}
elapsed = []
elapsed_cycle = []
elapsed_cycle_quick = []
channels = 8 # change for other boards

sel_list = [[ads.MUX_AIN1, ads.MUX_AINCOM], [ads.MUX_AIN2, ads.MUX_AINCOM],
			[ads.MUX_AIN5, ads.MUX_AINCOM], [ads.MUX_AIN6, ads.MUX_AINCOM],
			[ads.MUX_AIN0, ads.MUX_AINCOM], [ads.MUX_AIN3, ads.MUX_AINCOM],
			[ads.MUX_AIN4, ads.MUX_AINCOM], [ads.MUX_AIN7, ads.MUX_AINCOM]]

# open the txpattern if it was sent (which it would be if this is a transmitter)
try:
	with open(client_log_dir + '/txpattern.pickle', 'rb') as f:
		tx_message = pickle.load(f)
	tx_pattern = np.array([int(n) for n in tx_message.split()])
	print('tx recieved')
	print(tx_pattern)
except Exception as e:
	print(e)
	tx_pattern = 'None'

#== Listen for commands ========================================================
print('Listening for broadcasts...')
sb.ledAct(1,1) # turn on LED 1
end_flag = False
while not end_flag:
	try:
		# get commands
		message, address = s.recvfrom(8192)
		commands = message.split()
		print(commands)

		if commands[0] == b'collect':
			sb.ledAct(2,2,4) # blink LED 2 at 4 Hz
			sample_count =   int(commands[1])
			samplerate   = float(commands[2])
			pulsewidth   = float(commands[3])
			period     = 1/samplerate

            # init array to store data
			mox_data   = np.zeros([sample_count, channels], dtype='int32')
			temp_data  = np.zeros([sample_count, channels], dtype='float32')
			press_data = np.zeros([sample_count, channels], dtype='float32')

		# start thread to generate pattern
		if tx_pattern != 'None':
			p.openPort()    # open communication port
			p.setVoltage(0) # set voltage and current to 0V and 1A
			p.setCurrent(1)
			p.setOutput("ON")
			tx_time_log = np.zeros([len(tx_pattern)], dtype='float32')
			t = threading.Thread(target=pulser_thread, args=(tx_pattern, pulsewidth, tx_time_log))
			if not t.isAlive():
				t.start()
				print('started pulser')

			rx_time_log = np.zeros([sample_count], dtype='float32')
			trial_start_time = time.time()
			for i in range(sample_count):
				sample_start_time = time.time()
				rx_time_log[i] = (sample_start_time - trial_start_time)
				# collect samples from feach sensor on board
				if include_MOX:
					sam_1 = ads.getADCsample(ads.MUX_AIN1, ads.MUX_AINCOM)
					sam_2 = ads.getADCsample(ads.MUX_AIN2, ads.MUX_AINCOM)
					sam_3 = ads.getADCsample(ads.MUX_AIN5, ads.MUX_AINCOM)
					sam_4 = ads.getADCsample(ads.MUX_AIN6, ads.MUX_AINCOM)
					sam_5 = ads.getADCsample(ads.MUX_AIN0, ads.MUX_AINCOM)
					sam_6 = ads.getADCsample(ads.MUX_AIN3, ads.MUX_AINCOM)
					sam_7 = ads.getADCsample(ads.MUX_AIN4, ads.MUX_AINCOM)
					sam_8 = ads.getADCsample(ads.MUX_AIN7, ads.MUX_AINCOM)

					mox_data[i] = np.array([sam_1,sam_2,sam_3,sam_4,sam_5,sam_6,sam_7,sam_8], dtype='int32')

				if include_press_temp:
					for index in range(len(lps)):
						lps[index].OneShot()
						time.sleep(.001)
						temp_data[i][index]  = lps[index].ReadTemp()
						press_data[i][index] = lps[index].ReadPress()
					# for index in range(4,len(lps)):
					# 	lps[index].ChipSelect()   # select all chips
					# lps[0].OneShot()              # sample concurently
					# time.sleep(.001)
					# for index in range(4,len(lps)): # read concurrent samples sequentially
					# 	temp_data[i][index]  = lps[index].ReadTemp()
					# 	press_data[i][index] = lps[index].ReadPress()
					# 	lps[index].ChipRelease()

				sample_end_time = time.time()
				while time.time() - trial_start_time < (i+1)*period:
					pass
			trial_end_time = time.time()
## :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :)
				# start_time = time.time()
				# samps = ads.CycleReadADC(sel_list)
				# cycle_time = time.time() - start_time
				# print('Cycle Method:')
				# print('elapsed time: ' + str(cycle_time))
				# print('Data: ' + str(samps))
				# elapsed_cycle.append(cycle_time)
				#
				# ads.ChipSelect()
				# start_time = time.time()
				# samps = ads.CycleReadADC_quick(sel_list)
				# cycle_time = time.time() - start_time
				# print('Cycle Quick Method:')
				# print('elapsed time: ' + str(cycle_time))
				# print('Data: ' + str(samps))
				# ads.ChipRelease()
				# elapsed_cycle_quick.append(cycle_time)
## :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :) :)
				#time.sleep(period-elapsed_time)


			# print('average elapsed cycle time:       ' + str(sum(elapsed_cycle)/float(len(elapsed_cycle))))
			# print('average elapsed cycle quick time: ' + str(sum(elapsed_cycle_quick)/float(len(elapsed_cycle_quick))))

			# add info to logfile
			print("adding to log")
			log['MOX Data']         = mox_data
			log['Temperature Data'] = temp_data
			log['Pressure Data']    = press_data
			log['Start Time']       = trial_start_time
			log['End Time']         = trial_end_time
			log['Duration']         = trial_end_time - trial_start_time
			#log['Average Elapsed']  = sum(elapsed)/float(len(elapsed))
			log['TxPattern']        = tx_pattern
			log['Tx Time Log']      = tx_time_log
			log['Rx Time Log']      = rx_time_log

			# serialize data to be sent over network
			print(log)
			with open('/home/pi/TruffleBot/log/sendfile.pickle','wb') as f:
				pickle.dump(log,f)
				print('pickled!')

			# send the end flag to trigger data collection on host
			s.sendto('end_flag'.encode('utf-8'),address)
			pulseq.put('stop')
			print('end')
			end_flag=True
			sb.ledAct(2,0) # turn off LED 2

	except Exception as e:
			print(e)
sb.ledAct(1,0)
