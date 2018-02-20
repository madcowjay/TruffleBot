import RPi.GPIO as gpio
import time
# set up the numbering scheme, BCM is more standard but BOARD coincides with my schematic
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)

# give aliases to pins and set them as outputs
led1 = 8
led2 = 10
tx0 = 29
tx1 = 31
ADC_reset = 13
gpio.setup(led1,gpio.OUT)
gpio.setup(led2,gpio.OUT)
gpio.setup(tx0,gpio.OUT)
gpio.setup(tx1,gpio.OUT)
gpio.setup(ADC_reset,gpio.OUT)

# blinks specified led for t seconds
def blinkLed(number,t):
    if number==1:
        gpio.output(led1,gpio.HIGH)
        time.sleep(t)
        gpio.output(led1,gpio.LOW)
    else:
        gpio.output(led2,gpio.HIGH)
        time.sleep(t)
        gpio.output(led2,gpio.LOW)

def resetADC():
    gpio.output(ADC_reset,gpio.LOW)
    time.sleep(.0001)
    gpio.output(ADC_reset,gpio.HIGH)


def pulse(port,t):
    if port == 0:
        gpio.output(tx0,gpio.HIGH)
        time.sleep(t)
        gpio.output(tx0,gpio.LOW)
    else:
        gpio.output(tx1,gpio.HIGH)
        time.sleep(t)
        gpio.output(tx1,gpio.LOW)
