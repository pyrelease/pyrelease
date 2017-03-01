import sys


PY2 = sys.version_info[0] == 2


if PY2:
    from ConfigParser import ConfigParser

    input = raw_input

else:
    from configparser import ConfigParser

    input = input
