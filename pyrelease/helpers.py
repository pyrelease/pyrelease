# coding=utf-8
from __future__ import print_function, absolute_import
import os
import sys
import re
import ast
import imp
import logging


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


def version_from_git():
    # TODO: Implement me!
    raise NotImplementedError


def migrate_source_attribute(attr, to_this, target_file, regex):
    """Updates __magic__ attributes in the source file"""
    change_this = re.compile(regex, re.S)
    new_file = []
    found = False

    with open(target_file, 'r') as fp:
        lines = fp.readlines()

    for line in lines:
        if line.startswith(attr):
            found = True
            line = re.sub(change_this, to_this, line)
        new_file.append(line)

    if found:
        with open(target_file, 'w') as fp:
            fp.writelines(new_file)


def migrate_author(target_file, new_author):
    """Updates __author__ in the source file"""
    regex = r'\s*([^"\']*)\s*'
    migrate_source_attribute('__author__', new_author, target_file, regex)


def migrate_version(target_file, new_version):
    """Updates __version__ in the source file"""
    regex = r"(?:(\d+\.(?:\d+\.)*\d+))"
    migrate_source_attribute('__version__', new_version, target_file, regex)


def migrate_license(target_file, new_license):
    """Updates __license__ in the source file"""
    regex = r'\s*([^"\']*)\s*'
    migrate_source_attribute('__license__', new_license, target_file, regex)


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
                    # Sometimes parts is None and throws a TyoeError
                    # I think this is from __future__ imports, but
                    # this fixes it from crashing anyways
                    pass

        if type(node) is ast.ImportFrom:
            parts = imp.find_module(node.module.split('.')[0])
            try:
                if 'site-package' in parts[1]:
                    rv = node.module.split('.')[0]
                    deps.append(rv)
                    logger.info("Found dependency: %s", rv)
            except TypeError:
                # This is passed for the same reason as above
                pass
    parsed_deps = []

    # Some dependencies go by a different name than their PyPi
    # counterparts. This is an easy way to convert known cases
    # until something proves to work better.
    conversions = dict(yaml='pyyaml')
    for dep in deps:
        converted = conversions.get(dep, None)
        if converted is not None:
            dep = converted
        parsed_deps.append(dep)
    if parsed_deps:
        logger.info("Parsed dependencies. (%s)", ", ".join(parsed_deps))
    return parsed_deps
