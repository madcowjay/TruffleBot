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
import lib.savefile
import lib.connect

config = configparser.RawConfigParser()
config.read(config_file)

print('\nLoading config file: ' + config_file + '\n')

# set attributes
trials      =   int(config.get('experiment-parameters', 'trials'))     # trials
duration    =   int(config.get('experiment-parameters', 'duration'))   # seconds
padding     =   int(config.get('experiment-parameters', 'padding'))    # pulses of silence at beginning and end
pulsewidth  = float(config.get('experiment-parameters', 'pulsewidth')) # seconds
samplerate  = float(config.get('experiment-parameters', 'samplerate')) # hz

print('Starting experiment with the following attributes:')
print('\ttrials:       {} runs'.format(trials))
print('\tduration:     {} seconds per run'.format(duration))
print('\tpadding:      {} seconds'.format(padding))
print('\tpulsewidth    {} second'.format(pulsewidth))
print('\tsamplerate:   {} Hz'.format(samplerate))

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
	pe.set_attribute(key, experiment_attributes[key])

collector_ip_list = ast.literal_eval(config.get('ip-addresses', 'collector_ip_list'))
print('\tcollector ip addresses:   ' , end = '')
print(*collector_ip_list, sep = ', ')

# determine which pis are transmitters if any
try:
	transmitter_ip_list = ast.literal_eval(config.get('ip-addresses', 'transmitter_ip_list'))
	print('\ttransmitter ip addresses: ' , end = '')
	print(*transmitter_ip_list, sep = ', ')
	for transmitter in transmitter_ip_list:
		pe.add_transmitter(transmitter)
except:
	print('\tno transmitters indicated in configuration file')

broadcast_port = int(config.get('ports', 'broadcast_port'))
print('\tbrdcst port:  {}'.format(broadcast_port))

if options.remoteInstallFlag:
	print('TODO')

randomFlag = config.getboolean('message', 'random')
print('\trandom:       ' + str(randomFlag))
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

# set up socket for messaging
dest = ('<broadcast>', broadcast_port)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(5.0)

# get identifying dictionaries from pm
ip_serial = pm.identifpi()
print('\tboard list:   ' + str(ip_serial))

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

pad        = np.zeros(padding,     dtype='uint8')
tx_pattern = np.concatenate([pad, message, pad])
tx_pattern_upsampled = tx_pattern.repeat(pulsewidth * samplerate)

print('\tmessage:              ' + str(message))
print('\ttx_pattern:           ' + str(tx_pattern))
print('\ttx_pattern_upsampled: ' + str(tx_pattern_upsampled))
print('')

with open(host_log_dir + '/txpattern.pickle', 'wb') as f:
	tx_string = ' '.join([str(n) for n in tx_pattern])
	pickle.dump(tx_string, f, protocol=2)
	
for transmitter in transmitter_ip_list:
	pm.upload_file(host_log_dir + '/txpattern.pickle', addr=transmitter)
time.sleep(1)

#== Start Client ===============================================================
pm.run_script(client_file)
time.sleep(3) # wait for remote programs to start

#== Main Loop ==================================================================
for trial in range(trials): # number of times to do experiment
	print('\n*** trial %s started ***' %(trial))
	pe.set_start_time()

	# add collectors to experiment
	for ip in pm.ip_list:
		pe.add_collector(ip)
		pe.add_collector_element(ip,'Serial Number',str(ip_serial[ip]))

	#===========================================================================
	# send command to the client to collect data
	sample_count = len(tx_pattern)*pulsewidth*samplerate
	command = 'collect %s %s %s'%(sample_count, samplerate, pulsewidth)
	s.sendto(command.encode('utf-8'), dest)
	print('sending command: ' + command)

	# start lsitening until all responses are in
	start_time = time.time()
	print(time.strftime('%H:%M:%S',time.localtime(start_time)) + ' : listener started, press "q" to quit')

	t_stop = threading.Event()
	t = threading.Thread(target=input_thread, args=(t_stop,))
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
	pe.set_end_time()

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
		for ip in pe.collectors.keys():
			print('ip: {}'.format(ip))
			serial = ip[7:]
			temp_data  = data[ip]['Temperature Data']
			press_data = data[ip]['Pressure Data']
			savedata = data[ip]['MOX Data'].astype('float32')
			# scale data to reference 0 = 2**23
			for n in np.nditer(savedata, op_flags=['readwrite']):
				 n[...] = np.mod(n-2**23,2**24)/2**24

			print('    >data :\n' + textwrap.indent(str(savedata), '          '))
			print('    >end time: %s, avg elapse: %s'%(data[ip]['End Time'],data[ip]['Average Elapsed']))

			pe.add_collector_element(ip, 'MOX Data', savedata)
			pe.add_collector_element(ip, 'End Time',data[ip]['End Time'])
			pe.add_collector_element(ip, 'Temperature Data', temp_data)
			pe.add_collector_element(ip, 'Pressure Data', press_data)

			if ip in pe.trasnmitters.keys():
				tx_time_log = data[ip]['Tx Time Log']
				pe.add_transmitter_element(ip, 'Time Log', tx_time_log)
				pe.add_transmitter_element(ip, 'Message', message)
				pe.add_transmitter_element(ip, 'Tx Pattern', tx_pattern_upsampled)
				pe.add_transmitter_element(ip, 'Pulsewidth', pulsewidth)
				pe.add_transmitter_element(ip, 'Padding', padding)
		#=======================================================================

		# add number of trasnmitters, collectors to experiment attributes
		pe.set_attribute('# Collectors', responses_received)
		pe.set_attribute('# Trasnmitters', len(transmitter_ip_list))

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

	#== Cleanup ================================================================
	print('Cleaning up...')
	# kill processes on remote machines
	pm.kill_processes(client_file)
	print('press "q" to quit')
