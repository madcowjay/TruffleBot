"""
Updated 2018/05/03
  -Implemented config files for experiment parameters and IPs of clients

  -kill_processes now takes a client file as an argument
	 and is called at the beginning of the program to clean up
	 any running copies that might be leftover from crashes.
  -moved ip_list to host.py and made it an argument to PiManager
  -Unthreaded listener
  -Python3 only supported now
  -datavisualiztion removed
  -board numbers removed (use serial number instead)
									-JW
"""

import os, sys, platform, time, textwrap, threading
import socket, pickle, tempfile, configparser, ast
import numpy as np
from   optparse import OptionParser
from   lib.getch import *

# Function to get keyboard interrupts (cross-platform)
def input_thread(stop_event):
	c = getch()
	if c == 'q':
		print('uitting...')
		stop_event.set()

#== Setup ======================================================================
# Process command line arguments
usage = 'python3 host.py [OPTION]...'
parser = OptionParser(usage)
parser.add_option('-d','--debug',action='store_true',dest='debugFlag',help='display debug messages while running',default=False)
parser.add_option('-r','--remote-install',action='store_true',dest='remoteInstallFlag',help='install all necessary files on clients',default=False)
parser.add_option('-c','--config-file',dest='configfile',help='use the indicated configuration file, if not invoked, default.cfg is used',default='default.cfg')
(options, args) = parser.parse_args()
configFilePath = options.configfile
if options.debugFlag: os.environ['DEBUG'] = 'True'

# Load these after DEBUG status has been determined
import lib.savefile
import lib.connect

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

# Set parameters
trials      =   int(config.get('experiment-parameters', 'trials'))   #trials
duration    =   int(config.get('experiment-parameters', 'duration')) #seconds
padding     =   int(config.get('experiment-parameters', 'padding'))  #pulses of silence at beginning and end
pulsewidth  = float(config.get('experiment-parameters', 'pulsewidth')) #seconds
samplerate  = float(config.get('experiment-parameters', 'samplerate')) #hz

print('Starting experiment with the following parameters:')
print('\ttrials:       {} runs'.format(trials))
print('\tduration:     {} seconds per run'.format(duration))
print('\tpadding:      {} seconds'.format(padding))
print('\tpulsewidth    {} second'.format(pulsewidth))
print('\tsamplerate:   {} Hz'.format(samplerate))

ip_list = ast.literal_eval(config.get('ip-addresses', 'ip_list'))
print('\tip addresses: ' , end = '')
print(*ip_list, sep = ', ')

try:
	transmit_ip = ast.literal_eval(config.get('ip-addresses', 'transmit_ip'))
	print('\ttransmitter:  {}'.format(transmit_ip))
except:
	print('\tno transmitter')

broadcast_port = int(config.get('ports', 'broadcast_port'))
print('\tbrdcst port:  {}'.format(broadcast_port))

randomFlag = int(config.get('message', 'random'))
print('\trandom:       ' + str(randomFlag))
if not randomFlag:
	message_array = ast.literal_eval(config.get('message', 'message_array'))

if options.remoteInstallFlag:
	print('TODO')
	# sync files, run client on the remote machines
#host_dir='pi_utils'
host_dir    = config.get('paths', 'host_dir')
client_dir  = config.get('paths', 'client_dir')
log_dir     = config.get('paths', 'log_dir')
client_file = config.get('files', 'client_file')
log_file    = config.get('files', 'log_file')

username    = config.get('client-login', 'username')
password    = config.get('client-login', 'password')

# PiManager sends commands to all Pis
pm = lib.connect.PiManager(client_dir, ip_list)
pm.kill_processes(client_file)

#set up instances of Experiment and Log classes, set start time for log
pe = lib.savefile.PlumeExperiment()
pl = lib.savefile.PlumeLog(log_dir)
pe.set_parameter('Comment', 'trials with raspberry pi collector boards and humidifier trasnmitter')

#set up socket
dest = ('<broadcast>', broadcast_port)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(5.0)

#get identifying dictionaries from pm
ip_serial = pm.identifpi()
print('\tboard list:   ' + str(ip_serial))

# kernel_time = 4 # in seconds. PN code will repeat after this much time.

#add transmitter
#TODO - name transmitter by ip or serial
pe.add_transmitter('Trasnmitter 1')
#transmit_pi = 2#board number for transmitter

#== Start Client ===============================================================
pm.run_script(client_file, log_file, broadcast_port)
# pm.exec_command('sudo strace -p $(pgrep python) -o strace.txt')
time.sleep(4) # wait for remote programs to start

#== Transmit ===================================================================
# generate transmit pattern, add to log, and send to transmitter board
# message must be a np array to be saved in hdf5 correctly
if randomFlag:
	# fill message with randomly generated bit pattern
	message_len = int(duration / pulsewidth) # number of bits in message
	message = np.zeros(message_len, dtype='uint8')
	message = np.asarray([np.random.choice([0,1]) for n in range(len(message))])
else:
	message = np.asarray(message_array)

pad        = np.zeros(padding,     dtype='uint8')
tx_pattern = np.concatenate([pad, message, pad])

# This section upsamples the message and shortens the pulses to enure that
#   the falling edge after a 1 is completed before the next 0 starts
# for n, bit in enumerate(message):
#     for i in range(tx_pattern_bit_len):
#         if bit==1:
#             tx_pattern[n*tx_pattern_bit_len + i] = 1
#             break
#         else:
#             tx_pattern[n*tx_pattern_bit_len + i] = 0

#tweak the message into a form that can be saved and reconstructed easily
#    this essentially translates the message into an array constrained by
#    the samplerate of the Collectors
tx_pattern_upsampled = tx_pattern.repeat(pulsewidth * samplerate)
# element_len = int(pulsewidth * samplerate)
# for element in message:
#     for n in range(element_len):
#         tx_pattern_upsampled.append(element)

