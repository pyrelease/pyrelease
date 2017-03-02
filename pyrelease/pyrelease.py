from __future__ import print_function, absolute_import
import os
import sys
import re
import ast
import imp
import datetime
import subprocess
import logging
import pydoc
import tempfile
from shutil import copy as copy_to_dir
from shutil import copytree as copy_dir
from distutils.version import LooseVersion

from .userdata import PyPiRc, GitConfig, HgRc
from .templates import readme_rst, manifest_in, setup_py
from .shelltools import execute_shell_command, ignore_stdout, dir_context
from .licenses import MIT, UNLICENSE, APACHE_2, GPL_3, BSD_2, BSD_3, LGPL_2, LGPL_3
from .compat import input, devnull

# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


def find_package(target):
    """ Returns the absolute path to the package file.

    Is there a .py file for this repo or a __init__.py ?

    package_py('.')
    package_py('mypackage.py')
    package_py('/Users/bla/packagefolder/')

    This detects single file packages, and packages with __init__.py in them.
    """

    class InvalidPackage(Exception):
        pass

    class InvalidPackageName(Exception):
        pass

    if not os.path.exists(target):
        raise InvalidPackage("Must enter a valid path.")

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
    return None


def get_package_info(name, package_dir):
    """Imports the module and collects license, and description.
     This info is returned as a dict which also contains a pointer
     to the imported module.
     """
    sys.path.insert(0, package_dir)
    try:
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
        return rv


def get_author(package):
    rv = package.user_info['pypirc'].author
    if rv is None:
        rv = package.user_info['gitconfig'].author
    return rv


def get_author_email(package):
    rv = package.user_info['gitconfig'].author_email
    return rv


def version_from_git():
    # TODO: Implement me!
    raise NotImplementedError


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
        return os.path.split(path)[-1].rstrip('.py')

    if os.path.isdir(path):
        return os.path.split(os.path.abspath(path))[-1]


def has_main_func(target):
    """Looks for the text 'def main' in the target file and returns
     True if found, else returns False
     """
    with open(target, 'r') as f:
        if 'def main' in f.read():
            return True
        else:
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
    conversions = dict(
        yaml='pyyaml'
    )
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

        self.package_dir = os.path.abspath(
            os.path.dirname(self.target_file))  # Absolute dir of package

        self.user_info = get_user_info()  # Log each step and ensure is valid

        self.author = get_author(self)

        self.author_email = get_author_email(self)

        self.package_info = get_package_info(
            self.name, self.package_dir)  # Show preview, cancel if no good

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
        except (KeyError, ValueError) as e:
            logger.error(
                "There was an error setting the License.", exc_info=True)

    def set_version(self, new_version):
        if LooseVersion(new_version) >= LooseVersion(self.version):
            self.version = new_version
            return True
        else:
            return None

    @property
    def is_data_files(self):
        return os.path.exists(os.path.join(self.package_dir, 'data'))

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


