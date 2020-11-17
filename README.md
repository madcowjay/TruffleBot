# TruffleBot
An artificial "nose" comprised of VOC and pressure sensors that interfaces with either a Raspberry Pi.

![TruffleBot Board Image](media/TruffleBot_top.jpg?raw=true "Title")

The CircuitMaker homepage for TruffleBot is here: https://workspace.circuitmaker.com/Projects/Details/Jason-Webster/TruffleBot

## Installation
This repo contains the client and server software in one package. These files should be all you need to get a client Raspberry Pi up and running with a TruffleBot. The same software can be run on your Unix-like OS to act as the server and run the expperiments. Simply clone the repository on either system.

## Usage
A *default.cfg* file is provided which contains settings for both the client and the server.

In order for the UDP communication to work properly, you must be on a relatively open wireless network. Any home router should work. The Brown wireless network doesn't work because of the settings that the IT guys have set it up with.

## Unmaintained
The 'datavisualization.py' file is a tool to visualize the traces that are returned from the Pis. It can be run at the end of the host file by uncommenting a few lines. It may not work, depending on how you're returning the data, but should be helpful to see how to read the .hdf5 files using the PlumeLog class.
