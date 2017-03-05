# coding=utf-8
import os
import sys

try:
    import configparser
except ImportError:
    # Python 2.x fallback
    import ConfigParser as configparser

PY2 = sys.version_info[0] == 2

if PY2:

    input = raw_input

    devnull = os.open(os.devnull, os.O_WRONLY)

else:

    from subprocess import DEVNULL

    input = input

    devnull = DEVNULL
