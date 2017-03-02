import os
import sys

PY2 = sys.version_info[0] == 2


if PY2:
    from ConfigParser import ConfigParser as _ConfigParser, NoOptionError, NoSectionError

    input = raw_input

    _UNSET = object()
    class ConfigParser(_ConfigParser):
        def get(self, section, option, raw=None, vars=False, fallback=_UNSET):
            try:
                rv = _ConfigParser().get(section, option)
            except (NoOptionError, NoSectionError):
                if fallback is _UNSET:
                    raise
                else:
                    return fallback
            else:
                return rv

    devnull = open(os.devnull, 'w')

else:
    from configparser import ConfigParser
    from subprocess import DEVNULL

    input = input

    devnull = DEVNULL
