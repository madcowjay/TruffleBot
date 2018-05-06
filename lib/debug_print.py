import os, sys

DEBUG = eval(os.environ.get('DEBUG', 'False'))
def debug_print(string):
    "Will print if os.environ['DEBUG'] is 'True', otherwise it does nothing."

    if DEBUG:
        frame = list(sys._current_frames().values())[0]
        file  = frame.f_back.f_code.co_filename.split('/')[-1]
        name  = frame.f_back.f_code.co_name
        print("DEBUG: {0:<32} => {1}".format(file+'/'+name, string))
