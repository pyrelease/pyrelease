import os
import logging

from functools import partial
import click

# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)

# File handler
handler = logging.FileHandler(os.path.join(os.getcwd(), 'error.log'), 'w')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(levelname)s] <%(module)s> - %(message)s,  @ (%(asctime)s)')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Stream handler
# s_handler = logging.StreamHandler()
# s_handler.setLevel(logging.WARNING)
# s_formatter = logging.Formatter('%(message)s')
# s_handler.setFormatter(s_formatter)
# logger.addHandler(s_handler)


class Generator(object):
    """This class is taken directly from the `quickstart.py` for `Lektor`
     the static site generator by Armin Ronacher Licensed under the BSD-3
     clause.
     """
    def __init__(self):
        self.question = 0
        self.options = {}
        self.term_width = min(click.get_terminal_size()[0], 78)
        self.e = click.secho
        self.w = partial(click.wrap_text, width=self.term_width)

    def abort(self, message):
        click.echo('Error: %s' % message, err=True)
        raise click.Abort()

    def prompt(self, text, default=None, info=None, step=False, allow_none=False):
        # self.e('')
        if step:
            self.question += 1
            self.e('Step %d:' % self.question, fg='yellow')
        if info is not None:
            self.e(click.wrap_text(info, self.term_width - 2, '| ', '| '))
        text = '> ' + click.style(text, fg='green')

        if allow_none is True:
            rv = click.prompt(text, default=default, show_default=True)
            return rv
        elif default is True or default is False:
            return click.confirm(text, default=default)
        else:
            return click.prompt(text, default=default, show_default=True)

    def title(self, title):
        self.e(title, fg='cyan')
        self.e('=' * len(title), fg='cyan')
        self.e('')

    def red_text(self, text):
        self.e(self.w(text), fg='red')

    def green_text(self, text):
        self.e(self.w(text), fg='green')

    def yellow_text(self, text):
        self.e(self.w(text), fg='yellow')

    def cyan_text(self, text):
        self.e(self.w(text), fg='cyan')

    def text(self, text):
        self.e(self.w(text))

    def confirm(self, prompt):
        self.e('')
        click.confirm(prompt, default=True, abort=True, prompt_suffix=' ')


def confirm_or_exit(g, proceed, on_no="Aborting"):
    if not proceed:
        g.text(on_no)
        # g.text("\n")
        exit()


@click.command()
@click.option('-G', '--giver', is_flag=True,
              help="Enable this to just giver and build the whole thing in one go.")
