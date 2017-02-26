import os
from email.utils import getaddresses
from configparser import ConfigParser


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
        parser.read(os.path.expanduser('~/.pypirc'))
        self.author = parser.get('simple_setup', 'author', fallback=None)
        self.author_email = parser.get('simple_setup', 'author_email', fallback=None)


class GitConfig(UserConfigMixin):
    """
    ~/.gitconfig

    [user]
            name = My Name Is
            email = myemail@example.com

    """
    def __init__(self):
        parser = ConfigParser()
        parser.read(os.path.expanduser('~/.gitconfig'))
        self.author = parser.get('user', 'name', fallback=None)
        self.author_email = parser.get('user', 'email', fallback=None)


class HgRc(UserConfigMixin):
    """
    ~/.hgrc
    [ui]
    username = My Name Is <myemail@example.com>
    """
    def __init__(self):
        parser = ConfigParser()
        parser.read(os.path.expanduser('~/.hgrc'))
        username = parser.get('ui', 'username', fallback=None)
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
