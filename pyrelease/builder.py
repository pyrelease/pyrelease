# coding=utf-8
from __future__ import print_function, absolute_import
import os
import datetime
import subprocess
import logging
from shutil import copy as copy_to_dir
from shutil import copytree as copy_dir

from .templates import readme_rst, manifest_in, setup_py
from .shelltools import execute_shell_command, ignore_stdout, dir_context
from .licenses import MIT, UNLICENSE, APACHE_2, GPL_3, BSD_2, BSD_3, LGPL_2, LGPL_3
from .compat import devnull

# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class Builder(object):
    """The builder takes an instance of `pypackage.PyPackage` and
    uses it as the building block for creating a pyrelease.

    `build_dir` is the location your finished release will be found.
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
                os.getcwd(), (self.package.name + str(self.package.version)))
        self.build_dir = os.path.abspath(build_dir)


    def build_target_dir(self):
        # if os.path.exists(self.build_dir):
        #     if "__" in self.build_dir[:-5]:
        #         last = int(self.build_dir[-1])
        #         last += 1
        #         logger.debug("%s time through build_target_dir. Build dir - (%s)", (str(last), self.build_dir))
        #         self.build_dir += "__%s" % last
        #     else:
        #         logger.debug("First time through build_target_dir.")
        #         self.build_dir += "__1"
        try:
            logger.info("Creating dir - (%s)", self.build_dir)
            os.mkdir(self.build_dir)
        except OSError:
            return False
        else:
            logger.info("Crerated dir - (%s) - successfully", self.build_dir)
            return self.build_dir

    def build_package(self, count=1):
        """Copies the project file and data folders to the build destination"""
        if self.package.is_data_files:
            logger.info("Found data files.")
            if count == 10:
                return "You should clean up some of those directories.."
            data_folder = os.path.join(self.package.package_dir, 'data')
            dest = os.path.join(self.build_dir, 'data')
            try:
                copy_dir(data_folder, dest)
                logger.info("Copying: (%s) - To: (%s)", data_folder, dest)
            except Exception as e:
                logger.error("File exists error in build_package: (%s)", exc_info=True)
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
            license=self.package.license,
            license_name=self.package.license_name)
        self.package.PACKAGE_FILES['readme_rst'] = rv
        with open(os.path.join(self.build_dir, "README.rst"), 'w') as f:
            f.write(rv)
            logger.info("Readme built..")
        return rv

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
        logger.info("MANIFEST built..")

    def build_setup(self):
        """Build out the setup.py file for the release."""
        if self.package.is_script:
            console_scripts = setup_py.CONSOLE_SCRIPTS.format(
                self.package.name, self.package.name)
        else:
            console_scripts = ''

        if self.package.is_single_file:
            py_modules = "py_modules=['%s']," % self.package.name
            packages = ''
        else:
            raise NotImplementedError('only single files supported')
            # py_modules = ''
            # packages = "packages=find_packages(exclude=['contrib', 'docs', 'tests']),"

        install_requires = "install_requires=%s," % repr(
            self.package.requirements)

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
        logger.info("setup.py built..")

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
        logger.info("License built..")

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
        with dir_context(self.build_dir):
            for cmd in self.commands:
                # TODO: This needs to be better. Not enough info on the build.
                logger.info("Executing command - %s", str(cmd))
                execute_shell_command(cmd, suppress=suppress)
                logger.info("Done.")

    def copy_files(self):
        """Copies our package files into the new output folder.
        """
        if not self.package.is_single_file:
            logger.error("Package is more than one file.")
            # TODO: No reason why we couldn't glob all the .py files and send em all over too.. Panic for now.
            raise NotImplementedError('only single files supported')
        logger.info("%s file is being copied to %s", self.package.target_file, self.build_dir)
        copy_to_dir(self.package.target_file, self.build_dir)

    def make_all(self):
        """ Help method to just giver and build the whole thing"""
        # self.build_docs() # Broken
        logger.info("Running make_all")
        self.build_target_dir()
        self.build_readme()
        self.build_license()
        self.build_manifest()
        self.build_requirements()
        self.build_setup()
        self.build_package()
        # TODO: Keep track of progress and report errors..
        logger.info("Finished running make_all.")
        return self.errors

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

    def register_pypi_test_package(self, suppress=False):
        """Registers your package with the PyPi test site. This step doesn't
         seem to be necessary for the regular PyPi site though..
         """
        # TODO: Needs research.. See docstring.
        suppress = suppress or self.verbose
        with dir_context(self.build_dir):
            logger.info("Uploading Project to the Pypi TESTING server..")
            cmd = "python setup.py register -r %s" % self.pypi_test_url
            response = execute_shell_command(cmd, suppress=suppress)
            self.parse_response(response)
        return response

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
                "for more info.")
            logger.warning(msg)
            self.errors.append(msg)
            return
        logger.info("Uploading Project to the Pypi server..")
        with dir_context(self.build_dir):
            response = execute_shell_command(
                "twine upload dist/*", suppress=suppress)
            logger.info("Project has been uploaded to the Pypi server!")
            logger.debug("Result: %s", repr(response))
            self.parse_response(response)
        return response

    def upload_to_pypi_test_site(self, suppress=False):
        """Uploads your package to the PyPi repository allowing others
        to download easily with pip"""
        suppress = suppress or self.verbose
        with dir_context(self.build_dir):
            logger.info("Uploading Project to the Pypi TESTING server..")
            response = execute_shell_command(
                "twine upload dist/* -r testpypi", suppress=suppress)
            logger.info(
                "Project has been uploaded to the Pypi TESTING server!")
            logger.debug("Result: %s", repr(response))
            # TODO: This needs to be better..
            self.parse_response(response)
        return response

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
