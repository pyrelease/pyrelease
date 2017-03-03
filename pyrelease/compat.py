# coding=utf-8
import os
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    from ConfigParser import ConfigParser as _ConfigParser, NoOptionError

    input = raw_input

    _UNSET = object()

    class CompatParser(_ConfigParser):
        """The sole purpose of this is to work around the fact that
         I'm lazy and still haven't changed the user data classes
         into dicts()

         ConfigParser doesn't have a default/fallback argument
         in Python 2 and I mainly work in Python 3 so I threw this
         hack together for the py2.7 users"""

        def get(self, section, option, fallback=_UNSET):
            try:
                rv = _ConfigParser.get(section, option)
            except NoOptionError:
                if fallback is _UNSET:
                    raise
                else:
                    return fallback
            else:
                return rv

    ConfigParser = CompatParser

    devnull = os.open(os.devnull, os.O_WRONLY)

else:
    from configparser import ConfigParser
    from subprocess import DEVNULL

    input = input

    devnull = DEVNULL

    ConfigParser = ConfigParser
