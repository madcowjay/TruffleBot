"""
@author: Michael

File module to save, delete and read datasets. Contains two classes:
    PlumeExperiment and PlumeLog.

PlumeExperiment:
	This class is used to store information about an experiment as it runs.
	General experiment attributes, collectors, and transmitters can be added to
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
		self.attributes   = {}
		self.trials       = {}

	#== Experiment Stuff =======================================================
	def set_experiment_start_time(self):
		# sets the start time of the experiment
		self.attributes['Start Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

	def set_experiment_end_time(self):
		# sets the end time of the experiment
		self.attributes['End Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

	def add_attribute_to_experiment(self, title, value):
		# general function to add an attribute of the experiment
		self.attributes[title] = value

	def add_trial_to_experiment(self, trial_name):
		# adds a trial to the experiment
		self.trials[trial_name] = {'Trial Name' : trial_name, 'attributes' : {}, 'collectors' : {}, 'transmitters': {}}

	#== Trial Stuff ============================================================
	def set_trial_start_time(self, trial_name):
		# sets the start time of the trial
		self.trials[trial_name]['attributes']['Start Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

	def set_trial_end_time(self, trial_name):
		# sets the end time of the trial
		self.trials[trial_name]['attributes']['End Time'] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

	def add_attribute_to_trial(self, trial_name, title, value):
		# general function to set an attribute of a trial
		self.trials[trial_name]['attributes'][title] = value

	def add_collector_to_trial(self, trial_name, collector_name, serial):
		# adds a collector to a trial
		self.trials[trial_name]['collectors'][collector_name] = {'Serial Number' : serial}

	def add_transmitter_to_trial(self, trial_name, transmitter_name, serial):
		# adds a transmitter to a trial
		self.trials[trial_name]['transmitters'][transmitter_name] = {'Serial Number' : serial}

	#== Collector / Transmitter Stuff ==========================================
	def add_element_to_collector(self, trial_name, collector_name, title, value):
		# adds an attribute or data set to a collector
		self.trials[trial_name]['collectors'][collector_name][title] = value

	def add_element_to_transmitter(self, trial_name, transmitter_name, title, value):
		# adds an attribute or data set to a transmitter
		self.trials[trial_name]['transmitters'][transmitter_name][title] = value


class PlumeLog:
	def __init__(self, logdirname='logfiles_PID', h5filename='plumelog'):
		debug_print('init started')
		self.logdirname = logdirname
		self.h5filename = h5filename


	def save_file(self, experiment):
		# takes a PlumeExperiment object as an argument and saves to an .hdf5 dataset. the logfile is named the YearMonthDay.hdf5,
		# the experiment is saved as a group within the .hdf5 named YearMonthDayTime and the collector/transmitter data is saved to groups within this
		# the general experiment attributes are saved as attributes of the highest level group (/YearMonthDay) of the experiment. collector or transmitter
		# attributes are saved as attributes of the associated lower level groups
		debug_print('save_file started')

		date_time = experiment.attributes['End Time']

		logdirname = self.logdirname
		logname = self.h5filename + '_' + experiment.attributes['End Time'][:10] + '.hdf5'
		writelogfilename = os.path.join(os.getcwd(),logdirname,logname)
		os.makedirs(os.path.dirname(writelogfilename), exist_ok=True)

		with h5py.File(writelogfilename, "a") as f:
			f.attrs['Description']       = 'Plume communications control framework'
			f.attrs['Format Version']    = 3.0
			f.attrs['Working Directory'] = os.getcwd()
			f.attrs['Platform']          = sys.platform
			f.attrs['Platform System']   = platform.system()
			f.attrs['Platform Release']  = platform.release()
			f.attrs['Platform Version']  = platform.version()
			f.attrs['Created Timestamp'] = experiment.attributes['Start Time']
			f.attrs['Updated Timestamp'] = experiment.attributes['End Time']

			exper = '/' + date_time
			exp = f.create_group(exper)
			debug_print('made experiment: {}'.format(exper))

			for attr in experiment.attributes.keys():
				exp.attrs[attr] = experiment.attributes[attr]

			for trial in experiment.trials.keys():
				group = exper + '/' + experiment.trials[trial]['Trial Name']
				f.create_group(group)
				debug_print('  made group: {}'.format(group))

				subgroup = group + '/Transmitters'
				f.create_group(subgroup)
				debug_print('  made subgroup: {}'.format(subgroup))

				for transmitter in experiment.trials[trial]['transmitters'].keys():
					subsubgroup = subgroup + '/' + transmitter
					grp = f.create_group(subsubgroup)
					debug_print('    made subsubgroup: {}'.format(subsubgroup))
					for key in experiment.trials[trial]['transmitters'][transmitter].keys():
						if type(experiment.trials[trial]['transmitters'][transmitter][key]) == np.ndarray:
							signalname = subsubgroup + '/' + key
							savearray  = experiment.trials[trial]['transmitters'][transmitter][key]
							dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
							dset[...] = savearray
							debug_print('      logged **data set**: {}'.format(key))
						else:
							grp.attrs[key] = str(experiment.trials[trial]['transmitters'][transmitter][key])
							debug_print('      logged attribute   : {}'.format(key))

				subgroup = group + '/Collectors'
				f.create_group(subgroup)
				debug_print('  made subgroup: {}'.format(subgroup))

				for collector in experiment.trials[trial]['collectors'].keys():
					print(collector)
					subsubgroup = subgroup + '/' + collector
					grp = f.create_group(subsubgroup)
					debug_print('    made subsubgroup: {}'.format(subsubgroup))
					for key in experiment.trials[trial]['collectors'][collector].keys():
						if type(experiment.trials[trial]['collectors'][collector][key]) == np.ndarray:
							signalname = subsubgroup + '/' + key
							savearray  = experiment.trials[trial]['collectors'][collector][key]
							dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
							dset[...] = savearray
							debug_print('      logged **data set**: {}'.format(key))
						else:
							grp.attrs[key] = str(experiment.trials[trial]['collectors'][collector][key])
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
