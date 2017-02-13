import os
import sys
import click


class Context(object):

    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            for i in args:
                msg = msg + " " + i
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)


pass_context = click.make_pass_decorator(Context, ensure=True)


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
@pass_context
def release(ctx, verbose, project, version, output_path,
            dists_path, target_test_pypi):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import GatherInfo, fill_files, build_and_upload_to_pypi

    ctx.verbose = verbose
    if project is not None:
        ctx.home = project
    package_info = GatherInfo(ctx)
    if version is not None:
        package_info.set_package_version(version)
    package = fill_files(package_info, target=output_path, context=ctx)
    build_and_upload_to_pypi(package, test=target_test_pypi, output_dir=dists_path, context=ctx)

main = release