class Builder(object):
    """Builds pypackage project and uploads to PyPi.

    Errors during build will set the self.errors switch to True
    indicating there was an error.
    """

    default_commands = dict(builds=[
        "python setup.py sdist",
        "python setup.py bdist_wheel --universal",
    ])

    LICENSES = {
        'APACHE-2': APACHE_2.TEMPLATE,
        'GPL-3': GPL_3.TEMPLATE,
        'BSD-2': BSD_2.TEMPLATE,
        'BSD-3': BSD_3.TEMPLATE,
        'LGPL-2': LGPL_2.TEMPLATE,
        'LGPL-3': LGPL_3.TEMPLATE,
        'MIT': MIT.TEMPLATE,
        'UNLICENSE': UNLICENSE.TEMPLATE,
    }
    pypi_url = r"https://pypi.python.org/pypi"
    pypi_test_url = r"https://testpypi.python.org/pypi"
    # dists_folder = None

    def __init__(self, package, build_dir=None, test=False):
        self.package = package
        self.verbose = package.verbose
        self.file_name = package.target_file + ".py"

        # Set True to upload to PyPi test server.
        self.use_test_server = test

        # Mainly to keep track of Twine and setuptools error responses
        self.errors = []

        # Where this stuff will end up.
        if build_dir is None:
            build_dir = os.path.join(
                os.getcwd(), self.package.name + str(self.package.version))
        self.build_dir = os.path.abspath(build_dir)
        self.dists_folder = self.build_dir

    @property
    def worker_count(self):
        return len(self.workers)

    @property
    def workers(self):
        return [i for i in self.__dict__.keys() if i.startswith("build_")]

    def copy_files(self):
        """Copies our package files into the new output folder.
        """
        if not self.package.is_single_file:
            # TODO: No reason why we couldn't glob all the .py files and send em all over too.. Panic for now.
            raise NotImplementedError('only single files supported')

        copy_to_dir(self.package.target_file, self.build_dir)

    def make_all(self):
        """ Help method to just giver and build the whole thing"""
        # self.build_docs() # Broken
        self.build_target_dir()
        self.build_readme()
        self.build_license()
        self.build_manifest()
        self.build_requirements()
        self.build_setup()
        self.build_package()
        # TODO: Keep track of progress and report errors..
        return self.errors

    def build_target_dir(self):
        if os.path.exists(self.build_dir):
            if "__" in self.build_dir[:-5]:
                last = int(self.build_dir[-1])
                last += 1
                self.build_dir += "__%s" % last
            else:
                self.build_dir += "__1"
        try:
            os.mkdir(self.build_dir)
        except OSError:
            return False
        else:
            return self.build_dir

    def build_package(self, count=1):
        """Copies the project file and data folders to the build destination"""
        if self.package.is_data_files:
            if count == 10:
                return "You should clean up some of those directories.."
            data_folder = os.path.join(self.package.package_dir, 'data')
            dest = os.path.join(self.build_dir, 'data')
            try:
                copy_dir(data_folder, dest)
            except FileExistsError:
                new_dir = self.package.package_dir + "_%s" % count
                self.package.package_dir = new_dir
                self.build_package(count + 1)
        self.copy_files()

    def build_readme(self):
        """Builds your projects README.rst file from a template."""
        rv = readme_rst.TEMPLATE.format(
            name=self.package.name,
            description=self.package.description,
            author_email=self.package.author_email,
            author=self.package.author,
            version=self.package.version,
            url=self.package.url,
            is_script=self.package.is_script,
            find_packages=self.package.find_packages,
            # TODO License should return a dict, with `name` and `text` as keys
            license=self.package.license,
            license_name=self.package.license_name)
        self.package.PACKAGE_FILES['readme_rst'] = rv
        with open(os.path.join(self.build_dir, "README.rst"), 'w') as f:
            f.write(rv)
        return rv

    # TODO: This could probably go somewhere else.
    def preview_readme(self):
        """Open a preview of your readme in restview."""
        if not self.package.PACKAGE_FILES['readme_rst']:
            self.build_readme()
        with dir_context(self.build_dir):
            logger.info("Opening README.rst in restview. ")
            with ignore_stdout():
                shell = subprocess.Popen(
                    "restview README.rst".split(" "), stdout=devnull)
            return shell

    def build_manifest(self):
        """Fills in your releases MANIFEST.in file """
        include_data_files = 'recursive-include data *' if self.package.is_data_files else ''
        include_docs_folder = 'include docs/*'
        rv = manifest_in.TEMPLATE.format(
            include_data_files=include_data_files,
            include_docs_folder=include_docs_folder)
        self.package.PACKAGE_FILES['manifest_in'] = rv
        with open(os.path.join(self.build_dir, 'MANIFEST.in'), 'w') as f:
            f.write(rv)

    def build_setup(self):
        """Build out the setup.py file for the release."""
        if self.package.is_script:
            console_scripts = setup_py.CONSOLE_SCRIPTS.format(self.package.name,
                                                              self.package.name)
        else:
            console_scripts = ''

        if self.package.is_single_file:
            py_modules = "py_modules=['%s']," % self.package.name
            packages = ''
        else:
            raise NotImplementedError('only single files supported')
            # py_modules = ''
            # packages = "packages=find_packages(exclude=['contrib', 'docs', 'tests']),"

        install_requires = "install_requires=%s," % repr(self.package.requirements)

        rv = setup_py.TEMPLATE.format(
            url=self.package.url,
            name=self.package.name,
            version=self.package.version,
            license=self.package.license,
            description=self.package.description,
            author=self.package.author,
            author_email=self.package.author_email,
            console_scripts=console_scripts,
            install_requires=install_requires,
            packages=packages,
            py_modules=py_modules,
            find_packages=self.package.find_packages,
            long_description=self.package.PACKAGE_FILES['readme_rst'], )
        self.package.PACKAGE_FILES['setup_py'] = rv
        with open(os.path.join(self.build_dir, 'setup.py'), 'w') as f:
            f.write(rv)

    def build_license(self):
        """ Creates a license file by looking in your script for a
         __license__ = 'something' line.. MIT is default

         Supports:

             APACHE-2
             GPL-3
             BSD-2
             BSD-3
             LGPL-2
             LGPL-3
             default: MIT
             UNLICENSE
         """

        template = self.LICENSES.get(self.package.license, None)
        if template is None:
            template = self.LICENSES['MIT']

        rv = template.format(
            name=self.package.name,
            author=self.package.author,
            year=str(datetime.datetime.now().year))

        self.package.PACKAGE_FILES['license_md'] = rv
        with open(os.path.join(self.build_dir, "LICENSE.md"), 'w') as f:
            f.writelines(rv)

    # TODO: Fix me :(
    # def build_docs(self):
    #     """Builds a pydoc API documention of your script in html"""
    #     docs_folder = os.path.abspath(os.path.join(self.build_dir, 'docs'))
    #     if not os.path.exists(docs_folder):
    #         os.mkdir(docs_folder)
    #     mod = self.package.package_info['module']
    #     title = "{}: %s".format(self.package.name)
    #     html = pydoc.render_doc(mod, title)
    #     self.package.PACKAGE_FILES['license_md'] = html
    #     with open(os.path.join(self.build_dir, 'docs', 'index.html'),
    #               'w') as f:
    #         f.write(html)

    def build_requirements(self):
        """Writes the requirements.txt file"""
        with open(os.path.join(self.build_dir, "requirements.txt"), 'w') as f:
            f.write("\n".join([i for i in self.package.requirements]))

    def build_distros(self, suppress=False):
        """Builds out project distros, console output can be suppressed
         by setting show_output to True.
         """
        suppress = suppress or self.verbose
        with dir_context(self.dists_folder):
            for cmd in self.commands:
                # TODO: This needs to be better. Not enough info on the build.
                logger.info("Executing command - %s", str(cmd))
                execute_shell_command(cmd, suppress=suppress)
                logger.info("Done.")

    def upload_to_pypi(self, suppress=False):
        """Uploads package to PyPi using twine.
        The advantage to using Twine is your package is uploaded
        over HTTPS which prevents your private info from appearing
        in the request header. (Apparently setuptools uploads over
        https now as well, so find out more about that.
        """
        # TODO: This doesn't need to be twine anymore. ALTHOUGH, make sure ...
        # the default pip or setuptools uses https _without_ needing to be
        # upgraded first. Because if not, that makes twine the most secure
        # way.
        suppress = suppress or self.verbose
        if not os.path.exists(os.path.expanduser('~/.pypirc')):
            msg = (
                "No .pypirc found. Please see "
                "https://docs.python.org/2/distutils/packageindex.html#pypirc "
                "for more info."
            )
            logger.warning(msg)
            self.errors.append(msg)
            return
        logger.info("Uploading Project to the Pypi server..")
        with dir_context(self.dists_folder):
            response = execute_shell_command(
                "twine upload dist/*", suppress=suppress)
            logger.info("Project has been uploaded to the Pypi server!")
            logger.debug("Result: %s", repr(response))
            self.parse_response(response)
        return response

    def register_pypi_test_package(self, suppress=False):
        """Registers your package with the PyPi test site. This step doesn't
         seem to be necessary for the regular PyPi site though..
         """
        # TODO: Needs research.. See docstring.
        suppress = suppress or self.verbose
        with dir_context(self.dists_folder):
            logger.info("Uploading Project to the Pypi TESTING server..")
            cmd = "python setup.py register -r %s" % self.pypi_test_url
            response = execute_shell_command(cmd, suppress=suppress)
            self.parse_response(response)
        return response

    def upload_to_pypi_test_site(self, suppress=False):
        """Uploads your package to the PyPi repository allowing others
        to download easily with pip"""
        suppress = suppress or self.verbose
        with dir_context(self.dists_folder):
            logger.info("Uploading Project to the Pypi TESTING server..")
            response = execute_shell_command(
                "twine upload dist/* -r testpypi", suppress=suppress)
            logger.info(
                "Project has been uploaded to the Pypi TESTING server!")
            logger.debug("Result: %s", repr(response))
            # TODO: This needs to be better..
            self.parse_response(response)
        return response

    def parse_response(self, response):
        """Trying some things out to handle shell errors better while
         calling Twine.."""
        if response == 127:
            msg = "(%s) - Twine not installed.. Cancelled." % response
            logger.info(msg)
            self.errors.append(msg)
        if response == 400:
            msg = "(%s) - Needs to upgrade version.." % response
            logger.debug(msg)
            self.errors.append(msg)
        if response == 401:
            msg = "(%s) - Invalid login credentials." % response
            logger.debug(msg)
            self.errors.append(msg)

    @property
    def commands(self):
        """Returns the build commands to be used."""
        return self.default_commands['builds']

    @property
    def success(self):
        """Get build and deploy status.

        If self.errors is None, then no builds have been
        attempted yet. Otherwise returns False if an error
        was detected, True if build was a success.
        """
        if self.errors is None:
            return False
        return not self.errors


