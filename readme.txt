These files should be all you need to get a raspberry pi up and running with similar sensor software.

In order for the UDP communication to work properly, you must be on a relatively open wireless network.
Any home router should work. The Brown wireless network doesn't work because of the settings that
the IT guys have set it up with.

The 'host.py' file is where you can set experiment parameters(length, etc.).
When you want to run an experiment, running this file should handle everything.

The 'client.py' file and the contents of the 'pi_utils' folder should be on the raspberry pi.
The PiManager class in 'connect.py' can do this automatically by running the conditional_dir_sync() function
after properly initiating the PiManager class with the correct directories (the host_project_dir is on the
main computer, and the client_project_dir is the name of the folder on the pi where the files will be transferred).

The 'hpi_utils' folder contains the definitions of the PlumeLog and PlumeExperiment class. These are
used throughout the host file in order to create a coherent .hdf5 log file to be saved at the end.

The 'datavisualization.py' file is a tool to visualize the traces that are returned from the pis. It can be run
at the end of the host file by uncommenting a few lines. It may not work, depending on how you're returning the data,
but should be helpful to see how to read the .hdf5 files using the PlumeLog class.
