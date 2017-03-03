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

    def __init__(self, path, build_dir=None, verbose=False):
        self.verbose = verbose

        self.target_file = find_package(path)  # If package no good, PANIC

        self.name = get_name(self.target_file)

        self.resolved_path = resolve_path(self.target_file)  # Absolute dir of package

        self.user_info = get_user_info()  # Log each step and ensure is valid

        self.author = get_author(self)

        self.author_email = get_author_email(self)

        self.package_info = get_package_info(
            self.name, self.resolved_path)  # Show preview, cancel if no good

        self.is_single_file = os.path.isfile(self.target_file)

        self.requirements = get_dependencies(self.target_file)

        self.is_script = has_main_func(self.target_file)

        self.version = get_version(self.target_file)

        self.find_packages = "" if self.is_single_file else ", find_packages"

        self.description = self.package_info['description']

        self.errors = None

    def set_license(self, value):
        try:
            self.package_info['license'] = value
            logger.info("License set to: %s", value)
        except (KeyError, ValueError) as e:
            logger.error(
                "There was an error setting the License.", exc_info=True)

    def set_version(self, new_version):
        if LooseVersion(new_version) >= LooseVersion(self.version):
            self.version = new_version
            logger.info("Version set to: %s", new_version)
            return True
        else:
            logger.warning("Version not in valid range: %s", new_version)
            return None

    @property
    def is_data_files(self):
        return os.path.exists(os.path.join(self.resolved_path, 'data'))

    @property
    def license(self):
        return self.package_info['license']

    @property
    def license_name(self):
        return self.package_info['license_name']

    @property
    def url(self):
        return 'https://pypi.python.org/pypi/' + self.name

    def jsonize(self):
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

    @staticmethod
    def load_package(target, verbose):
        try:
            rv = PyPackage(target, verbose=verbose)
        except Exception as e:
            logger.error("load_package error traceback: (%s)", exc_info=True)
            return None
        else:
            return rv
