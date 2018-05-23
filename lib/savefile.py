"""
@author: Michael

File module to save, delete and read datasets. Contains two classes:
    PlumeExperiment and PlumeLog.

PlumeExperiment:
	This class is used to store information about an experiment as it runs.
	General experiment parameters, collectors, and transmitters can be added to
	the class. Transmitters and collectors have datasets associated with each
	instance.

PlumeLog:
	This class is used for saving experiment data to .hdf5 logfile, as well as
    reading from previously stored logfiles.
"""

import os, sys, platform, warnings
from   datetime import datetime
import numpy as np
from   lib.debug_print import *

warnings.filterwarnings("ignore", category=FutureWarning)
import h5py

class PlumeExperiment:
	#initializes the empty dictionaries that will be filled by the methods below
	def __init__(self):
		self.parameters   = {}
		self.transmitters = {}
		self.collectors   = {}


	def set_parameter(self, paramName, paramValue):
		# general function to set a parameter of the experiment, will be stored as a .hdf5 attribute at the highest level
		self.parameters[paramName] = paramValue


	def add_collector(self, name, gain=None, location=None):
		# adds a collector to the experiment, can be initialized with various attributes
		self.collectors[name] = {'gain':gain, 'location':location}


	def add_collector_element(self, collector_name, title, value):
		# adds a parameter or data set to a collector
		self.collectors[collector_name][title] = value


	def add_transmitter(self, name, gain=None, chemical=None, message=None, coding=None, location=None, bitrate=None):
		# adds a transmitter to the experiment, can be initialized with various parameters which will be stored as attributes
		self.transmitters[name] = {'gain':gain, 'chemical':chemical, 'message':message, 'coding':coding, 'location':location, 'bitrate':bitrate}


	def add_transmitter_element(self, transmitter_name, title, value):
		# adds a parameter or data set to a transmitter
		debug_print('add_transmitter_data started')
		self.transmitters[transmitter_name][title] = value


	def set_start_time(self):
		# sets the start time of the experiment, will be saved as high-level attribute
		self.parameters['Start Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


	def set_end_time(self):
		# sets the end time of the experiment, will be saved as high-level attribute
		self.parameters['End Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")



class PlumeLog:
	def __init__(self, logdirname='logfiles_PID', h5filename='plumelog'):
		debug_print('init started')
		self.logdirname = logdirname
		self.h5filename = h5filename


	def save_file(self, experiment):
		# takes a PlumeExperiment object as an argument and saves to an .hdf5 dataset. the logfile is named the YearMonthDay.hdf5,
		# the experiment is saved as a group within the .hdf5 named YearMonthDayTime and the collector/transmitter data is saved to groups within this
		# the general experiment parameters are saved as attributes of the highest level group (/YearMonthDay) of the experiment. collector or transmitter
		# parameters are saved as attributes of the associated lower level groups
		debug_print('save_file started')

		date_time = experiment.parameters['End Time']

		logdirname = self.logdirname
		logname = self.h5filename + '_' + experiment.parameters['End Time'][:10] + '.hdf5'
		writelogfilename = os.path.join(os.getcwd(),logdirname,logname)
		os.makedirs(os.path.dirname(writelogfilename), exist_ok=True)

		with h5py.File(writelogfilename, "a") as f:
			f.attrs['description']   = 'Plume communications control framework'
			f.attrs['formatversion'] = 2.0
			f.attrs['workingdir']    = os.getcwd()
			f.attrs['platform']      = sys.platform
			f.attrs['platform_system']   = platform.system()
			f.attrs['platform_release']  = platform.release()
			f.attrs['platform_version']  = platform.version()
			f.attrs['Created timestamp'] = experiment.parameters['Start Time']
			f.attrs['Updated timestamp'] = experiment.parameters['End Time']

			group = '/' + date_time # this is the trial
			grp = f.create_group(group)
			debug_print('made group: {}'.format(group))

			for attr in experiment.parameters.keys(): # add trial parameters
				grp.attrs[attr] = experiment.parameters[attr]

			subgroup = group + '/Transmitters'
			f.create_group(subgroup)
			debug_print('  made subgroup: {}'.format(subgroup))

			for transmitter in experiment.transmitters.keys():
				subsubgroup = subgroup + '/' + transmitter
				grp = f.create_group(subsubgroup)
				debug_print('    made subsubgroup: {}'.format(subsubgroup))
				for key in experiment.transmitters[transmitter].keys():
					if type(experiment.transmitters[transmitter][key]) == np.ndarray:
						signalname = subsubgroup + '/' + key
						savearray  = experiment.transmitters[transmitter][key]
						dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
						dset[...] = savearray
						debug_print('      logged **data set**: {}'.format(key))
					else:
						grp.attrs[key] = str(experiment.transmitters[transmitter][key])
						debug_print('      logged attribute   : {}'.format(key))

			subgroup = group + '/Collectors'
			f.create_group(subgroup)
			debug_print('  made subgroup: {}'.format(subgroup))

			for collector in experiment.collectors.keys():
				print(collector)
				subsubgroup = subgroup + '/' + collector
				grp = f.create_group(subsubgroup)
				debug_print('    made subsubgroup: {}'.format(subsubgroup))
				for key in experiment.collectors[collector].keys():
					if type(experiment.collectors[collector][key]) == np.ndarray:
						signalname = subsubgroup + '/' + key
						savearray  = experiment.collectors[collector][key]
						dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
						dset[...] = savearray
						debug_print('      logged **data set**: {}'.format(key))
					else:
						grp.attrs[key] = str(experiment.collectors[collector][key])
						debug_print('      logged attribute   : {}'.format(key))

			f.close()
		print("All data saved to:",logname)
		return '%s/%s'%(logdirname,logname), date_time


	def read_dataset(self, logfile, dset_name):
		# returns a dataset, must specify logfile and full path to dataset. Ex: read_dataset('20170614.hdf5','/20170614_120400/collector 1')
		debug_print('read_dataset started')
		try:
			with h5py.File('%s/%s'%(self.logdirname,logfile)) as f:
				dset = f[dset_name]
				data = np.array(dset)
				attributes={}
				for key in dset.attrs.keys():
					attributes[key] = dset.attrs[key]
				return data, attributes
		except:
			print(dset_name,' not found.\n')


	def read_all_data(self, logfile):
		# returns a dictionary with all the data in the logfile, must specifiy logfilename
		debug_print('read_all_data started')
		with h5py.File('%s/%s'%(self.logdirname,logfile)) as f:
			times = {}
			for time in f['/'].keys():
				times[time] = {}
				data = {}
				for transmitter in f['/%s/transmitterData' % (time)].keys():
					for key in f['/%s/transmitterData/%s' % (time, transmitter)].keys():
						dset = f['/%s/transmitterData/%s/%s' % (time, transmitter, key)]
						data[key]= np.array(dset)
					attributes={}
					for key in f['/%s/transmitterData/%s' % (time, transmitter)].attrs.keys():
						attributes[key] = f['/%s/transmitterData/%s' % (time, transmitter)].attrs[key]
					times[time][transmitter] = {'data':data, 'attributes':attributes}

				for collector in f['/%s/collectorData' % (time)].keys():
					for key in f['/%s/collectorData/%s' % (time, collector)].keys():
						dset = f['/%s/collectorData/%s/%s' % (time, collector, key)]
						data[key]= np.array(dset)
					attributes={}
					for key in f['/%s/collectorData/%s' % (time, collector)].attrs.keys():
						attributes[key] = f['/%s/collectorData/%s' % (time, collector)].attrs[key]
					times[time][collector] = {'data':data, 'attributes':attributes}
			return times


	def get_experiments(self, logfile):
		# returns all of the experiment times saved within the logfile. Ex: ['20170614_120400', '20170614_130600','20170614_220560' ]
		debug_print('get_experiments started')
		with h5py.File('%s/%s'%(self.logdirname,logfile)) as f:
			times = [n for n in f.keys()]
			return times


	def delete(self, logfile, element):
		# deleltes an element of the logfile, must specify full path. Ex: delete('20170614.hdf5','/20170614_120400/transmitter 1/TxData')
		debug_print('delete started')
		with h5py.File('%s/%s'%(self.logdirname,logfile), "a") as f:
			f.__delitem__(element)
		print("%s deleted" % (element))
