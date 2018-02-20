import pi_utils.pyads1256
import pi_utils.pydac8532

# define classes and setup ADC
ads = pyads1256.ADS1256()
myid = ads.ReadID()
print('ADS1256 ID = ' + hex(myid))
ads.ConfigADC()
ads.SyncAndWakeup()

# define DAC and send a value to DACB
dac = pydac8532.DAC8532()
dac.SendDACBValue(0.75 * 2**16)

# Sampling method for ADC
def getADCsample():
	ads.SetInputMux(ads.MUX_AIN0,ads.MUX_AINCOM)   # these two values can be any two ADC Inputs
	ads.SyncAndWakeup()
	myconversion = ads.ReadADC()
	return myconversion
