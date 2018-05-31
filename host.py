import os, sys, platform, time, textwrap, threading
import socket, pickle, tempfile, configparser, ast
import numpy as np
from   optparse import OptionParser
from   lib.getch import *

# function to get keyboard interrupts (cross-platform)
def input_thread(stop_event):
	c = getch()
	if c == 'q':
		print('uitting...')
		stop_event.set()

#== Setup ======================================================================
# process command line arguments
usage = 'python3 host.py [OPTION]...'
parser = OptionParser(usage)
parser.add_option('-d','--debug',action='store_true',dest='debugFlag',help='display debug messages while running',default=False)
parser.add_option('-r','--remote-install',action='store_true',dest='remoteInstallFlag',help='install all necessary files on clients',default=False)
parser.add_option('-c','--config-file',dest='configfile',help='use the indicated configuration file, if not invoked, default.cfg is used',default='default.cfg')
(options, args) = parser.parse_args()
config_file = options.configfile
if options.debugFlag: os.environ['DEBUG'] = 'True'

# load these after DEBUG status has been determined
from   lib.debug_print import *
import lib.savefile
import lib.connect

config = configparser.RawConfigParser()
config.read(config_file)

print('\nLoading config file: ' + config_file + '\n')

# set attributes
voltage     =   int(config.get('pulser', 'voltage'))
trials      =   int(config.get('experiment-parameters', 'trials'))     # trials
duration    =   int(config.get('experiment-parameters', 'duration'))   # seconds
prepadding  =   int(config.get('experiment-parameters', 'padding'))    # pulses of silence at beginning end
postpadding =   int(config.get('experiment-parameters', 'padding'))    # pulses of silence at the end
pulsewidth  = float(config.get('experiment-parameters', 'pulsewidth')) # seconds
samplerate  =   int(config.get('experiment-parameters', 'samplerate')) # hz

print('Starting experiment with the following attributes:')
print('\t**Pulser VOLTAGE**:       {} V'.format(voltage))
print('\ttrials:                   {} runs'.format(trials))
print('\tduration:                 {} seconds per run'.format(duration))
print('\tprepadding:               {} seconds'.format(prepadding))
print('\tpostpadding:              {} seconds'.format(postpadding))
print('\tpulsewidth                {} second'.format(pulsewidth))
print('\tsamplerate:               {} Hz'.format(samplerate))

client_dir     = config.get('paths', 'client_dir')
host_log_dir   = config.get('paths', 'host_log_dir')
client_log_dir = config.get('paths', 'client_log_dir')
client_file    = config.get('files', 'client_file')
log_file       = config.get('files', 'log_file')

# set up instances of Experiment and Log classes, set start time for log
pe = lib.savefile.PlumeExperiment()
pl = lib.savefile.PlumeLog(host_log_dir)
experiment_attributes = ast.literal_eval(config.get('hdf5', 'experiment-attributes'))
for key in experiment_attributes:
	pe.add_attribute_to_experiment(key, experiment_attributes[key])

collector_ip_list = ast.literal_eval(config.get('ip-addresses', 'collector_ip_list'))
print('\tcollector ip addresses:   ', end = '')
print(*collector_ip_list, sep = ', ')

include_MOX        = config.getboolean('include-sensor-types', 'MOX')
include_press_temp = config.getboolean('include-sensor-types', 'press/temp')
print('\tinclude MOX:              {}'.format(include_MOX))
print('\tinclude press/temp:       {}'.format(include_press_temp))

broadcast_port = int(config.get('ports', 'broadcast_port'))
print('\tbrdcst port:              {}'.format(broadcast_port))

if options.remoteInstallFlag:
	print('TODO') #TODO

randomFlag = config.getboolean('message', 'random')
print('\trandom:                   {}'.format(randomFlag))
if not randomFlag:
	message_array = ast.literal_eval(config.get('message', 'message_array'))

username    = config.get('client-login', 'username')
password    = config.get('client-login', 'password')

# PiManager sends commands to all Pis
pm = lib.connect.PiManager(client_dir, client_log_dir, config_file, log_file, collector_ip_list, username, password)
# make sure there are no lingering copies of the program running (from crashes)
pm.kill_processes(client_file)
# upload current config file to client
pm.upload_file(config_file)
# sanitize client by removing previous pickles
pm.exec_commands(['rm %s/sendfile.pickle'%client_log_dir, 'rm %s/txpattern.pickle'%pm.client_log_dir])

# get identifying dictionaries from pm
ip_serial = pm.identifpi()
print('\tboard list:               ' + str(ip_serial))

# determine which pis are transmitters if any
try:
	transmitter_ip_list = ast.literal_eval(config.get('ip-addresses', 'transmitter_ip_list'))
	print('\ttransmitter ip addresses: ' , end = '')
	print(*transmitter_ip_list, sep = ', ')
except:
	print('\tno transmitters indicated in configuration file')

# set up socket for messaging
dest = ('<broadcast>', broadcast_port)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(5.0)

#== Transmitter Handling =======================================================
# generate transmit pattern, add to log, and send to transmitter board
# message must be a np array to be saved in hdf5 correctly
if randomFlag:
	# fill message with randomly generated bit pattern
	message_len = int(duration / pulsewidth) # number of bits in message
	message = np.zeros(message_len, dtype='uint8')
	message = np.asarray([np.random.choice([0,1]) for n in range(len(message))])
else:
	message = np.asarray(message_array)

