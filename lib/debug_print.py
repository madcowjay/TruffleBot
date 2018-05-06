import os

DEBUG = eval(os.environ.get('DEBUG', 'False'))
def debug_print(string):
    "Will print if os.environ['DEBUG'] is 'True', otherwise it does nothing."

    if DEBUG:
        print("DEBUG: " + string)
