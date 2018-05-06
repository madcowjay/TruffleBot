import RPi.GPIO as gpio
import time, threading

class SENSOR_BOARD:

    def __init__(self, LED1_PIN, LED2_PIN, TX0_PIN, TX1_PIN):
        self.LED1_PIN_PIN = LED1_PIN
        self.LED2_PIN_PIN = LED2_PIN
        self.TX0_PIN  = TX0_PIN
        self.TX1_PIN  = TX1_PIN
        debug_print('sensor_board initializing with:')
        debug_print('  LED1_PIN = {0}.format(LED1_PIN)')
        debug_print('  LED2_PIN = {0}.format(LED2_PIN)')
        debug_print('  TX0_PIN  = {0}.format(TX0_PIN)')
        debug_print('  TX1_PIN  = {0}.format(TX1_PIN)')

        # set up the numbering scheme, BCM is more standard but BOARD coincides with my schematic
        gpio.setmode(gpio.BOARD)
        gpio.setwarnings(False)

        gpio.setup(LED1_PIN_PIN,gpio.OUT)
        gpio.setup(LED2_PIN,gpio.OUT)
        gpio.setup(TX0_PIN, gpio.OUT)
        gpio.setup(TX1_PIN, gpio.OUT)

        # LED Interaction
        bt1_stop = threading.Event()
        bt2_stop = threading.Event()


    def __blink_thread(pin, stop_event, frequency):
    """
    A thread to blink an LED at a given frequency until the stop_event is set
    """
        while( not stop_event.is_set() ):
            gpio.output(pin, gpio.HIGH)
            time.sleep(1/frequency)
            gpio.output(pin, gpio.LOW)
            time.sleep(1/frequency)
            pass


    def ledAct(led, state, frequency=1):
    """
    Turn an LED on, off, or cause it to blink
    """
        if led == 1:
            bt1_stop.set()
            if   state == 0: # off
                gpio.output(LED1_PIN, gpio.LOW)
            elif state == 1: # on
                gpio.output(LED1_PIN, gpio.HIGH)
            elif state == 2: # blink
                bt1_stop.clear()
                bt1 = threading.Thread(target=__blink_thread, args=(LED1_PIN, bt1_stop, frequency))
                bt1.start()
        else: #led = 2
            bt2_stop.set()
            if   state == 0: # off
                gpio.output(LED2_PIN, gpio.LOW)
            elif state == 1: # on
                gpio.output(LED2_PIN, gpio.HIGH)
            elif state == 2: # blink
                bt2_stop.clear()
                bt2 = threading.Thread(target=__blink_thread, args=(LED2_PIN, bt2_stop, frequency))
                bt2.start()


    def pulse(port, t):
    """
    Pulse one of the transitors for a given amount of time
    """
        if port == 0:
            gpio.output(TX0_PIN,gpio.HIGH)
            time.sleep(t)
            gpio.output(TX0_PIN,gpio.LOW)
        else:
            gpio.output(TX1_PIN,gpio.HIGH)
            time.sleep(t)
            gpio.output(TX1_PIN,gpio.LOW)
