"""
Updated 2018/04/30
  -Unthreaded listener
                                    -JW
Updated 2018/04/25
  -Python3 only supported now
  -datavisualiztion removed
  -board numbers removed (use serial number instead)
                                    -JW
"""

import os, sys, platform, time, textwrap
import socket, pickle, tempfile
import numpy as np

import lib.savefile
import lib.connect

#==========================================================================================================
# sync files, run client on the remote machines
#host_project_dir='pi_utils'
#host_project_dir='/home/pi/TruffleBot'
client_project_dir='/home/pi/TruffleBot'
client_file = 'client.py'

pm = lib.connect.PiManager(client_project_dir)

# #dictionary to associate serial number with board number
# boardlookup = { '00000000d7ef3031' : 1,
#                 '0000000068c200c3' : 2
#               }

# # dictionary to associate board number with serial number
# IDlookup = dict((v,k) for k, v in boardlookup.items())

#set up instances of Experiment and Log classes, set start time for log
pe = lib.savefile.PlumeExperiment()
pl = lib.savefile.PlumeLog(logdirname='log')
pe.set_parameter('Comment', 'trials with raspberry pi sensor boards and humidifier source')

#set up socket
dest = ('<broadcast>', 5000)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(5.0)

#experiment parameters
iterations = 2 #trials
duration = 5 #seconds
samplerate = 2 #hz
padding = 0 #seconds of silence at beginning and end
num_samples = duration*samplerate+ 2*padding*samplerate
spacing = 1/samplerate

# #tx parameters
# message_time = duration # seconds
# bit_duration = 1 # width of each bit (seconds)
# bitrate = 1/bit_duration #hz
# pulse_duration = 1 #time that chemical is pulsed (seconds)
# num_bits = message_time*bit_duration
# # kernel_time = 4 # in seconds. PN code will repeat after this much time.
#
# #add transmitter
# pe.add_source('Source 1')
# transmit_pi = 2#board number for transmitter
#
# # create tx pattern to be pulsed
# message_len = int(message_time/bit_duration) #number of bits in message
# tx_len      = int(message_time/pulse_duration) # number of bits
# tx_bit_len  = int(bit_duration/pulse_duration)
#
# message = np.zeros(message_len, dtype='uint8')
# tx = np.zeros(tx_len, dtype='uint8')
#
# def gen_tx_pattern():
#     # message must be a np array to be saved in hdf5 correctly
#     # fill message with randomly generated bit pattern
#     message = np.asarray([np.random.choice([0,1]) for n in range(message_len)])
#     # message = np.asarray([1,0])
#
#     # add the ability to have pulse be shorter than bit length
#     for n, bit in enumerate(message):
#         for i in range(tx_bit_len):
#             if bit==1:
#                 tx[n*tx_bit_len +i] = 1
#                 break
#             else:
#                 tx[n*tx_bit_len +i] = 0
    #
    #
    # #tweak the message into a form that can be saved and reconstructed easily
    # #this essentially translates the message into an array constrained by the samplerate of the Sensors
    # msg_plot = []
    # element_len = int(pulse_duration*samplerate)
    # for element in message:
    #     for n in range(element_len):
    #         msg_plot.append(element)
    # msg_plot = np.pad(msg_plot,samplerate*padding,'constant',constant_values=0)
    # print(msg_plot)
    # print(msg_plot.shape)
    #
    # return message,tx,msg_plot

#==========================================================================================================
# main code
for trial in range(iterations): # number of times to do experiment
    # set start time of experiment
    print('\n*** trial %s started ***' %(trial))
    pe.set_start_time()

#============================================================================
    #manage the pis
    #pm.conditional_dir_sync()
    #pm.upload_file(client_file)
    # pm.exec_command('sudo pkill python')

    #sanitize client-directory
    pm.exec_commands(['rm %s/sendfile.pickle'%pm.client_project_dir,'rm %s/txpattern.pickle'%pm.client_project_dir])

    #get identifying dictionaries from pm
    ip_serial = pm.identifpi() #-JW
    print('board list: ' + str(ip_serial)) #-JW

