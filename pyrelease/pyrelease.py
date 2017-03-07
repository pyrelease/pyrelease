# coding=utf-8
from __future__ import print_function, absolute_import
import os
import json
import logging

from .helpers import find_package, get_author, get_author_email, \
    get_dependencies, get_license, get_name, import_target_package, \
    get_user_info, has_main_func, get_version, resolve_path, \
    InvalidPackage, get_description

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

        # The absolute path to the target directory
        self.resolved_path = resolve_path(self.target_file)

        # The imported file.
        self.module = import_target_package(self.resolved_path)
        if self.module is None:
            raise ImportError("Couldn't import the module.")

        # The name of the package to be released
        self.name = get_name(self.target_file)

        # The version number as set in the __version__ variable
        self.version = get_version(self.module)

        # The license the package will be released under.
        self.license = get_license(self.module)

        # The package description as taken from package info.
        self.description = get_description(self.module)

        # Returns a dict containing config file data, such as
        # the .pypirc and .gitconfig data
        self.user_info = get_user_info()

        # The name of the developer or author of the release
        self.author = get_author(self)

        # The authors email
        self.author_email = get_author_email(self)

        # Returns True if the target package is a single file.
        self.is_single_file = os.path.isfile(self.target_file)

        # A list of dependencies to to be added to requirements.txt
        self.requirements = get_dependencies(self.target_file)

        # Returns True if the target has a `main` function
        self.is_script = has_main_func(self.target_file)

        # For the MANIFEST.in file
        self.find_packages = "" if self.is_single_file else ", find_packages"

        # Turns on third party library console messages
        self.verbose = verbose

        self.errors = None

    def _update(self):
        self.module = import_target_package(self.resolved_path)
        self.update_user_info()

    def update_user_info(self):
        self.user_info = get_user_info()

    @property
    def is_data_files(self):
        """Returns True if there is a data folder in the resolved path
         """
        return os.path.exists(os.path.join(self.resolved_path, 'data'))

    @property
    def url(self):
        """Returns the URL that the package will be
         hosted on"""
        return 'https://pypi.python.org/pypi/' + self.name

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

    def __str__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("{}: {}".format(k, v))
        return "\n".join(rv)
