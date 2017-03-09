#!/usr/bin/env
from __future__ import print_function, absolute_import
import os
import json
import logging

from pyrelease.userdata import PyPiRc, GitConfig
from pyrelease.helpers import find_package, \
    get_dependencies, get_name, import_target_package, \
    has_main_func, InvalidPackage

logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class PyPackage(object):
    """ Given a source path and a build directory, this class will fetch
     package and release information, including user info, gathered from
     various supported config files and the package itself.

     If no build directory is given, then a temporary directory is created
     based on the name and version of you release. For example
     a release by the name of `croutonlib` version `1.0.0`
     will be placed in a directory named `croutonlib.1.0.0/`

     Currently .gitconfig, .hgrc, and .pypirc files are
     the supported config files, but more can be added
     easily.
     """

    PACKAGE_FILES = {}

    def __init__(self, path, verbose=False):

        # The relative path to the target file
        self.target_file = find_package(path)
        if self.target_file is None:
            raise InvalidPackage("Not a valid target.")

        # The imported file.
        self.module = import_target_package(self.resolved_path)
        if self.module is None:
            raise ImportError("Couldn't import the module.")

        # The name of the package to be released
        self.name = get_name(self.target_file)

        # The version number as set in the __version__ variable
        self.version = self.get_version()

        # The license the package will be released under.
        self.license = self.get_license()

        # The package description as taken from package info.
        self.description = self.get_description()

        # Returns a dict containing config file data, such as
        # the .pypirc and .gitconfig data
        self.user_info = self.get_user_info()

        # The name of the developer or author of the release
        self.author = self.get_author()

        # The authors email
        self.author_email = self.get_author_email()

        # A list of dependencies to to be added to requirements.txt
        self.requirements = get_dependencies(self.target_file)

        # Returns True if the target has a `main` function
        self.is_script = has_main_func(self.target_file)

        # Turns on third party library console messages
        self.verbose = verbose

        self.errors = None

    def get_author(self):
        try:
            author = self.module.__author__
        except AttributeError:
            rv = self.user_info['gitconfig'].author
            logger.info("Got author from .gitconfig: %s", str(rv))
            return rv
        else:
            logger.info("Author variable found - %s -", str(author))
            return author

    def get_author_email(self):
        rv = self.user_info['gitconfig'].author_email
        logger.info("Got email from .gitconfig: %s", str(rv))
        return rv

    def get_description(self):
        mod = self.module
        try:
            entry = mod.__dict__[mod.__all__[0]]
        except (AttributeError, KeyError):
            logger.warning(
                "Module has no __all__ attribute from which to "
                "derive it's description.")
            return ""
        else:
            if entry.__doc__:
                description = entry.__doc__
                logger.info("Description: %s", str(description))
            else:
                description = ""
                logger.warning(
                    "(%s) has no docstring to use "
                    "for project description", str(entry))
            return description

    def get_license(self):
        try:
            _license = self.module.__license__
        except AttributeError:
            logger.warning("No license found.")
            return None
        else:
            logger.info("License found - %s -", str(_license))
            return _license

    def get_user_info(self):
        """Fetches user info from .gitconfig, .pypirc and .hgrc files
         if they exist and returns them as a dict."""
        rv = {
            "gitconfig": GitConfig(),
            "pypirc": PyPiRc(),
            # "hgrc":      HgRc()
        }
        logger.info("Got user info (%s)", str(rv))
        return rv

    def get_version(self):
        try:
            ver = self.module.__version__
        except AttributeError:
            logger.warning("No version found.")
            return None
        else:
            logger.info("Version found - %s -", str(ver))
            return ver

    @property
    def find_packages(self):
        if os.path.basename(self.target_file) == '__init__.py':
            return ", find_packages"
        else:
            return ""

    @property
    def install_requires(self):
        if self.requirements:
            return "install_requires=%s," % repr(
                self.requirements)
        else:
            return ""

    @property
    def is_data_files(self):
        """Returns True if there is a data folder in the resolved path
         """
        return os.path.exists(os.path.join(self.resolved_path, 'data'))

    @property
    def is_single_file(self):
        return os.path.isfile(self.target_file)

    @property
    def resolved_path(self):
        return os.path.abspath(self.target_file)

    @property
    def url(self):
        """Returns the URL that the package will be
         hosted on"""
        return 'https://pypi.python.org/pypi/' + self.name

    def load(self):
        """Loads a release.info save file."""
        logger.info("Loading from save file.")
        with open("release.info", 'r') as f:
            try:
                o = json.load(f)
            except ValueError as e:
                logger.warning("Save file may be corrupted.")
                logger.error("%s", sys_exec=True)
                return
            else:
                self.__dict__.update(**o)
                self._update()
                logger.info("Loaded successfully.")

    def save(self):
        """Saves package data to release.info for easy
         reloading of edited releases
         """
        with open("release.info", 'w') as f:
            data = self.jsonize()
            json.dump(data, fp=f, indent=4)

    def update_user_info(self):
        self.user_info = self.get_user_info()

    def _update(self):
        self.module = import_target_package(self.resolved_path)
        self.update_user_info()

    def jsonize(self):
        """Returns a dict of the PyPackage attributes for
         saving
         """
        rv = dict(
            name=self.name,
            version=self.version,
            license=self.license,
            description=self.description,
            author=self.author,
            author_email=self.author_email,
            requirements=self.requirements,
        )
        return rv

    def __str__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("{}: {}".format(k, v))
        return "\n".join(rv)
