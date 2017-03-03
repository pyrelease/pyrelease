# coding=utf-8
from __future__ import print_function, absolute_import
import os
import sys
import re
import ast
import imp
import logging

from .userdata import PyPiRc, GitConfig


# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class InvalidPackage(Exception):
    pass


class InvalidPackageName(Exception):
    pass


def find_package(target):
    """ Returns the absolute path to the package file.

    Is there a .py file for this repo or a __init__.py ?

    package_py('.')
    package_py('mypackage.py')
    package_py('/Users/bla/packagefolder/')

    This detects single file packages, and packages with __init__.py in them.
    """

    if not os.path.exists(target):
        logger.error("Target path not valid with pyrelease (%s)", target)
        raise InvalidPackage("Must enter a valid path.")

    if os.path.isdir(target) and os.path.exists(os.path.join(target, 'setup.py')):
        logger.error("PyRelease doesn't work with existing setup.py files")
        raise InvalidPackage("setup.py file detected.")

    if target.endswith('.py') and os.path.isfile(target):
        if "-" in target:
            raise InvalidPackageName("Filename cannot contain dashes.")
        # Single file package, just what we want.
        logger.info("Single file target found (%s)", target)
        return os.path.abspath(target)

    elif os.path.isdir(target) or target == '.':
        # lets see if there is a __init__.py in there.
        path = os.path.join(target, '__init__.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            return os.path.abspath(path)

        # maybe there is a file with the same name as the folder?
        folder_name = os.path.split(os.path.abspath(target))[-1]
        if "-" in folder_name:
            raise InvalidPackageName("Cannot find a valid module to release.")

        path = os.path.join(target, folder_name + '.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            return os.path.abspath(path)

        # Check for an __init__.py file in there while we're at it.
        path = os.path.join(target, folder_name, '__init__.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            return os.path.abspath(path)

        logger.error("No valid package found in. (%s)", target)
        exit()
    else:
        logger.error("Pyrelease only supports single file package release.")
        exit()


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


def get_version(py_file):
    """Regex for scraping the license from a python file"""
    VERSION_REGEX = re.compile(r"(?:(\d+\.(?:\d+\.)*\d+))", re.S)
    with open(py_file, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("__version__"):
                version = re.search(VERSION_REGEX, line).group()
                logger.info("Version found - %s -", str(version))
                return version
    logger.warning("No version found in - %s -", py_file)
    return False


#         try:
#             versions = subprocess.check_output('git tag --sort version:refname'.split())
#         except subprocess.CalledProcessError as e:
#             logging.error("Error getting version from git. (%s)", exc_info=True)
#             return
#         else:
#             lines = versions.splitlines()
#             if lines:
#                 version = lines[-1].decode('utf-8')
#                 logger.info("Version found in git. - %s -", str(version))
#                 return version


def get_license(target):
    """And another regex for scraping the license from a python file.."""
    # TODO: Show some resources
    # https://choosealicense.com/
    with open(target, 'r') as f:
        py_file = f.readlines()
        for line in py_file:
            line = line.strip()
            if line.startswith("__license__"):
                license_match = line[14:].replace('"', '').replace("'", "")
                logger.info("License line found in - %s -", target)
                return license_match
                # TODO: Fix me :(
                # if license_match.upper() == 'MIT':
                #     _license = license_match.group(1)
                #     # return _license
                #     url = 'https://opensource.org/licenses/' + license_match
                #     print(url)
                #     resp = urllib.request.urlopen(url).read().decode('utf-8')
                #     logger.info("License found in (%s) file. - %s -", str(target), str(license_match))
                #     # resp = json.loads(resp)
                #     pprint.pprint(resp)
                #     print(resp['identifiers']['text'])
                #     input()
            # logger.warning("Still no license string :/")
    logger.warning("No license line found in - %s -", target)
    return None


def get_package_info(name, package_dir):
    """Imports the module and collects license, and description.
     This info is returned as a dict which also contains a pointer
     to the imported module.
     """
    sys.path.insert(0, package_dir)
    try:
        logger.info("Importing module - %s -", name)
        mod = __import__(name)
    except Exception as e:
        logger.error(
            "Error importing module build_docs function (%s)", exc_info=True)
    else:
        entry = mod.__dict__[mod.__all__[0]]
        description = ""
        if entry.__doc__:
            description = entry.__doc__
        logger.info("Description: %s", str(description))
        _license = get_license(os.path.join(package_dir, name + ".py"))
        rv = dict(
            module=mod,
            license=_license,
            license_name=_license,
            description=description)
        logger.info("Get package info returned: %s", str(rv.keys()))
        return rv


def get_author(package):
    rv = package.user_info['pypirc'].author
    if rv is None:
        rv = package.user_info['gitconfig'].author
    logger.info("Get author function returned: %s", str(rv))
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
    return os.path.abspath(
            os.path.dirname(target_path))


def get_name(path):
    """ We can get this by looking at what is there.

     Is there a single python file? 'leftpad.py' -> 'leftpad'
     Is there a single folder of python files? 'leftpad/' -> 'leftpad'
     If it is '.' then we use the folder name -> 'leftpad'
     """
    if path is None:
        logger.error("Target is None..")
        exit()
    logger.info("Target: %s", path)
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
    module = ast.parse(open(target).read())
    deps = []
    for node in module.body:
        if type(node) is ast.Import:
            for name in node.names:
                parts = imp.find_module(name.name.split('.')[0])
                if 'site-package' in parts[1]:
                    deps.append(name.name.split('.')[0])
        if type(node) is ast.ImportFrom:
            parts = imp.find_module(node.module.split('.')[0])
            if 'site-package' in parts[1]:
                deps.append(node.module.split('.')[0])
    parsed_deps = []
    for dep in deps:
        parsed_deps.append(conversions.get(dep, dep))
    logger.info("Found dependencies. (%s)", "\n".join(parsed_deps))
    return parsed_deps
