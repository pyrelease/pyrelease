#! /usr/bin/env python
# encoding: utf-8
"""PyPackage is for python packages with only code and data.

*Please do not use this.*
*This is just an experiment so far.*

Often you have only a couple of python files, and you want to share them.


* Gather facts.
* Ask about required details.
    * Tell user to set up things (eg .pypirc, .gitconfig)
* Write out template.
* build build dist
* push

"""
from __future__ import print_function
import io
import os
import sys
import re
import ast
import tempfile
import imp
import yaml
import subprocess
from shutil import copy as copy_to_dir

from .templates.manifest_in import TEMPLATE
from .templates.setup_py import TEMPLATE, CONSOLE_SCRIPTS
from .userdata import PyPiRc, GitConfig, HgRc
from .extern.doc2md import doc2md, mod2md
from .shelltools import execute_shell_command

PY2 = sys.version_info[0] == 2

if not PY2:
    raw_input = input

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Reads in file from *parts.
    """
    try:
        return io.open(os.path.join(*parts), 'r', encoding='utf-8').read()
    except IOError:
        return ''


def version_from_file(fname):
    """ TODO: Make a test for this to compare against regex from trabBuild
    """
    version_file = read(fname)
    version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                              version_file, re.MULTILINE)
    if version_match:
        return version_match.group(1)


def version_from_git():
    """Gets the current version from git tags.
    """
    try:
        versions = subprocess.check_output(
            'git tag --sort version:refname'.split())
    except subprocess.CalledProcessError:
        return
    lines = versions.splitlines()
    if lines:
        return lines[-1].decode('utf-8')


def package_py(what_to_package):
    """Is there a .py file for this repo or a __init__.py ?

    package_py('.')
    package_py('mypackage.py')
    package_py('/Users/bla/packagefolder/')

    This detects single file packages, and packages with __init__.py in them.

    """
    if what_to_package.endswith('.py'):
        return what_to_package

    if os.path.isdir(what_to_package) or what_to_package == '.':
        # lets see if there is a __init__.py in there.
        apath = os.path.join(what_to_package, '__init__.py')
        if os.path.exists(apath):
            return apath

        # maybe there is a file with the same name as the folder?
        folder_name = os.path.split(os.path.abspath(what_to_package))[-1]
        apath = os.path.join(what_to_package, folder_name + '.py')
        if os.path.exists(apath):
            return apath

        # Check for posix style name match, ex: ``file-name`` == ``file_name``
        posix_style_title = folder_name.replace('_', '-')
        apath = os.path.join(what_to_package, posix_style_title + '.py')
        if os.path.exists(apath):
            return apath

        apath = os.path.join(what_to_package, folder_name, '__init__.py')
        if os.path.exists(apath):
            return apath


def dependencies_ast(package):
    """Try to find 3rd party dependencies in the past in .py file.

    Returns a list of package names.
    """
    module = ast.parse(open(package).read())
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

    return deps


class BuildDocs(object):
    """For getting the description and long_description out of the module docstring
    """

    def __init__(self, ctx, user_info):
        target_dir = ctx.home
        mod_abs_path = package_py(target_dir)
        mod_name = os.path.relpath(mod_abs_path)
        rel_dir = os.path.relpath(target_dir)
        self.module_docs = read(mod_name)
        name = mod_name.replace("./", "").replace(".py", "")
        __path = list(sys.path)
        sys.path.insert(0, rel_dir)
        try:
            mod = __import__(name)
        finally:
            sys.path[:] = __path  # restore
        self.module_docs = mod2md(mod, name, "API")
        """Set description... This is a hack.."""
        # requires ``__all__`` be set
        entry = mod.__dict__[mod.__all__[0]]
        self.description = ""
        if entry.__doc__:
            md, sec = doc2md(entry.__doc__, name, more_info=True, toc=False)

            self.description = md[2]
        self.long_description = self.module_docs


class GatherInfo(object):
    def __init__(self, ctx):
        """ Gathers user info from config files. Works with
         `.pypirc`, `.gitconfig`, `.hgrc`, and `.gitconfig`
         files.
         """
        self.target_package = ctx.home
        self._version = None
        self.pypirc = PyPiRc()
        self.gitconfig = GitConfig()
        self.hgrc = HgRc()
        # TODO: Get this outta here..
        self.module_docs = BuildDocs(ctx)

    def set_package_version(self, new_version):
        self._version = new_version

    @property
    def author(self):
        if self.pypirc.author is not None:
            return self.pypirc.author
        if self.gitconfig.author is not None:
            return self.gitconfig.author

    @property
    def author_email(self):
        if self.pypirc.author_email is not None:
            return self.pypirc.author_email
        if self.gitconfig.author_email is not None:
            return self.gitconfig.author_email

    @property
    def name(self):
        """ We can get this by looking at what is there.

        Is there a single python file? 'leftpad.py' -> 'leftpad'
        Is there a single folder of python files? 'leftpad/' -> 'leftpad'
        If it is '.' then we use the folder name -> 'leftpad'
        """
        if self.target_package.endswith('.py'):
            return self.target_package.rstrip('.py')

        if os.path.isdir(self.target_package):
            return os.path.split(os.path.abspath(self.target_package))[-1]

    @property
    def description(self):
        return self.module_docs.description

    @property
    def long_description(self):
        return self.module_docs.long_description

    @property
    def version(self):
        if self._version is not None:
            return self._version
        afile = package_py(self.target_package)
        ver = version_from_file(afile)
        if ver is None:
            ver = version_from_git()
        if ver is None:
            ver = '0.0.0'
        return ver

    @property
    def url(self):
        # from .git/config
        if os.path.isdir(self.target_package):
            package_name = os.path.split(
                os.path.abspath(self.target_package))[-1]
            return 'https://pypi.python.org/pypi/%s' % package_name

    @property
    def install_requires(self):
        if self.target_package.endswith('.py'):
            return dependencies_ast(self.target_package)
        else:
            return []

    def is_data_files(self):
        return False

    @property
    def is_script(self):
        """Is the package a script? Does it have a module.main() ?
        """
        return 'def main' in read(package_py(self.target_package))

    @property
    def is_single_file(self):
        return package_py(self.target_package)

    @property
    def find_packages(self):
        return "" if self.is_single_file else ", find_packages"

    def __str__(self):
        """
        """
        output = """
