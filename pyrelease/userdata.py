from __future__ import print_function, absolute_import
import os
import logging
from email.utils import getaddresses

from .compat import ConfigParser

logger = logging.getLogger('pyrelease')


# TODO: Really, really gotta make these functions that return dicts.. But I'm soooo lazy

class UserConfigMixin(object):
    def __str__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("{}: {}".format(k, v))
        return "\n".join(rv)

    def __repr__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("%s: %s" % (k, v))
        return "{%s}" % (", ".join(rv))


class PyPiRc(UserConfigMixin):
    """
    ~/.pypirc
    [simple_setup]
    author = My Name Is
    author_email = myemail@example.com

    """
    def __init__(self):
        parser = ConfigParser()
        self.author = None
        self.author_email = None
        if os.path.exists(os.path.expanduser('~/.pypirc')):
            parser.read(os.path.expanduser('~/.pypirc'))
            self.author = parser.get('pypi', 'username', fallback=None)
            self.author_email = parser.get('pypi', 'email', fallback=None)


class GitConfig(UserConfigMixin):
    """
    ~/.gitconfig

    [user]
            name = My Name Is
            email = myemail@example.com

    """
    def __init__(self):
        self.author = None
        self.author_email = None
        if os.path.exists(os.path.expanduser('~/.gitconfig')):
            parser = ConfigParser()
            parser.read(os.path.expanduser('~/.gitconfig'))
            self.author = parser.get('user', 'name', fallback=None)
            self.author_email = parser.get('user', 'email', fallback=None)
        else:
            logger.error("No .gitconfig found.")


class HgRc(UserConfigMixin):
    """
    ~/.hgrc
    [ui]
    username = My Name Is <myemail@example.com>
    """
    def __init__(self):
        self.author = None
        self.author_email = None
        if os.path.exists(os.path.expanduser('~/.hgrc')):
            parser = ConfigParser()
            parser.read(os.path.expanduser('~/.hgrc'))

            username = parser.get('ui', 'username', fallback=None)
            if username is None:
                return
            try:
                name_email = getaddresses([username])
            except TypeError:
                name_email = None
            if name_email:
                self.author = name_email[0][0]
                self.author_email = name_email[0][1]


class DotGitConfig(UserConfigMixin):
    """Grab info out of a .git/config file.

    [remote "origin"]
        url = git@github.com:pygame/solarwolf.git

    """
    def __init__(self):
        """
        """