prepad     = np.zeros(prepadding,  dtype='uint8')
postpad    = np.zeros(postpadding, dtype='uint8')
tx_pattern = np.concatenate([prepad, message, postpad])

print('\tmessage:                  ' + str(message))
print('\ttx_pattern:               ' + str(tx_pattern))
print('\ttx_pattern_upsampled:     ' + str(tx_pattern_upsampled))
print('')

with open(host_log_dir + '/txpattern.pickle', 'wb') as f:
	tx_string = ' '.join([str(n) for n in tx_pattern])
	pickle.dump(tx_string, f, protocol=2)

for transmitter in transmitter_ip_list:
	pm.upload_file(host_log_dir + '/txpattern.pickle', addr=transmitter)
time.sleep(1)

pe.set_experiment_start_time()
t_stop = threading.Event()
t = threading.Thread(target=input_thread, args=(t_stop,))

#== Main Loop ==================================================================
for trial in range(1, trials+1): # MATLAB indexed
	print('\n*** trial %s started ***' %(trial))
	trial_name = 'Trial #{:0{}}'.format(trial, len(str(trials+1)))
	pe.add_trial_to_experiment(trial_name)
	pe.set_trial_start_time(trial_name)

	# start clients
	pm.run_script(client_file)
	time.sleep(3) # wait for remote programs to start

	for ip in pm.ip_list:
		pe.add_collector_to_trial(trial_name, ip, str(ip_serial[ip]))

	for transmitter in transmitter_ip_list:
		pe.add_transmitter_to_trial(trial_name, transmitter, str(ip_serial[transmitter]))

	#===========================================================================
	# send command to the client to collect data
	sample_count = int(len(tx_pattern)*pulsewidth*samplerate)
	command = 'collect {} {} {}'.format(sample_count, samplerate, pulsewidth)
	s.sendto(command.encode('utf-8'), dest)
	print('sending command: ' + command)

	# start lsitening until all responses are in
	start_time = time.time()
	print(time.strftime('%H:%M:%S',time.localtime(start_time)) + ' : listener started, press "q" to quit')

	if not t.isAlive():
		t.start()

	s.settimeout(1) # shorter timeout for recieving to work in long loop+
	responses_received = 0
	while responses_received < len(collector_ip_list) and not ( t_stop.is_set() ):
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

	# end experiment
	pe.set_trial_end_time(trial_name)

	if not t_stop.is_set():
		#== Get data from pis, reassemble data =================================
		data = {}
		for ip in pm.ip_list:
			pm.ssh.connect(ip, username=username, password=password)
			sftp = pm.ssh.open_sftp()
			with tempfile.TemporaryFile() as fp:
				sftp.getfo(client_log_dir + '/sendfile.pickle', fp)
				fp.seek(0)
				data[ip] = pickle.load(fp)

		# save data in hdf5 file, scale the data
		for ip in pe.trials[trial_name]['collectors'].keys():
			debug_print('ip: {}'.format(ip))
			serial = ip[7:]
			rx_time_log = data[ip]['Rx Time Log']
			temp_data   = data[ip]['Temperature Data']
			press_data  = data[ip]['Pressure Data']
			savedata    = data[ip]['MOX Data'].astype('float32')
			# scale data to reference 0 = 2**23
			for n in np.nditer(savedata, op_flags=['readwrite']):
				 n[...] = np.mod(n-2**23,2**24)/2**24

			debug_print('    >MOX data :\n' + textwrap.indent(str(savedata), '          '))
			#debug_print('    >end time: %s, avg elapse: %s'%(data[ip]['End Time'],data[ip]['Average Elapsed']))

			pe.add_element_to_collector(trial_name, ip, 'MOX Data', savedata)
			pe.add_element_to_collector(trial_name, ip, 'End Time', data[ip]['End Time'])
			pe.add_element_to_collector(trial_name, ip, 'Temperature Data', temp_data)
			pe.add_element_to_collector(trial_name, ip, 'Pressure Data', press_data)
			pe.add_element_to_collector(trial_name, ip, 'Rx Time Log', rx_time_log)

			if ip in pe.trials[trial_name]['transmitters'].keys():
				tx_time_log = data[ip]['Tx Time Log']
				pe.add_element_to_transmitter(trial_name, ip, 'Tx Time Log', tx_time_log)
				pe.add_element_to_transmitter(trial_name, ip, 'Message', message)
				pe.add_element_to_transmitter(trial_name, ip, 'Tx Pattern', tx_pattern)
				pe.add_element_to_transmitter(trial_name, ip, 'Pulsewidth', pulsewidth)
				pe.add_element_to_transmitter(trial_name, ip, 'Padding', padding)

#== Trials Done ================================================================
pe.set_experiment_end_time()
pe.add_attribute_to_experiment('# Collectors', responses_received)
pe.add_attribute_to_experiment('# Transmitters', len(transmitter_ip_list))
pe.add_attribute_to_experiment('Include MOX', include_MOX)
pe.add_attribute_to_experiment('Include Press/Temp', include_press_temp)

# save log
try:
	log_path, date_time = pl.save_file(pe)
except Exception as e:
	print('error: ' + str(e) )
	print (e.value)

# # visualize returned data
# logname = log_path.split('/')[1]
# print('visualizing')
# dv.visualize(logname)

print('Cleaning up...')
# kill processes on remote machines
pm.kill_processes(client_file)
print('press "q" to quit')