name="{name}"
description = {description}
long_description = {long_description}
author_email="{author_email}"
author="{author}"
version="{version}"
url="{url}"
is_script={is_script}
find_packages={find_packages}
"""
        return output.format(
            name=self.name,
            description=repr(self.description),
            long_description=repr(self.long_description),
            author_email=self.author_email,
            author=self.author,
            version=self.version,
            url=self.url,
            is_script=self.is_script,
            find_packages=self.find_packages)


class FillFiles:
    """ This fills setup files in with what they need.
    """

    def __init__(self, package_info, target_dir=None, context=None):
        self._ctx = context
        self.package_info = package_info
        if target_dir is not None:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            self.tmpdir = target_dir
        else:
            self.tmpdir = tempfile.mkdtemp()
        # repo = 'https://github.com/pypa/sampleproject/'
        # subprocess.check_output = 'git clone %s %s' % (repo, self.tmpdir)

    def fill_files(self):
        setup_py_data = self.setup_py()
        manifest_in_data = self.manifest_in()
        requirements_file = self.requirements_txt()
        md_readme = self.readme_md()

        with open(os.path.join(self.tmpdir, 'setup.py'), 'w') as afile:
            afile.write(setup_py_data)
        with open(os.path.join(self.tmpdir, 'MANIFEST.in'), 'w') as afile:
            afile.write(manifest_in_data)
        with open(os.path.join(self.tmpdir, "requirements.txt"), 'w') as f:
            f.write(requirements_file)
        with open(os.path.join(self.tmpdir, "README.md"), 'w') as f:
            f.write(md_readme)
        self.copy_files()

    def readme_md(self):
        return self.package_info.long_description

    def requirements_txt(self):
        return "".join(self.package_info.install_requires)

    def copy_files(self):
        """Copies our package files into the new output folder.
        """
        if not self.package_info.is_single_file:
            raise NotImplementedError('only single files supported')

        pyfname = package_py(self.package_info.target_package)
        copy_to_dir(pyfname, self.tmpdir)

    def manifest_in(self):
        """Fill in a MANIFEST.in
        """
        include_data_files = 'recursive-include data *' if self.package_info.is_data_files else ''
        return MANIFEST_IN.format(include_data_files=include_data_files)

    def setup_py(self):
        """Fill in a setup.py string.
        """

        if self.package_info.is_script:
            console_scripts = CONSOLE_SCRIPTS.format(self.package_info.name,
                                                     self.package_info.name)
        else:
            console_scripts = ''

        if self.package_info.is_single_file:
            py_modules = "py_modules=['%s']," % self.package_info.name
            packages = ''
        else:
            raise NotImplementedError('only single files supported')
            # py_modules = ''
            # packages = "packages=find_packages(exclude=['contrib', 'docs', 'tests']),"

        install_requires = "install_requires=%s," % repr(
            self.package_info.install_requires)

        return SETUP_PY.format(
            name=self.package_info.name,
            description=repr(self.package_info.description),
            # long_description=repr(self.package_info.long_description),
            author_email=self.package_info.author_email,
            author=self.package_info.author,
            version=self.package_info.version,
            url=self.package_info.url,
            console_scripts=console_scripts,
            install_requires=install_requires,
            license='MIT',
            packages=packages,
            py_modules=py_modules,
            find_packages=self.package_info.find_packages)


class Builder:
    """Builds pypackage project and uploads to PyPi.

    Commands for build are intended to be stored in a config file
    to allow for easy customization. Config format is `yaml`. If
    no config is found the default commands should be used.
    Errors during build will set the self.errors switch to True
    indicating there was an error.
    """

    command_file = os.path.join(SCRIPT_PATH, "pybuilder.yml")
    default_commands = {
        "builds": [
            "python setup.py sdist",
            "python setup.py bdist_wheel --universal",
        ]
    }
    dists_folder = None
    errors = None

    def __init__(self, test=False, output_to=None, ctx=None):
        self._ctx = ctx
        self.log = ctx.log
        self.vlog = ctx.vlog
        self.config = self._read_command_config()
        self.commands = self.config["builds"]
        if output_to is not None:
            output_to = os.path.abspath(output_to)
            self.commands = [
                " ".join([cmd, "--dist-dir", output_to])
                for cmd in self.commands
            ]
        self.dists_folder = output_to

        # Set True to upload to PyPi test server.
        self.use_test_server = test

    def build(self):
        """Build out project distros.

        Build commands are pulled from config file to
        allow for easy customization.
        """
        for cmd in self.commands:
            execute_shell_command(cmd)

        # If using test server then project needs to register first.
        # Not necessary for normal PyPi server
        # x = raw_input("Exit? [y] n  $ ") or None
        # if x is None:
        #     sys.exit()
        if self.use_test_server:
            register_test_site = "python setup.py register -r https://testpypi.python.org/pypi",  # FOR PYPI TEST SITE
            subprocess.call(register_test_site, shell=True)
        self.log("Done Building")

    def upload(self):
        """Uploads package to PyPi using twine.
        The advantage to using Twine is your package is uploaded
        over HTTPS which prevents your private info from appearing
        in the request header.
        """
        if self.use_test_server:
            response = execute_shell_command(
                "twine upload dist/* -r testpypi", suppress=False)
        else:
            response = execute_shell_command(
                "twine upload dist/*", suppress=False)

        # TODO: This needs to be better..
        if response == 127:
            print("Twine not installed.. Cancelled.")
            self.errors = True

    def _read_command_config(self):
        """Get yaml config file with build commands.

        If no config file is found the defaults are used
        """
        if not os.path.isfile(self.command_file):
            return self.default_commands
        with open(self.command_file, 'r') as f:
            return yaml.load(f.read())

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


def build_and_upload_to_pypi(path, test=False, output_dir=None, context=None):
    """Helper function for `UploadPyPi` class.

    TODO: Need better twine update status.

    """

    builder = Builder(test, output_dir, context)
    os.chdir(path)
    builder.build()
    if not builder.success:
        context.log("Build completed with errors.")
    builder.upload()
    if not builder.success:
        context.log("Deployment completed with errors.")


def fill_files(package_info, target=None, context=None):
    """Helper function for ``FillFiles`` class.

    Fills project files with info gathered from ``GatherInfo``
    class and stores them to ``target`` directory. If ``target``
    is none them a temporary directory is created automatically.
    Returns the location of the created files, for example if a
    temp_dir is used then that is what's returned.

    :param package_info: ``class.GatherInfo`` instance
    :param target: directory to store project files
    :param context: ``class.Context`` instace
    :return: returns path to ``temp_files``
    """
    filler = FillFiles(package_info, target, context)
    filler.fill_files()
    return filler.tmpdir
