# coding=utf-8
from __future__ import print_function, absolute_import
import os
import logging
from distutils.version import LooseVersion

from .helpers import find_package, get_author, get_author_email, \
    get_dependencies, get_license, get_name, get_package_info, \
    get_user_info, get_version, has_main_func, resolve_path

logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class PyPackage(object):
    """ Given a source path and a build directory, this class will fetch
     package and release information, including user info, gathered from
     various supported config files and the package itself.

     If no build directory is given, then a temporary directory is created
     and used to store the temporary package until it can be built and up-
     loaded.

     Currently .gitconfig, .hgrc, and .pypirc files are supported, but more
     can easily be added should the need arise.
     """

    PACKAGE_FILES = {}

    def __init__(self, path, verbose=False):

        # Turns on third party library console messages
        # TODO: This could probably be in `Builder`
        self.verbose = verbose

        # The relative path to the target file
        self.target_file = find_package(path)

        # The absolute path to the target directory
        self.resolved_path = resolve_path(self.target_file)

        # The name of the package to be released
        self.name = get_name(self.target_file)

        # The version number as set in the __version__ variable
        self.version = get_version(self.target_file)

        # Returns a dict containing config file data, such as
        # the .pypirc and .gitconfig data
        self.user_info = get_user_info()  # Log each step and ensure is valid

        # The name of the developer or author of the release
        self.author = get_author(self)

        # The authors email
        self.author_email = get_author_email(self)

        # A dict containing a description of the package
        # and a variable containing the imported file.
        self.package_info = get_package_info(self.name, self.resolved_path)  # Show preview, cancel if no good

        # The package description as taken from package info.
        self.description = self.package_info['description']

        # Returns True if the target package is a single file.
        self.is_single_file = os.path.isfile(self.target_file)

        # A list of dependencies to to be added to requirements.txt
        self.requirements = get_dependencies(self.target_file)

        # Returns True if the target has a `main` function
        self.is_script = has_main_func(self.target_file)

        # For the MANIFEST.in file
        self.find_packages = "" if self.is_single_file else ", find_packages"

        # The license the package will be released under.
        self.license = get_license(self.target_file)

        self.errors = None

    @property
    def is_data_files(self):
        """Returns True if there is a data folder in the resolved path
         """
        return os.path.exists(os.path.join(self.resolved_path, 'data'))

    @property
    def url(self):
        """Returns the URL that the package will be hosted on"""
        return 'https://pypi.python.org/pypi/' + self.name

    def jsonize(self):
        """Returns a dict of the PyPackage attributes and their values
         """
        rv = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.update({k: v})
        return rv

    def __str__(self):
        rv = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            rv.append("{}: {}".format(k, v))
        return "\n".join(rv)
