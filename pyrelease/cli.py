import os
import logging

import click

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


@click.command()
@click.option('-P', '--project', type=click.Path
              (exists=True, file_okay=True, resolve_path=True),
              help='The path to the package or file you wish to release.')
@click.option('-V', '--version', default=None,
              help='Version you will be updating to. Defaults to the next lowest factor '
                   'of the version scheme. ie: "0.1.0" becomes "0.1.1", "2.3.4" becomes '
                   '"2.3.5"')
@click.option('-D', '--dists-path', type=click.Path(), default=None,
              help='Destination for your completed builds.')
@click.option('-O', '--output-path', type=click.Path(resolve_path = True),
              help='Location to put your finished package files.')
@click.option('-T', '--target-test-pypi', is_flag=True,
              help='Deploy to PyPi test server instead.')
@click.option('-v', '--verbose', is_flag=True,
              help='Enables verbose mode for debugging.')
def release(project, version, output_path,
            dists_path, target_test_pypi, verbose):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage, Builder
    package = PyPackage(project)
    if package.version is None:
        click.echo(f"")
    else:
        click.echo(f"You are on version {package.version}. If you have this set in"
               f"")



main = release