@click.argument('project', type=click.Path(exists=True, file_okay=True, resolve_path=True))
def release(project, giver):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage, Builder

    package = PyPackage(project)

    # ------------------------------------Giver mode
    if giver:
        package.build_all()
        builder = Builder(package)
        builder.build()
        builder.upload()
        return builder.errors
    #################################

    g = Generator()

    g.text(' ')
    g.title("PyRelease wizard")
    g.green_text("This wizard will help guide you through setting up %s "
                "for release on pypi. Don't worry, it's easy! "
                "Press ctrl-c at any time to exit to the terminal" % package.name)

    # Check for a .pypirc file. It's required to upload to pypi.
    g.text(' ')
    if not os.path.exists(os.path.expanduser('~/.pypirc')):
        proceed = g.prompt("Continue without .pypirc? -", True,
                           "No .pypirc file found. You must create one if you want to upload "
                           "to Pypi. Please refer to https://docs.python.org/2/distutils/pack"
                           "ageindex.html#pypirc for more info. You can continue without it "
                           "but you won't be able to upload to PyPi.")
        confirm_or_exit(g, proceed)
    # Make sure the version is correct.
    version = g.prompt("Version", package.version or "0.1.0",
                       "%s is set to version %s. Enter a new version or press enter "
                       "to continue." % (package.name, package.version))

    result = package.set_version(version)
    if result is None:
        g.abort("Invalid version. You must choose a version that is higher than, or equal to "
                "your current version.")

    # Go through config files
    g.text(' ')
    g.text("PyRelease will now attempt to locate any config files to "
           "use automatically.")

    for key, klass in package.user_info.items():
        choices = dict(
            pypirc="~/.pypirc - Used for uploading to PyPi and it's test server. "
                   "*Needed if you also want to upload to PyPi.",

            gitconfig="~/.gitconfig - Used for interacting with git. ",

            hgrc="~/.hgrc - Currently not used for anything. * Safe to leave as None.")

        g.red_text("\n * Detected a %s file." % key)
        name = g.prompt("Username: ", klass.author or "None", choices[key], step=False)
        email = g.prompt("Email ", klass.author_email or "None", step=False)
        package.user_info[key].author = name
        package.user_info[key].author_email = email

    g.text(" ")
    package.author = g.prompt("Author: ", package.author,
                              "Your name shows up in a few places in the release.")

    g.text(" ")
    package.author_email = g.prompt("E-mail: ", package.author_email,
                                    "Leaving an e-mail gives people who use your package a way to "
                                    "reach you with feedback and support.")

    # Verify requirements
    def list_dependencies():
        for dep in package.requirements:
            g.text(" ")
            g.red_text(dep)
    g.text(" ")
    g.text("PyRelease has analyzed %s and has found these dependancies.")

    list_dependencies()
    g.text(" ")
    proceed = g.prompt("Proceed", True,
                       "You can continue or append more dependencies to the list. You can't "
                       "however delete entries, this will be implemented soon.")
    if not proceed:
        g.text(" ")
        while 1:
            dependencies = g.prompt("Please enter any dependencies you want to append to "
                                    "the list. Separate each entry with an empty space.", "")
            if dependencies != "":
                package.requirements.extend(dependencies.split(" "))
            list_dependencies()
            g.text(" ")
            confirm = g.prompt("Is this correct?" % package.requirements, True)
            if confirm:
                break

    # Verify License
    _license = package.package_info['license']
    if _license is None:
        g.text(" ")
        proceed = g.prompt("Choose a License -", True,
                           "Having a license for your source code is always a good idea. "
                           "By default PyRelease adds an MIT license to your source, if"
                           "you haven't set the variable `__version__` in your script. "
                           "You can choose from a few others that we have. If you want a "
                           "license that's not in this list, enter None and copy a license "
                           "file into the package directory before you build and it will "
                           "be included. Or let us know and we can add the license you want. "
                           "Yes to pick a license or no to skip.")
        if proceed:
            for l_name in package.LICENSES.keys():
                g.text(" ")
                g.red_text("%s" % l_name)

            g.text(" ")
            _license = g.prompt("Choose a License", "MIT",
                                "Choose from the list, if the license you want isn't "
                                "there let us know so we can add it.! Make sure you type "
                                "the name exactly how you see it.")
        package.set_license(_license)

    g.text(" ")
    g.red_text("Using license: %s" % package.license)
    # g.text(" ")
    # build_docs = g.prompt("Make pydoc help page? ", True,
    #                       "Pyrelease can invoke pydoc to automatically create a index.html "
    #                       "file with your script api auto-documented.")

    # Set build directory
    g.text(" ")
    build_dir = g.prompt("Build directory", package.build_dir,
                         "You can specify a directory that you would like your "
                         "package to be created in. Otherwise a default temp "
                         "folder will be made automatically in the current working "
                         "directory")
    package.build_dir = os.path.abspath(build_dir)

    # --------------------------------------Build all packages.
    # TODO: Fix error reporting on this part and put some hooks between the calls
    g.text(" ")
    # g.green_text("Pyrelease is ready to build your package.")
    # g.red_text("Pyrelease is ready to build your package.")
    # g.yellow_text("Pyrelease is ready to build your package.")
    g.cyan_text("Pyrelease is ready to build your package.")
    click.pause()
    g.text(" ")
    g.cyan_text("Building README.rst")
    package.build_readme()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building LICENSE.md")
    package.build_license()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building MANIFEST.in")
    package.build_manifest()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building requirements.txt")
    package.build_requirements()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building setup.py")
    package.build_setup()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Creating package")
    package.create_package()
    g.green_text("Complete!")

    errors = package.errors
    # --------------------------------------- Package creation complete.

    if errors:
        g.text(" ")
        g.red_text("Build completed with errors..!")
        g.abort("There were errors detected during the build, please check the error.log "
                "file for more details.")
    else:
        g.text(" ")
        g.green_text("Build completed successfully!")
        # g.text(" ")
        # g.text("Have a look at your new package.")
        # # click.pause()
        # g.text(" ")
        # click.launch(os.path.abspath(package.build_dir))
        # click.pause()
    g.text(" ")

    # Preview README.rst
    preview_readme = g.prompt("Preview README.rst file? ", True,
                              "You can preview your auto-generated README.rst file now "
                              "if you'd like. This will open up your default browser to "
                              "a preview of the file. When you're ready to proceed again, "
                              "come back to the termianl and press enter, which will end "
                              "the browser session (but won't close the tab)")
    if preview_readme:
        shell_session = package.preview_readme()

        while 1:
            g.text(" ")
            click.pause()
            shell_session.kill()
            break
    URLS = dict(
        pypi="https://pypi.python.org/pypi/",
        test_pypi="https://testpypi.python.org/pypi/",
    )
    g.text(" ")
    g.green_text("Loading builder.")
    builder = Builder(package)
    g.text(" ")
    g.green_text("Builder loaded successfully.")
    g.text(" ")
    g.cyan_text("Pyrelease is ready to build your package distros.")
    g.text(" ")
    click.pause()

    # Build files
    builder.build(suppress=True)

    if builder.success:
        g.green_text("Builds finished without error.")
    # else:
    #     g.green_text("There were errors during the build, look at the debug.log for more details.")

    g.yellow_text("Have a look at your new package.")
    click.launch(os.path.abspath(package.build_dir))

    # Upload files
    g.text(" ")
    g.cyan_text("Pyrelease is ready to upload your package!")
    g.text(" ")
    click.pause()
    g.text(" ")
    builder.use_test_server = g.prompt("Use test PyPi server?", True,
                                       "It's always a good idea to check your project on the "
                                       "PyPi test site before committing to the regular site. "
                                       "Using the test site requires you to register the "
                                       "package first, but don't worry, we do that part too. "
                                       "[Y]es for test server or [n] for regular PyPi.")
    builder.upload()
    g.text(" ")
    if not builder.success:
        # TODO: Figure out any error codes..
        # g.red_text("Upload completed with errors. Did you remember to set the correct version?")
        pass
    else:
        g.red_text("Upload completed successfully!")

    g.text(" ")
    g.text("Here, have a look at your new package on PyPi.")
    if builder.use_test_server:
        click.launch(URLS['test_pypi'] + package.name)
    else:
        click.launch(URLS['pypi'] + package.name)
    click.pause()

    g.text(" ")
    g.green_text("Thanks for using PyRelease! If you have any suggestions please let us know "
                 "either on GitHUb or by e-mail.")

    g.text(" ")
    g.yellow_text("PyRelease is open-source and  MIT licensed. It was made in part by Illume "
                  "and traBpUkciP (Scott Doucet) from a desire to make basic python script "
                  "packaging easy and effective. Thanks for using PyRelease.")
    g.text(" ")
    exit()

main = release

if __name__ == '__main__':
    main()