#########################################################################
# # transmit section
#     # generate transmit pattern, add to log, and send to transmitter board
#     message, tx_pattern, msg_plot = gen_tx_pattern()
#
#     print(message)
#     print(tx_pattern)
#     pe.add_data('Source 1',message,datatype='Message')
#     pe.add_data('Source 1',msg_plot,datatype='Tx Pattern')
#     pe.add_source_parameter('Source 1','Pulse Duration',pulse_duration)
#     pe.add_source_parameter('Source 1', 'Padding', padding)
#     pe.add_source_parameter('Source 1', 'bitrate',bitrate)
#
#     with open('txpattern.pickle','wb') as f:
#         tx_string = ' '.join([str(n) for n in tx_pattern])
#         pickle.dump(tx_string,f, protocol=2)
#     transmit_addr = boardnum_ip[transmit_pi]
#     pm.upload_file('txpattern.pickle', addr=transmit_addr)
#     time.sleep(1)
#########################################################################

#============================================================================
    ## start client script
    pm.run_script(client_file,log_file='log.txt')
    # pm.exec_command('sudo strace -p $(pgrep python) -o strace.txt')
    time.sleep(3) # wait for remote programs to start

    # add sensors to experiment
    responses_requested = 0
    for ip in pm.ip_list:
        pe.add_sensor('Board #'+str(ip_serial[ip]),samplerate=samplerate)
        pe.add_sensor_parameter('Board #'+str(ip_serial[ip]),'Serial Number',str(ip_serial[ip]))
        pe.add_sensor_parameter('Board #'+str(ip_serial[ip]),'Type','MOX')
        responses_requested += 1

    #kill the program if no sensors respond
    if not responses_requested:
        print('There were no boards in the ip_list - Exiting')
        sys.exit()

    #==========================================================================================================

    #send command to the client to collect data
    pulse_duration = 1; #-JW
    command = 'collect %s %s %s %s'%(num_samples, spacing, pulse_duration, padding)
    s.sendto(command.encode('utf-8'), dest)
    print('sending command: ' + command)

    #start lsitening until all responses are in
    print("listener started")
    s.settimeout(1)#shorter timeout for recieving to work in long loop+
    responses_received = 0
    while responses_received < responses_requested:
        try:
            (buf, address) = s.recvfrom(8192)
            response = buf.decode('utf-8')
            if response!='unknown':
                if response == 'end_flag':
                    responses_received += 1
                    print('    >received response from : ' + str(address))
                    print('    >total responses: ' + str(responses_received))
                else: pass
        except Exception as e:
            print("    >" + str(e))
    print('listener ended')

    #end experiment
    pe.set_end_time()

    #==========================================================================================================

    # get data from pis, reassemble data
    data = {}
    sample_times = {}
    for ip in pm.ip_list:
        pm.ssh.connect(ip, username='pi', password='raspberryB1oE3')
        sftp = pm.ssh.open_sftp()
        with tempfile.TemporaryFile() as fp:
            sftp.getfo('/home/pi/TruffleBot/log/sendfile.pickle',fp)
            fp.seek(0)
            log = pickle.load(fp,encoding='latin1') #incompatibility of np arrays between python 2(clients) and 3(host) so use latin1 encoding
            data[ip] = log
        print('TxPattern: ' + str(data[ip]['TxPattern']))

    #save data in log file, scale the data
    for board in pe.sensors.keys():
        print(board)
        serial = board[7:]
        # print('  >board serial: ' + str(serial))
        ip = ip_serial.inv[serial]
        ret_data = data[ip]['Data']
        savedata = ret_data.astype('float32')
        #scale data to reference 0 = 2**23
        for n in np.nditer(savedata, op_flags=['readwrite']):
             n[...] = np.mod(n-2**23,2**24)/2**24
        print('    >data :\n' + textwrap.indent(str(savedata), '          '))
        pe.add_data(board,savedata)
        pe.add_sensor_parameter(board,'End Time',data[ip]['End Time'])
        print('    >end time: %s, avg elapse: %s'%(data[ip]['End Time'],data[ip]['Average Elapsed']))

    #==========================================================================================================
    #kill processes on remote machines
    pid_dict = {ip:PID for (ip,PID) in [(n,data[n]['PID']) for n in data.keys()]}
    pm.kill_processes(pid_dict)

    # add number of sources, sensors to experiment parameters
    pe.set_parameter('# Sensors',responses_received)
    pe.set_parameter('# Sources',1)
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
