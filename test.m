
clc; close all; clear variables; set(0,'DefaultFigureWindowStyle','docked')

filename='log/plumelog_20180521.hdf5';

info = h5info(filename); % get group information
trial_count = length(info.Groups); % get number of datasets

run = trial_count; %Last run in file

fprintf('Loading run %d/%d. \n', run, trial_count);

name=info.Groups(run).Name;

%sensor={'Board #0000000068c200c3','Board #00000000d7ef3031'};
%sensor={'Board #0000000068c200c3'};
sensor={'Board #00000000d7ef3031'};
%flow = h5read(filename,strcat(name,'/SourceData/Source 1/Flowrate'));

Rxbits=[];
for s= 1:length(sensor)
    arg = strcat(name,'/SensorData/',sensor{s})
    h5read(filename, arg)
    Rxbits=h5read(filename,arg);
end
%sensor=[1,2,5,6];
sensor = [1 2 3 4 5 6 7 8];
%sensor = [5 6 7 8];
%sensor = [2]
values=[];
figure;

for i=1:8
    hold on 
    values(i,:)=Rxbits(sensor(i),:);
    plot(values(i,:))
end
legend('1','2','3','4','5','6','7','8')