print('\tmessage:              ' + str(message))
print('\ttx_pattern:           ' + str(tx_pattern))
print('\ttx_pattern_upsampled: ' + str(tx_pattern_upsampled))
print('\tshape of upsampled:   ' + str(tx_pattern_upsampled.shape))

pe.add_data('Trasnmitter 1', message,  datatype='Message')
pe.add_data('Trasnmitter 1', tx_pattern_upsampled, datatype='Tx Pattern')
pe.add_transmitter_parameter('Trasnmitter 1', 'Pulsewidth', pulsewidth)
pe.add_transmitter_parameter('Trasnmitter 1', 'Padding', padding)
#pe.add_transmitter_parameter('Trasnmitter 1', 'Bitrate', bitrate)

with open('log/txpattern.pickle','wb') as f:
	tx_string = ' '.join([str(n) for n in tx_pattern])
	pickle.dump(tx_string, f, protocol=2)
pm.upload_file('log/txpattern.pickle', addr=transmit_ip)
time.sleep(1)

#== Main Loop ==================================================================
for trial in range(trials): # number of times to do experiment
	print('\n*** trial %s started ***' %(trial))
	pe.set_start_time()

	#manage the pis
	#pm.conditional_dir_sync()
	#pm.upload_file(client_file)
	#pm.exec_command('sudo pkill python')

	#sanitize client-directory
	pm.exec_commands(['rm %s/sendfile.pickle'%pm.client_dir,'rm %s/txpattern.pickle'%pm.client_dir])

	# add collectors to experiment
	for ip in pm.ip_list:
		pe.add_collector('Board #'+str(ip_serial[ip]), samplerate=samplerate)
		pe.add_collector_parameter('Board #'+str(ip_serial[ip]),'Serial Number',str(ip_serial[ip]))
		pe.add_collector_parameter('Board #'+str(ip_serial[ip]),'Type','MOX')

	#===========================================================================
	#send command to the client to collect data
	sample_count = len(tx_pattern)*pulsewidth*samplerate
	command = 'collect %s %s %s'%(sample_count, samplerate, pulsewidth)
	s.sendto(command.encode('utf-8'), dest)
	print('sending command: ' + command)

	#start lsitening until all responses are in
	start_time = time.time()
	print(time.strftime('%H:%M:%S',time.localtime(start_time)) + ' : listener started, press "q" to quit')

	t_stop = threading.Event()
	t = threading.Thread(target=input_thread, args=(t_stop,))
	t.start()
	s.settimeout(1)#shorter timeout for recieving to work in long loop+
	responses_received = 0
	while responses_received < len(ip_list) and not ( t_stop.is_set() ):
		curr_time = time.time() - start_time
		try:
			(buf, address) = s.recvfrom(8192)
			response = buf.decode('utf-8')
			if response!='unknown':
				if response == 'end_flag':
					responses_received += 1
					print('    {0:>4} : received response from: {1}'.format(int(curr_time), address))
					print('    {0:>4} : total responses: {1}'.format(int(curr_time), responses_received))
				else: pass
		except Exception as e:
			print('    {0:>4} : {1}'.format(int(curr_time), e))
	print('    {0:>4} : listener ended'.format(int(curr_time)))

	#end experiment
	pe.set_end_time()

	if not t_stop.is_set():
		#== get data from pis, reassemble data =================================
		data = {}
		for ip in pm.ip_list:
			pm.ssh.connect(ip, username=username, password=password)
			sftp = pm.ssh.open_sftp()
			with tempfile.TemporaryFile() as fp:
				sftp.getfo('/home/pi/TruffleBot/log/sendfile.pickle',fp)
				fp.seek(0)
				#log = pickle.load(fp,encoding='latin1') #incompatibility of np arrays between python 2(clients) and 3(host) so use latin1 encoding
				#log =
				data[ip] = pickle.load(fp)

		#save data in hdf5 file, scale the data
		for board in pe.collectors.keys():
			print(board)
			serial = board[7:]
			ip = ip_serial.inv[serial]
			# ret_data = data[ip]['Data']
			# savedata = ret_data.astype('float32')
			savedata = data[ip]['Data'].astype('float32')
			print(savedata)
			print(type(savedata))
			savedata1 = data[ip]['Data']
			print(savedata1)
			print(type(savedata1))
			#scale data to reference 0 = 2**23
			for n in np.nditer(savedata, op_flags=['readwrite']):
				 n[...] = np.mod(n-2**23,2**24)/2**24
			print('    >data :\n' + textwrap.indent(str(savedata), '          '))
			pe.add_data(board, savedata)
			pe.add_collector_parameter(board,'End Time',data[ip]['End Time'])
			print('    >end time: %s, avg elapse: %s'%(data[ip]['End Time'],data[ip]['Average Elapsed']))

			time_log = data[ip]['Time Log']
			print(time_log)
			print(type(time_log))
			pe.add_data(board, time_log)

		#=======================================================================


		# add number of trasnmitters, collectors to experiment parameters
		pe.set_parameter('# Collectors',responses_received)
		pe.set_parameter('# Trasnmitters',1)
		pe.set_parameter('Wind Speed (m/s)', 2.1)

		# save log
		try:
			log_path, date_time = pl.save_file(pe)
		except Exception as e:
			print('error'+str(e))

		#visualize returned data
		# logname = log_path.split('/')[1]
		# print('visualizing')
		# dv.visualize(logname)

	#== Cleanup ================================================================
	print('Cleaning up...')
	#kill processes on remote machines
	pm.kill_processes(client_file)
	print('press "q" to quit')
