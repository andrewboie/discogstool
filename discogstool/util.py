import os
import os.path

if not os.path.exists(os.path.expanduser("~/.discogstool")):
    os.mkdir(os.path.expanduser("~/.discogstool"))

def userfile(fname):
    return os.path.join(os.path.expanduser("~/.discogstool"), fname)

