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

    def __init__(self):
        self.question = 0
        self.options = {}
        self.term_width = min(click.get_terminal_size()[0], 78)
        self.e = click.secho
        self.w = partial(click.wrap_text, width=self.term_width)

    def abort(self, message):
        click.echo('Error: %s' % message, err=True)
        raise click.Abort()

    def prompt(self, text, default=None, info=None):
        self.question += 1
        self.e('')
        self.e('Step %d:' % self.question, fg='yellow')
        if info is not None:
            self.e(click.wrap_text(info, self.term_width - 2, '| ', '| '))
        text = '> ' + click.style(text, fg='green')

        if default is True or default is False:
            return click.confirm(text, default=default)
        else:
            return click.prompt(text, default=default, show_default=True)

    def title(self, title):
        self.e(title, fg='cyan')
        self.e('=' * len(title), fg='cyan')
        self.e('')

    def text(self, text):
        self.e(self.w(text))

    def confirm(self, prompt):
        self.e('')
        click.confirm(prompt, default=True, abort=True, prompt_suffix=' ')


@click.command()
@click.option('-t', '-p', '-P', '--project', type=click.Path
              (exists=True, file_okay=True, resolve_path=True),
              help='The path to the package or file you wish to release.')
@click.option('-D', '--dists-path', type=click.Path(), default=None,
              help='Destination for your completed builds.')
@click.option('-O', '--output-path', type=click.Path(resolve_path = True),
              help='Location to put your finished package files.')
@click.option('-T', '--target-test-pypi', is_flag=True,
              help='Deploy to PyPi test server instead.')
@click.option('-v', '--verbose', is_flag=True,
              help='Enables verbose mode for debugging.')
@click.argument('project')
def release(project, output_path, dists_path, target_test_pypi, verbose):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage, Builder

    package = PyPackage(project)

    g = Generator()

    g.text(' ')
    g.title("PyRelease wizard")

    g.text(
        "This wizard will help guide you through setting up %s "
        "for release on pypi. Don't worry, you won't have to do much!" % package.name
    )
    if not os.path.exists(os.path.expanduser('~/.pypirc')):
        v = g.prompt("No .pypirc file found. You must create one if you want to upload to Pypi. "
                     "Please refer to https://docs.python.org/2/distutils/packageindex.html#pypirc "
                     "for more info. Continue?", default=True)
        if not v:
            g.text("Exiting.")
            exit()

    if package.version is None:
        v = g.prompt("You don't have a version specified in your main file. Either "
                     "create a version line in your file or enter one here:", default="0.1.0")
        package.version = v
    else:
        proceed = g.prompt("%s is set to version %s in %s, "
                           "if you need to change it please exit and do so now. "
                           "Then when you are ready you can run pyrelease again. "
                           "Continue?" % (package.name, package.version, package.target_file), default=True)
        if not proceed:
            g.text("Exiting")
            exit()
    g.text("Proceeding!")


main = release

if __name__ == '__main__':
    main()