########################################################################
########################################################################


def main(*args):
    """ Main entry point for now until I get the click interface working.
     Please use the logger and not print in this file, screen prints will
     all be done from the cli and I don't want the logger to interfere if
     I can help it."""
    from .cli import main

    main(*args)

    args = sys.argv

    # --------------------------------------------- Package creation

    package = PyPackage(args[1])
    print("Package loaded.")

    input(
        "Press enter to continue on to the build stage. Or press ctrl-c to exit."
    )
    builder = Builder(package, test=True)

    # Test means upload to test site ore not.
    print("Builder loaded")

    builder.build_docs()
    print("index.html built")

    builder.build_readme()
    print("readme.rst built")

    builder.build_license()
    print("LICENSE.md built")

    builder.build_manifest()
    print("manifest.in built")

    builder.build_requirements()
    print("requirements.txt built")

    builder.build_setup()
    print("setup.py file built")

    print("Previewing in browser.")
    builder.preview_readme()
    # ------------------------------------------------

    # Create the package for the Builder.F
    builder.build_package()
    print("Package created")

    # ------------------------------------------------- Build commands

    # show_output turns on console output
    # for the various setup.py build commands
    # and any pypi upload commands.
    builder.build_distros(suppress=True)
    print("Package built")

    if builder.use_test_server:
        print("PyPi server is set to TESTING server.")
    else:
        print("PyPi server is set to NORMAL server.")
    input(
        "Press enter to continue on to the upload step. Or press ctrl-c to exit."
    )
    # There is an input sentinal that will allow you to
    # Exit before any attempt to upload is made.
    builder.upload_to_pypi()
    if builder.success:
        print("Package up-loaded successfully.")
        state = "TEST server" if builder.use_test_server else "server"
        print("Thanks for using PyRelease, your completed files can be "
              "found in the %s directory, and on the PyPi %s" %
              (builder.build_dir, state))
    else:
        print("Build completed with errors..")


if __name__ == '__main__':
    main()
