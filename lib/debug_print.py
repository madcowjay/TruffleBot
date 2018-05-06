import os, sys

DEBUG = eval(os.environ.get('DEBUG', 'False'))
def debug_print(string):
    "Will print if os.environ['DEBUG'] is 'True', otherwise it does nothing."

    if DEBUG:
        f = list(sys._current_frames().values())[0]
        g = f.f_back.f_back
        h = g.f_code
        print(h.co_filename)
        print("DEBUG: " + string)
