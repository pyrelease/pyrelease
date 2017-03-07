# coding=utf-8
from __future__ import print_function, absolute_import
import os
import sys
import re
import ast
import imp
import logging

from .userdata import PyPiRc, GitConfig

logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class InvalidPackage(Exception):
    pass


class InvalidPackageName(Exception):
    pass


def find_package(what_to_package):
    """ Returns the path to the package file if found
     to be compatible with PyRelease.

    Is there a .py file for this repo or a __init__.py ?

    package_py('.')
    package_py('mypackage.py')
    package_py('/Users/bla/packagefolder/')

    This detects single file packages, and packages with __init__.py in them.
    """
    if what_to_package.endswith('.py'):
        if not os.path.exists(what_to_package):
            logger.info("Doesn't exist! (%s)", what_to_package)
        logger.info("What to package ends with .py - (%s)", what_to_package)
        folder = os.getcwd()
        apath = os.path.join(folder, what_to_package)
        return os.path.relpath(apath)

    if os.path.isdir(what_to_package) or what_to_package == '.':
        # maybe there is a file with the same name as the folder?
        folder_name = os.path.split(os.path.abspath(what_to_package))[-1]
        apath = os.path.join(what_to_package, folder_name + '.py')
        if os.path.exists(apath):
            logger.info("Found file with same name as folder - (%s)", apath)
            return os.path.relpath(apath)

        # lets see if there is a __init__.py in there.
        apath = os.path.join(what_to_package, '__init__.py')
        if os.path.exists(apath):
            logger.info("What to package found - (%s)", apath)
            return os.path.relpath(apath)

        apath = os.path.join(what_to_package, folder_name, '__init__.py')
        if os.path.exists(apath):
            logger.info("Found __init__.py - (%s)", apath)
            return os.path.relpath(apath)
    else:
        logger.warning("No valid package found! (%s)", what_to_package)


def get_user_info():
    """Fetches user info from .gitconfig, .pypirc and .hgrc files
     if they exist and returns them as a dict."""
    rv = {
        "gitconfig": GitConfig(),
        "pypirc": PyPiRc(),
        # "hgrc":      HgRc()
    }
    logger.info("Got user info (%s)", str(rv))
    return rv


def get_version(module):
    try:
        ver = module.__version__
    except AttributeError:
        logger.warning("No version found.")
        return None
    else:
        logger.info("Version found - %s -", str(ver))
        return ver


def get_license(module):
    try:
        ver = module.__license__
    except AttributeError:
        logger.warning("No license found.")
        return None
    else:
        logger.info("License found - %s -", str(ver))
        return ver


def import_target_package(package_dir):
    """Imports the module"""
    name = os.path.basename(package_dir)
    logger.info("called with - %s - %s", name, package_dir)
    if name.endswith(".py"):
        name = name[:-3]
    package_dir = os.path.abspath(os.path.dirname(package_dir))
    logger.info("Importing module - %s -", name)
    logger.info("Importing module from dir - %s -", package_dir)
    sys.path.insert(0, package_dir)
    try:
        mod = __import__(name)
    except ImportError as e:
        logger.warning(
            "Error importing module %s", name)
        return None
    else:
        return mod


def get_description(mod):
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
                "Unable to find get a description for (%s)", mod.__name__)
        return description


def get_author(package):
    if hasattr(package.module, "__author__"):
        return package.module.__author__
    rv = package.user_info['pypirc'].author
    if rv is not None:
        return rv
    rv = package.user_info['gitconfig'].author
    if rv is not None:
        return rv


def get_author_email(package):
    rv = package.user_info['gitconfig'].author_email
    logger.info("Get author email function returned: %s", str(rv))
    return rv


def version_from_git():
    # TODO: Implement me!
    raise NotImplementedError


def migrate_version(file, new_version):
    version_regex = re.compile(r"(?:(\d+\.(?:\d+\.)*\d+))", re.S)
    new_file = []
    for line in file:
        if line.startswith("__version__"):
            line = re.sub(version_regex, new_version, line)
            new_file.append(line)
            continue
        new_file.append(line)
    return new_file


def resolve_path(target_path):
    return os.path.abspath(target_path)


def get_name(path):
    """ We can get this by looking at what is there.

     Is there a single python file? 'leftpad.py' -> 'leftpad'
     Is there a single folder of python files? 'leftpad/' -> 'leftpad'
     If it is '.' then we use the folder name -> 'leftpad'
     """
    logger.info("Target: %s", path)
    if os.path.basename(path) == '__init__.py':
        dir_name = os.path.split(os.path.abspath(path))[-2]
        rv = os.path.basename(dir_name)
        logger.info("get_name using directory name for __init__.py result: %s", str(rv))
        return rv

    if path.endswith('.py'):
        rv = os.path.split(path)[-1].rstrip('.py')
        logger.info("get_name found a name from a *.py file: %s", str(rv))
        return rv

    if os.path.isdir(path):
        rv = os.path.split(os.path.abspath(path))[-1]
        logger.info("get_name found a directory for the result: %s", str(rv))
        return rv


def has_main_func(target):
    """Looks for the text 'def main' in the target file and returns
     True if found, else returns False
     """
    with open(target, 'r') as f:
        if 'def main' in f.read():
            logger.info("Package has a main function.")
            return True
        else:
            logger.info("Package does not have a main function.")
            return False


def get_dependencies(target):
    """Try to find 3rd party dependencies in the past in .py file.
     Some packages go by a different PyPi name so they are run through
     a conversion first, if the dependency is found in the conversion
     dict then it is swapped.

     Conversion keys must be added manually here.

     Returns a list of package names.
     """
    # TODO: Make this look for a requirements.tx file also
    # TODO: Get more popular conversions.
    conversions = dict(yaml='pyyaml')

    # So ast can import the target we must add it's
    # directory to the system path.
    abs_path = os.path.abspath(target)
    sys.path.insert(0, abs_path)

    module = ast.parse(open(target).read())
    deps = []
    for node in module.body:
        if type(node) is ast.Import:
            for name in node.names:
                parts = imp.find_module(name.name.split('.')[0])
                try:
                    if 'site-package' in parts[1]:
                        rv = name.name.split('.')[0]
                        deps.append(rv)
                        logger.info("Found dependency: %s", rv)
                except TypeError:
                    pass

        if type(node) is ast.ImportFrom:
            parts = imp.find_module(node.module.split('.')[0])
            try:
                if 'site-package' in parts[1]:
                    rv = node.module.split('.')[0]
                    deps.append(rv)
                    logger.info("Found dependency: %s", rv)
            except TypeError:
                pass

    parsed_deps = []
    for dep in deps:
        converted = conversions.get(dep, None)
        if converted is not None:
            dep = converted
        parsed_deps.append(dep)
    if parsed_deps:
        logger.info("Parsed dependencies. (%s)", ", ".join(parsed_deps))
    return parsed_deps
