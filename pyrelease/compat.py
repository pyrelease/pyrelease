import sys


PY2 = sys.version_info[0] == 2


if PY2:
    from ConfigParser import ConfigParser as _ConfigParser, NoOptionError

    input = raw_input

    _UNSET = object()
    class ConfigParser(_ConfigParser):
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


else:
    from configparser import ConfigParser

    input = input
