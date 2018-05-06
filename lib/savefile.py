# -*- coding: utf-8 -*-
"""

@author: Michael

File module to save, delete and read datasets. Contains two classes: PlumeExperiment and PlumeLog.

PlumeExperiment:
    This class is used to store information about an experiment as it runs. General experiment parameters, sensors, and sources can be added
    the class. Sources and Sensors have datasets associated with each instance.

PlumeLog:
    This class is used for saving experiment data to .hdf5 logfile, as well as reading from previously stored logfiles.


"""
import os, sys, platform, warnings
from datetime import datetime
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
import h5py

class PlumeExperiment:
    #initializes the empty dictionaries that will be filled by the methods below
    def __init__(self):
        self.parameters = {}
        self.sources = {}
        self.sensors = {}

    # general function to set a parameter of the experiment, will be stored as a .hdf5 attribute at the highest level
    def set_parameter(self, paramName, paramValue):
        self.parameters[paramName] = paramValue

    # adds a sensor to the experiment, can be initialized with various attributes
    def add_sensor(self, name, gain=None, pumpspeed=None, location=None, samplerate=None):
        self.sensors[name] = {'gain':gain, 'pumpspeed':pumpspeed, 'location':location, 'samplerate':samplerate}

    # used to add a miscellaneous parameter to a sensor
    def add_sensor_parameter(self, sensor_name, param, value):
        self.sensors[sensor_name][param] = value

    # adds a source to the experiment, can be initialized with various parameters which will be stored as attributes
    def add_source(self, name, gain=None, chemical=None, message=None, coding=None, location=None, bitrate=None):
        self.sources[name] = {'gain':gain, 'chemical':chemical, 'message':message, 'coding':coding, 'location':location, 'bitrate':bitrate}

    # used to add a miscellaneous parameter to a source
    def add_source_parameter(self, source_name, param, value):
        self.sources[source_name][param] = value

    # adds a dataset to a sensor or source. if to a sensor, names the dataset 'data'. if to a source, name must be specified with 'datatype='
    def add_data(self, save_name, data, datatype=''):
        if save_name in self.sensors.keys():
            self.sensors[save_name]['data'] = data
        elif save_name in self.sources.keys():
            self.sources[save_name][datatype] = data

    # sets the start time of the experiment, will be saved as high-level attribute
    def set_start_time(self):
        self.parameters['Start Time'] = datetime.now().strftime("%Y%m%d_%H%M%S")

    # sets the end time of the experiment, will be saved as high-level attribute
    def set_end_time(self):
        self.parameters['End Time'] = datetime.now().strftime("%Y%m%d_%H%M%S")


class PlumeLog:
    def __init__(self, logdirname='logfiles_PID', h5filename='plumelog'):
        self.logdirname = logdirname
        self.h5filename = h5filename

    # takes a PlumeExperiment object as an argument and saves to an .hdf5 dataset. the logfile is named the YearMonthDay.hdf5,
    # the experiment is saved as a group within the .hdf5 named YearMonthDayTime and the sensor/source data is saved to groups within this
    # the general experiment parameters are saved as attributes of the highest level group (/YearMonthDay) of the experiment. Sensor or source
    # parameters are saved as attributes of the associated lower level groups
    def save_file(self, experiment):

        date_time = experiment.parameters['End Time']

        logdirname=self.logdirname
        logname = self.h5filename + '_' + experiment.parameters['End Time'][:8] + '.hdf5'
        writelogfilename = os.path.join(os.getcwd(),logdirname,logname)
        os.makedirs(os.path.dirname(writelogfilename), exist_ok=True)

        with h5py.File(writelogfilename, "a") as f:
            f.attrs['description'] = 'Plume communications control framework'
            f.attrs['formatversion'] = 1.0
            f.attrs['workingdir'] = os.getcwd()
            f.attrs['platform'] = sys.platform
            f.attrs['platform_system'] = platform.system()
            f.attrs['platform_release'] = platform.release()
            f.attrs['platform_version'] = platform.version()
            f.attrs['Created timestamp'] = experiment.parameters['Start Time']
            f.attrs['Updated timestamp'] = experiment.parameters['End Time']


            groupname='/'+date_time
            grp=f.create_group(groupname)
            for attr in experiment.parameters.keys():
                grp.attrs[attr] = experiment.parameters[attr]

            filename = groupname +'/SourceData'
            f.create_group(filename)

            for source in experiment.sources.keys():
                subgroup = filename+'/'+source
                grp = f.create_group(subgroup)
                for key in experiment.sources[source].keys():
                    if type(experiment.sources[source][key]) == np.ndarray:
                        signalname = subgroup+'/'+key
                        savearray = experiment.sources[source][key]
                        dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
                        dset[...] = savearray
                    else:
                        grp.attrs[key] = str(experiment.sources[source][key])


            filename = groupname+'/SensorData'
            f.create_group(filename)

            for sensor in experiment.sensors.keys():
                #create dataset and save data
                signalname = filename+'/'+sensor
                savearray  = experiment.sensors[sensor]['data']
                dset = f.create_dataset(signalname, savearray.shape, savearray.dtype.name)
                dset[...] = savearray

                #add attributes to dataset
                for attr in experiment.sensors[sensor].keys():
                    if attr != 'data':
                        dset.attrs[attr] = str(experiment.sensors[sensor][attr])
            f.close()

        print("All data saved to:",logname)

        return '%s/%s'%(logdirname,logname),date_time


    # returns a dataset, must specify logfile and full path to dataset. Ex: read_dataset('20170614.hdf5','/20170614_120400/Sensor 1')
    def read_dataset(self, logfile, dset_name):
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

    # returns a dictionary with all the data in the logfile, must specifiy logfilename
    def read_all_data(self, logfile):
        with h5py.File('%s/%s'%(self.logdirname,logfile)) as f:
            times = {}
            for time in f['/'].keys():
                times[time] = {}
                data = {}
                for source in f['/%s/SourceData' % (time)].keys():
                    for key in f['/%s/SourceData/%s' % (time,source)].keys():
                        dset = f['/%s/SourceData/%s/%s' % (time,source,key)]
                        data[key]= np.array(dset)
                    attributes={}
                    for key in f['/%s/SourceData/%s' % (time,source)].attrs.keys():
                        attributes[key] = f['/%s/SourceData/%s' % (time,source)].attrs[key]
                    times[time][source] = {'data':data, 'attributes':attributes}

                for sensor in f['/%s/SensorData' % (time)].keys():
                    dset = f['/%s/SensorData/%s' % (time,sensor)]
                    data = np.array(dset)
                    attributes={}
                    for key in dset.attrs.keys():
                        attributes[key] = dset.attrs[key]
                    times[time][sensor] = {'data':data, 'attributes':attributes}
            return times

    #returns all of the experiment times saved within the logfile. Ex: ['20170614_120400', '20170614_130600','20170614_220560' ]
    def get_experiments(self, logfile):
        with h5py.File('%s/%s'%(self.logdirname,logfile)) as f:
            times = [n for n in f.keys()]
            return times

    #deleltes an element of the logfile, must specify full path. Ex: delete('20170614.hdf5','/20170614_120400/Source 1/TxData')
    def delete(self, logfile, element):
        with h5py.File('%s/%s'%(self.logdirname,logfile), "a") as f:
            f.__delitem__(element)
        print("%s deleted" % (element))
