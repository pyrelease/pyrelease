import os
import sys
import re
import ast
import time
import imp
import datetime
import subprocess
import contextlib
import logging
import pydoc
import tempfile
from shutil import copy as copy_to_dir
from shutil import copytree as copy_dir

from .userdata import PyPiRc, GitConfig, HgRc
from .templates import readme_rst, manifest_in, setup_py
from .shelltools import execute_shell_command, ignore_stdout
from .licenses import MIT

# ######## LOGGING #########
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler
# handler = logging.FileHandler(os.path.join(os.getcwd(), 'build.log'), 'w')
# handler.setLevel(logging.INFO)
# formatter = logging.Formatter(
#     '%(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# Stream handler
s_handler = logging.StreamHandler()
s_handler.setLevel(logging.DEBUG)
s_formatter = logging.Formatter('%(message)s')
s_handler.setFormatter(s_formatter)
logger.addHandler(s_handler)

INTERVAL = 0.5


def slow_log(arg, interval=1):
    """ This function merely slows down the build steps in the main
     function below by introducing `interval` which can be customized
     as seconds between commands. ie `0.5` = half a second, `1` = one
     second, etc.."""
    time.sleep(interval)
##############################


def find_package(target):
    """ Returns the absolute path to the package file.

    Is there a .py file for this repo or a __init__.py ?

    package_py('.')
    package_py('mypackage.py')
    package_py('/Users/bla/packagefolder/')

    This detects single file packages, and packages with __init__.py in them.
    """
    class InvalidPackage(Exception): pass

    class InvalidPackageName(Exception): pass

    if not os.path.exists(target):
        raise InvalidPackage("Must enter a valid path.")

    if target.endswith('.py') and os.path.isfile(target):
        if "-" in target:
            raise InvalidPackageName("Filename cannot contain dashes." )
        # Single file package, just what we want.
        logger.info("Single file target found (%s)", target)
        time.sleep(INTERVAL) ###### -----------------------------------------<<<<<<<<<<<<<
        return os.path.abspath(target)

    elif os.path.isdir(target) or target == '.':
        # lets see if there is a __init__.py in there.
        path = os.path.join(target, '__init__.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
            return os.path.abspath(path)

        # maybe there is a file with the same name as the folder?
        folder_name = os.path.split(os.path.abspath(target))[-1]
        if "-" in folder_name:
            raise InvalidPackageName("Cannot find a valid module to release.")

        path = os.path.join(target, folder_name + '.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
            return os.path.abspath(path)

        # Check for an __init__.py file in there while we're at it.
        path = os.path.join(target, folder_name, '__init__.py')
        if os.path.exists(path):
            logger.info("Single file target found (%s)", path)
            time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
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
        "pypirc":    PyPiRc(),
        "hgrc":      HgRc()
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
                time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
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
    logger.warning("Still no license string :/")
    time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
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
        logger.error("Error importing module build_docs function (%s)", exc_info=True)
        time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
    else:
        entry = mod.__dict__[mod.__all__[0]]
        description = ""
        if entry.__doc__:
            description = entry.__doc__
        logger.info("Description: %s", str(description))
        time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
        _license = get_license(os.path.join(package_dir, name + ".py"))
        rv = dict(
            module=mod,
            license=_license,
            license_name=_license,
            description=description
        )
        return rv


def get_author():
    """Fallback for getting author name when no config files are found. Should be Github username"""
    return input("Enter the name of the author, this should be your github user name: ")


def get_author_email():
    """Fallback for getting user email address when no config files are found."""
    return input("Enter e-mail to show on the readme: ")


def version_from_git():
    # TODO: Implement me!
    return "0.5.5"


def get_name(path):
    """ We can get this by looking at what is there.

     Is there a single python file? 'leftpad.py' -> 'leftpad'
     Is there a single folder of python files? 'leftpad/' -> 'leftpad'
     If it is '.' then we use the folder name -> 'leftpad'
     """
    if path is None:
        logger.error("Target is None..")
        time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
        exit()
    logger.info("Target: %s", path)
    time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
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
    time.sleep(INTERVAL)  ###### -----------------------------------------<<<<<<<<<<<<<
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

    def __init__(self, path, build_dir='.'):
        self.target_file = find_package(path)                                    # If package no good, PANIC

        self.name = get_name(self.target_file)

        self.package_dir = os.path.abspath(os.path.dirname(self.target_file))    # Absolute dir of package

        self.user_info = get_user_info()                                         # Log each step and ensure is valid

        self.package_info = get_package_info(self.name, self.package_dir)              # Show preview, cancel if no good

        self.build_dir = tempfile.mkdtemp(dir=build_dir)

        self.is_single_file = os.path.isfile(self.target_file)

        self.requirements = get_dependencies(self.target_file)

        self.is_script = has_main_func(self.target_file)

        self.version = get_version(self.target_file)

        self.find_packages = "" if self.is_single_file else ", find_packages"

        self.long_description = self.build_readme()

    @property
    def author(self):
        rv = self.user_info['pypirc'].author
        if rv is None:
            rv = self.user_info['gitconfig'].author
        if rv is None:
            return get_author()
        return rv

    @property
    def author_email(self):
        rv = self.user_info['pypirc'].author_email
        if rv is None:
            rv = self.user_info['gitconfig'].author_email
        if rv is None:
            return get_author_email()
        return rv

    @property
    def description(self):
        return self.package_info['description']

    @property
    def license(self):
        return self.package_info['license']

    @property
    def license_name(self):
        return self.package_info['license_name']

    @property
    def url(self):
        return 'https://pypi.python.org/pypi/' + self.name

    @property
    def is_data_files(self):
        return os.path.exists(os.path.join(self.package_dir, 'data'))

    def build_readme(self):
        """Builds your projects README.rst file from a template."""
        rv = readme_rst.TEMPLATE.format(
            name=self.name,
            description=self.description,
            author_email=self.author_email,
            author=self.author,
            version=self.version,
            url=self.url,
            is_script=self.is_script,
            find_packages=self.find_packages,
            # TODO License should return a dict, with `name` and `text` as keys
            license=self.license,
            license_name=self.license_name
        )
        self.PACKAGE_FILES['readme_rst'] = rv
        with open(os.path.join(self.build_dir, "README.rst"), 'w') as f:
            f.write(rv)
        return self

    # TODO: This could probably go somewhere else.
    def preview_readme(self):
        """Open a preview of your readme in restview.
        """
        if not self.PACKAGE_FILES['readme_rst']:
            self.build_readme()
        with dists_context(self.build_dir):
            input("Press enter to view a preview of your README.rst file. When you're done, press enter again.")
            logger.info("Opening README.rst in restview. ")
            with ignore_stdout():
                shell = subprocess.Popen("restview README.rst".split(" "))
            input()
            shell.kill()

    def build_manifest(self):
        """Fills in your releases MANIFEST.in file """
        include_data_files = 'recursive-include data *' if self.is_data_files else ''
        include_docs_folder = 'include docs/*'
        rv = manifest_in.TEMPLATE.format(include_data_files=include_data_files,
                                         include_docs_folder=include_docs_folder)
        self.PACKAGE_FILES['manifest_in'] = rv
        with open(os.path.join(self.build_dir, 'MANIFEST.in'), 'w') as f:
            f.write(rv)
        return self

    def build_setup(self):
        """Build out the setup.py file for the release."""
        if self.is_script:
            console_scripts = setup_py.CONSOLE_SCRIPTS.format(self.name, self.name)
        else:
            console_scripts = ''

        if self.is_single_file:
            py_modules = "py_modules=['%s']," % self.name
            packages = ''
        else:
            raise NotImplementedError('only single files supported')
            # py_modules = ''
            # packages = "packages=find_packages(exclude=['contrib', 'docs', 'tests']),"

        install_requires = "install_requires=%s," % repr(self.requirements)

        rv = setup_py.TEMPLATE.format(
            url=self.url,
            name=self.name,
            version=self.version,
            license=self.license,
            description=self.description,
            author=self.author,
            author_email=self.author_email,
            console_scripts=console_scripts,
            install_requires=install_requires,
            packages=packages,
            py_modules=py_modules,
            find_packages=self.find_packages,
            long_description=self.long_description,
        )
        self.PACKAGE_FILES['setup_py'] = rv
        with open(os.path.join(self.build_dir, 'setup.py'), 'w') as f:
            f.write(rv)
        return self

    def build_license(self):
        """Create you license file. Only supports MIT for now but only because I'm lazy,
        not because I'm pushy, let me know what you need and I'll add it asap"""
        rv = MIT.TEMPLATE.format(
            author=self.author,
            year=str(datetime.datetime.now().year)
        )
        self.PACKAGE_FILES['license_md'] = rv
        with open(os.path.join(self.build_dir, "LICENSE.md"), 'w') as f:
            f.writelines(rv)
        return self

    def build_docs(self):
        """Builds a pydoc API documention of your script in html"""
        docs_folder = os.path.join(self.build_dir, 'docs')
        if not os.path.exists(docs_folder):
            os.mkdir(docs_folder)
        mod = self.package_info['module']
        title = "{}: %s".format(self.name)
        html = pydoc.render_doc(mod, title, pydoc.html)
        self.PACKAGE_FILES['license_md'] = html
        with open(os.path.join(self.build_dir, 'docs', 'index.html'), 'w') as f:
            f.write(html)
        return self

    def build_requirements(self):
        """Writes the requirements.txt file"""
        with open(os.path.join(self.build_dir, "requirements.txt"), 'w') as f:
            f.writelines(self.requirements)
        return self

    def copy_files(self):
        """Copies our package files into the new output folder.
        """
        if not self.is_single_file:
            # TODO: No reason why we couldn't glob all the .py files and send em all over too.. Panic for now.
            raise NotImplementedError('only single files supported')

        copy_to_dir(self.target_file, self.build_dir)
        return self

    def build_all(self):
        """ Help method to just giver and build the whole thing"""
        self.build_docs()
        self.build_readme()
        self.build_license()
        self.build_manifest()
        self.build_requirements()
        self.build_setup()

    def create_package(self):
        """Copies the project file and data folders to the build destination"""
        if self.is_data_files:
            data_folder = os.path.join(self.package_dir, 'data')
            dest = os.path.join(self.build_dir, 'data')
            copy_dir(data_folder, dest)
        self.copy_files()


@contextlib.contextmanager
def dists_context(target_dir):
    """Context manager that runs commands in the provided target_dir
     and swicthes back to the previous dir automatically
     """
    current_dir = os.getcwd()
    os.chdir(os.path.abspath(target_dir))
    try:
        yield
    finally:
        os.chdir(current_dir)


class Builder:
    """Builds pypackage project and uploads to PyPi.

    Errors during build will set the self.errors switch to True
    indicating there was an error.
    """

    default_commands = {
        "builds": [
            "python setup.py sdist",
            "python setup.py bdist_wheel --universal",
        ]
    }
    dists_folder = None
    errors = None

    def __init__(self, package: PyPackage, test=False):
        self.package = package
        self.dists_folder = package.build_dir
        self.file_name = package.target_file + ".py"

        # Set True to upload to PyPi test server.
        self.use_test_server = test

    def build(self, show_output=False):
        """Builds out project distros, console output can be suppressed
         by setting show_output to True.
         """
        with dists_context(self.dists_folder):
            for cmd in self.commands:
                # TODO: This needs to be better. Not enough info on the build.
                logger.info("Executing command - %s", str(cmd))
                execute_shell_command(cmd, suppress=show_output)
                logger.info("Done.")

    def upload(self, show_output=False):
        """Uploads package to PyPi using twine.
        The advantage to using Twine is your package is uploaded
        over HTTPS which prevents your private info from appearing
        in the request header.
        """
        with dists_context(self.dists_folder):
            # TODO: This doesn't need to be twine anymore. ALTHOUGH, make sure the default pip or setuptools uses https _without_ needing to be upgraded first. Because if not, that makes twine the most secure way.
            if self.use_test_server:
                logger.info("To upload to the test server you need to first register your package.\n"
                            "Please enter you PyPi password when prompted.")
                time.sleep(INTERVAL)
                register_test_site = "python setup.py register -r https://testpypi.python.org/pypi",  # FOR PYPI TEST SITE
                execute_shell_command(register_test_site, suppress=show_output)
                logger.info("Done")

                logger.info("Uploading Project to the Pypi TESTING server..")
                response = execute_shell_command("twine upload dist/* -r testpypi", suppress=show_output)
                logger.info("Project has been uploaded to the Pypi TESTING server!")
                logger.info("You can now install with the command\n"
                            "$ pip install -i https://testpypi.python.org/pypi %s", self.package.name)
            else:
                logger.info("Uploading Project to the Pypi server..")
                response = execute_shell_command("twine upload dist/*", suppress=show_output)
                logger.info("Project has been uploaded to the Pypi server!")
                logger.info("You can now install with the command\n"
                            "$ pip install %s", self.package.name)

            # TODO: This needs to be better..
            if response == 127:
                logger.info("Twine not installed.. Cancelled.")
                self.errors = True

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


def main():
    """ Main entry point for now until I get the click interface working.
     Please use the logger and not print in this file, screen prints will
     all be done from the cli and I don't want the logger to inerfere if
     I can help it."""
    args = sys.argv

    # --------------------------------------------- Package creation

    package = PyPackage(args[1])
    slow_log(print("Package loaded, making files."))

    package.build_docs()
    slow_log(print("index.html built"))

    package.build_readme()
    slow_log(print("readme.rst built"))

    package.build_license()
    slow_log(print("LICENSE.md built"))

    package.build_manifest()
    slow_log(print("manifest.in built"))

    package.build_requirements()
    slow_log(print("requirements.txt built"))

    package.build_setup()
    slow_log(print("setup.py file built"))

    # Browser preview. ------------------------------ Browser preview
    slow_log(print("Previewing in browser."))
    package.preview_readme()
    # ------------------------------------------------

    # Create the package for the Builder.F
    package.create_package()
    slow_log(print("Package created"))

    # ------------------------------------------------- Build commands

    input("Press enter to continue on to the build stage. Or press ctrl-c to exit.")

    # Test means upload to test site ore not.
    builder = Builder(package, test=True)
    slow_log(print("Builder loaded"))

    # show_output turns on console output
    # for the various setup.py build commands
    # and any pypi upload commands.
    builder.build(show_output=True)
    slow_log(print("Package built"))

    if builder.use_test_server:
        slow_log(print("PyPi server is set to TESTING server."))
    else:
        slow_log(print("PyPi server is set to NORMAL server."))
    input("Press enter to continue on to the upload step. Or press ctrl-c to exit.")
    # There is an input sentinal that will allow you to
    # Exit before any attempt to upload is made.
    builder.upload()
    slow_log(print("Package up-loaded successfully."))
    state = "TEST server" if builder.use_test_server else "server"
    print("Thanks for using PyRelease, your completed files can be"
          "found in the %s directory. And on the PyPi %s" % (package.build_dir, state))


if __name__ == '__main__':
    main()

