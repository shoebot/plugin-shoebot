#!/usr/bin/env python

import os
import subprocess

here = os.path.dirname(os.path.abspath(__file__))

def gedit_install():
    version = None
    try:
        version = subprocess.check_output(['gedit', '--version']).strip()
    except OSError:
        print("gedit not found")
        return
    v_str = version.rpartition(" ")[-1]
    major, minor, patch = map(int, v_str.split("."))

    if major == 2:
        subprocess.call("gedit2-plugin/install.py", shell=True)
    elif major == 3:
        if minor < 12:
            subprocess.call("gedit3-plugin/install.py", shell=True)
        else:
            cwd = os.path.join(here, "gedit3.12-plugin")
            subprocess.call("gedit3.12-plugin/install.py", shell=True)
    else:
        print("Unknown gedit version %s" % version)


if __name__=="__main__":
    print("Install gedit plugins")
    gedit_install()
    print("TODO - installers for other plugins")
