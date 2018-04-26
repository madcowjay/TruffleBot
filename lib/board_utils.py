import RPi.GPIO as gpio
import time, threading

# set up the numbering scheme, BCM is more standard but BOARD coincides with my schematic
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)

# give aliases to pins and set them as outputs
led1 =  8
led2 = 10
tx0  = 29
tx1  = 31
gpio.setup(led1,gpio.OUT)
gpio.setup(led2,gpio.OUT)
gpio.setup(tx0, gpio.OUT)
gpio.setup(tx1, gpio.OUT)

# LED Interaction
bt1_stop = threading.Event()
bt2_stop = threading.Event()

def blink_thread(pin, stop_event, frequency):
    while( not stop_event.is_set() ):
        gpio.output(pin, gpio.HIGH)
        time.sleep(1/frequency)
        gpio.output(pin, gpio.LOW)
        time.sleep(1/frequency)
        pass

def ledAct(led, state, frequency=1):
    if led == 1:
        bt1_stop.set()
        if   state == 0: # off
            gpio.output(led1, gpio.LOW)
        elif state == 1: # on
            gpio.output(led1, gpio.HIGH)
        elif state == 2: # blink
            bt1_stop.clear()
            bt1 = threading.Thread(target=blink_thread, args=(led1, bt1_stop, frequency))
            bt1.start()
    else: #led = 2
        bt2_stop.set()
        if   state == 0: # off
            gpio.output(led2, gpio.LOW)
        elif state == 1: # on
            gpio.output(led2, gpio.HIGH)
        elif state == 2: # blink
            bt2_stop.clear()
            bt2 = threading.Thread(target=blink_thread, args=(led2, bt2_stop, frequency))
            bt2.start()

# Transistor Interaction
def pulse(port, t):
    if port == 0:
        gpio.output(tx0,gpio.HIGH)
        time.sleep(t)
        gpio.output(tx0,gpio.LOW)
    else:
        gpio.output(tx1,gpio.HIGH)
        time.sleep(t)
        gpio.output(tx1,gpio.LOW)
