from __future__ import print_function, absolute_import
import os
import logging
from email.utils import getaddresses

from .compat import ConfigParser

logger = logging.getLogger('pyrelease')


class UserConfigMixin(object):
    def __str__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("{}: {}".format(k, v))
        return "\n".join(rv)


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
            self.author = parser.get('simple_setup', 'author') or None
            self.author_email = parser.get('simple_setup', 'author_email') or None


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
            try:
                parser.read(os.path.expanduser('~/.gitconfig'))
            except Exception as e:
                logger.error("No .gitconfig found. (%s)", sys_exec=True)
            self.author = parser.get('user', 'name') or None
            self.author_email = parser.get('user', 'email') or None


class HgRc(UserConfigMixin):
    """
    ~/.hgrc
    [ui]
    username = My Name Is <myemail@example.com>
    """
    def __init__(self):
        parser = ConfigParser()
        if os.path.exists(os.path.expanduser('~/.hgrc')):
            parser.read(os.path.expanduser('~/.hgrc'))
            if parser is not None:
                username = parser.get('ui', 'username') or None
                if username is None:
                    return
                try:
                    name_email = getaddresses([username])
                except TypeError:
                    name_email = None
                self.author = None
                self.author_email = None
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
