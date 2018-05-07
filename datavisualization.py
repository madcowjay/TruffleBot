import pi_utils.savefile
# import matplotlib
# matplotlib.use('TkAgg') # to fix MacOsX backend error
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.preprocessing import normalize

def visualize(logname):
	pl = pi_utils.savefile.PlumeLog(logdirname='gascommlogs')
	data = pl.read_all_data(logname)
	# pl.delete('plumelog_20170705.hdf5','Source 1')
	last_e = max(data.keys())

	#function to scale data with max = 1 and min =  0
	def normalize(vector):
		normed_vec = np.zeros(len(vector))
		xmin = min(vector)
		xmax = max(vector)
		for i,x in enumerate(vector):
			normed_vec[i] = (x-xmin)/(xmax-xmin)
		return normed_vec

	def channel_avg(array):
		avgs = [sum(n)/len(n) for n in array]
		return avgs


	#list only the board data in on our latest experiment
	boards = [n for n in data[last_e].keys() if 'Board' in n]

	#cheat way to put the boards in order
	# board_order = ['Board #2']#['Board #3','Board #7','Board #6','Board #4']
	# boards=board_order

	print(data[last_e]['Source 1'])
	message = data[last_e]['Source 1']['data']['Message']
	bitrate = float(data[last_e]['Source 1']['attributes']['bitrate'])
	pulse_duration = float(data[last_e]['Source 1']['attributes']['Pulse Duration'])
	samplerate = int(data[last_e][boards[0]]['attributes']['samplerate'])
	padding = int(data[last_e]['Source 1']['attributes']['Padding'])
	element_len = int(pulse_duration*samplerate)
	bit_len = int(samplerate/bitrate)
	print(element_len,bit_len)

	msg_plot = []
	for element in message:
		for n in range(element_len):
			msg_plot.append(element)
		if bit_len > element_len:
			for n in range(bit_len-element_len):
				msg_plot.append(element%1)
	msg_plot = np.pad(msg_plot,samplerate*padding,'constant',constant_values=0)
	print(msg_plot)

	#set up subplots to plot each boards sensor channel data in
	f, ax = plt.subplots(len(boards),2, sharex=True)

	for n,board in enumerate(boards):
		#data to be normalized and plotted
		n_data = data[last_e][board]['data']

		channel_avgs = channel_avg(n_data)

		for column in np.split(n_data,8, axis=1):
			# normalize column = sensor channel
			normed_c = normalize(column)
			x = np.arange(column.shape[0])

			#plot in subplot
			try:
				# plot in left column
				ax[0,0].set_title('Raw')
				ax[n,0].plot(x,column)
				ax[n,0].set_ylim([0,1])

				# ax[0,0].set_title('Averaged')
				# ax[n,0].plot(x,channel_avgs)

				# plot in right column
				ax[0,1].set_title('Normalized')
				ax[n,1].plot(x,normed_c)
				ax[n,1].set_ylim([-0.25,1.25])


				# plot message
				ax[n,0].plot(x,[(n*0.5)+0.25 for n in msg_plot],drawstyle='steps-pre')
				ax[n,1].plot(x,msg_plot,drawstyle='steps-pre')

				#label board
				ax[n,0].set_ylabel(board)
			except:
				# left column
				ax[0].set_title('Raw')
				ax[0].plot(x,column)
				ax[0].set_ylim([0,1])

				# right column
				ax[1].set_title('Normalized')
				ax[1].plot(x,normed_c)
				ax[1].set_ylim([-0.25,1.25])

				# message
				ax[0].plot(x,[(n*0.5)+0.25 for n in msg_plot],drawstyle='steps-pre')
				ax[1].plot(x,msg_plot,drawstyle='steps-pre')

				# label board
				ax[0].set_ylabel(board)

	#make pretty
	# plt.title('Chemical Sensor Response to Binary Message')
	plt.xlabel('Sample Count')
	plt.ylabel('Normalized Sensor Data')

	#save png
	plt.savefig('gascommlogs/plots/%s'%last_e)
	#show plot
	plt.show()

# visualize('plumelog_20171121.hdf5')
