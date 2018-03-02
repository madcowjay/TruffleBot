# (very) simple test for DAC - sends a voltage to each channel
import time
from drivers import pylps22hb
# set up 16 bit DAC

my_cs = [33, 32, 37, 22, 35, 36, 38, 18]
#my_cs = [33]
lps = []
for i in range(len(my_cs)):
    lps.append(pylps22hb.LPS22HB(my_cs[i]))
    print('Press' + str(i) + ' id: ' + lps[i].ReadID())
