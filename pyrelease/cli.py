import os
import logging

from functools import partial
import click

# ######## LOGGING #########
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)

# File handler
# handler = logging.FileHandler(os.path.join(os.getcwd(), 'build.log'), 'w')
# handler.setLevel(logging.INFO)
# formatter = logging.Formatter(
#     '%(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

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
@click.option('-O', '--output-path', type=click.Path(resolve_path = True),
              help='Location to put your finished package files.')
@click.option('-T', '--target-test-pypi', is_flag=True,
              help='Deploy to PyPi test server instead.')
@click.argument('project', type=click.Path(exists=True, file_okay=True, resolve_path=True))
def release(project, output_path, target_test_pypi):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage, Builder

    package = PyPackage(project)

    g = Generator()
    g.text(' ')
    g.title("PyRelease wizard")
    g.text("This wizard will help guide you through setting up %s "
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
    package.version = g.prompt("Version", package.version or "0.1.0",
                               "%s is set to version %s. Enter a new version or press enter "
                               "to continue." % (package.name, package.version))

    # Go through config files
    g.text(' ')
    g.text("PyRelease will now attempt to locate any config files to "
           "use automatically.")

    for key, klass in package.user_info.items():
        choices = {
            "pypirc":
                "~/.pypirc - Used for uploading to PyPi and it's test server. "
                "*Needed for PyPi.",

            "gitconfig":
                "~/.gitconfig - Used for interacting with git. "
                "*Safe to leave as None.",

            "hgrc":
                "~/.hgrc - Currently not used for anything. * Safe to leave as None."
        }

        g.text("\n * Detected a %s file." % key)
        name = g.prompt("Username: ", klass.author or "None", choices[key], step=False)
        email = g.prompt("Email ", klass.author_email or "None", step=False)
        package.user_info[key].author = name
        package.user_info[key].author_email = email

    # Verify requirements
    def list_dependencies():
        for dep in package.requirements:
            g.text(" ")
            g.red_text(dep)
    g.text(" ")
    g.text("PyRelease has analyzed %s and has found these dependancies.")

    list_dependencies()
    g.text(" ")
    proceed = g.prompt("Confirm", True,
                       "Yes to continue or no to add dependencies to the list.")
    g.text(" ")
    if not proceed:
        while 1:
            dependencies = g.prompt("Please enter any dependencies you want to add to the "
                                    "list. Separate each entry with an empty space.", "")
            if dependencies != "":
                package.requirements.extend(dependencies.split(" "))
            list_dependencies()
            g.text(" ")
            confirm = g.prompt("Is this correct?" % package.requirements, True)
            if confirm:
                break

    # Verify License
    g.text(" ")
    _license = package.package_info['license']
    if _license is None:
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
    g.text("Using license: %s" % package.license)

    g.text(" ")



    g.text("Goodbye!")


main = release

if __name__ == '__main__':
    main()
