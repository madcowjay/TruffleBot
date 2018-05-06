clc
close all
clear variables
set(0,'DefaultFigureWindowStyle','docked')


filename='plumelog_20180426.hdf5';
info = h5info(filename); % get group information
numrun=length(info.Groups); % get number of datasets

numrun = 1;
include_runs = [10];
run=include_runs;

fprintf('Loading run %d/%d. \n',run,numrun);

name=info.Groups(run).Name;

%sensor={'Board #0000000068c200c3','Board #00000000d7ef3031'};
sensor={'Board #0000000068c200c3'};
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