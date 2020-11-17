function [name,Message,Txbits,Rxbits,samplerate,bitrate,wind,flow]=getData(filename,subdirectory,include_runs,sensor)
    % ========================================================
    if ~exist('filename','var')
        filename='plumelog_20170913.hdf5';    % DEFAULT LOG FILE
    end

    if ~exist('subdirectory','var')
        subdirectory='logfiles';   % DEFAULT SUBDIRECTORY
    end

    filename=fullfile(pwd,subdirectory,filename);
    info = h5info(filename); % get group information
    numrun=length(info.Groups); % get number of datasets


    if ~exist('include_runs','var')
        include_runs = 1;
        print('No runs specified. Displaying Run #1. \n');
    end

    if ~exist('sensor','var')
        sensor={'Sensor 1','Sensor 2','Sensor 3','Sensor 4'};
    end
    % ========================================================

    fprintf('==================\n');
fprintf('Opening file %s. \n',filename);

% message = h5read(filename,strcat(info.Groups(10).Name,'/SourceData/Source 1/TxData'));
run=include_runs;
if run > numrun
    include_runs = 1;
    fprintf('Run #%d does not exist in this file. Displaying Run #1 \n',run);
end
fprintf('Loading run %d/%d. \n',run,numrun);
        
name=info.Groups(run).Name;
        
Txbits = h5read(filename,strcat(name,'/SourceData/Source 1/TxData'));
Message= h5read(filename,strcat(name,'/SourceData/Source 1/Message'));

try
%     wind = h5read(filename,strcat(name,'/SourceData/Source 1/Windspeed'));
    flow = h5read(filename,strcat(name,'/SourceData/Source 1/Flowrate'));
%     wind=[];
catch 
   disp('Wind and Flow not recorded for this dataset')
   wind=[];
   flow=[];
  
end 
wind=[];
for s= 1:length(sensor)
    Rxbits(s,:)=h5read(filename,strcat(name,'/SensorData/',sensor{s}));
end

samplerate =str2num(cell2mat(h5readatt(filename,strcat(name,'/SensorData/Sensor 1'),'samplerate')));
bitrate = str2num(cell2mat(h5readatt(filename,strcat(name,'/SourceData/Source 1'),'bitrate')));
Message=repelem(Message,floor(samplerate/bitrate));
