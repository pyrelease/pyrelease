# coding=utf-8
import os
import logging

from .generator import Generator
import click

# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)

# File handler
handler = logging.FileHandler(os.path.join(os.getcwd(), 'error.log'), 'w')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(levelname)s] <%(funcName)s> <%(module)s> - %(message)s  @ (%(asctime)s)')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Stream handler
# s_handler = logging.StreamHandler()
# s_handler.setLevel(logging.WARNING)
# s_formatter = logging.Formatter('%(message)s')
# s_handler.setFormatter(s_formatter)
# logger.addHandler(s_handler)


def view_on_pypi(g, builder, package, urls):
    g.text(" ")
    g.text("Here, have a look at your new package on PyPi.")
    g.text(" ")
    if builder.use_test_server:
        click.launch(urls['test_pypi'] + package.name)
    else:
        click.launch(urls['pypi'] + package.name)
    g.text(" ")
    click.pause()


def register_package(g, builder):
    """Giver runs and wizard runs both use this prompt."""
    test_pypi = builder.use_test_server
    g.text(" ")
    proceed = g.prompt(
        "Register package? ", True,
        "To upload to the test server you must have first registered the "
        "package with the test site. We can do that right now, first make "
        "sure your .pypirc file is set-up like on the readme here "
        "https://github.com/pyrelease/PyRelease then go ahead and continue."
        "(If you have already registered this package to the test site, you "
        "can skip this part)")
    if proceed:
        g.green_text("Enter your PyPi %s password into Twine to "
                     "register your package" % ("", "TEST server")[test_pypi])
        builder.register_pypi_test_package()
        g.text(" ")
        g.green_text("Registration complete.")


pass_context = click.make_pass_decorator(Generator, ensure=True)


@click.command()
@click.option('-G', '--giver', is_flag=True,
              help="Enable this to just giver and build the whole thing in one go.")
@click.option('-T', '--test-pypi', is_flag=True,
              help="Upload to the PyPi test site.")
@click.option('-V', '--verbose', is_flag=True,
              help="Enable to view Twine output.")
@click.option('-T', '-t', '--target', default=None,
              help="This is folder your package will be saved to.",
              type=click.Path(exists=False, file_okay=False,
                              writable=True, resolve_path=True, allow_dash=True))
@click.argument('project', default=".",
                type=click.Path(exists=True, file_okay=True, resolve_path=True))
@pass_context
def release(g, project, giver, test_pypi, verbose, target):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage
    from .builder import Builder

    package = PyPackage.load_package(project, verbose=verbose)

    if package is None:
        g.abort("Release failed, see the error log for more details.")

    g.cls()
    # ------------------------------------Giver mode
    # TODO: Move me into a click command group
    if giver:
        import random
        builder = Builder(package, build_dir=target)
        builder.use_test_server = test_pypi

        g.print_header()
        g.red_text("   Giver Mode %s" % ("", "TEST SERVER")[test_pypi])
        g.text(" ")

        if not os.path.exists(builder.build_dir):
            builder.build_target_dir()

        message = [
            "Preparing data",
            "Reticulating splines",
            "Collecting data",
            "Prepping release",
        ]
        msg = random.choice(message)
        with click.progressbar(length=7, label=msg) as bar:
            bar.update(1)
            builder.build_readme()
            bar.update(1)
            builder.build_license()
            bar.update(1)
            builder.build_manifest()
            bar.update(1)
            builder.build_requirements()
            bar.update(1)
            builder.build_setup()
            bar.update(1)
            builder.build_package()
            bar.update(1)
            g.text(" ")
            g.text(" ")
            g.green_text("Done.")
            g.text(" ")

        click.pause(info="Press any key to start the build.")
        builder.build_distros(suppress=False)
        g.green_text("Build finished. Upload to PyPi? [Using test server = %s]"
                     % builder.use_test_server)

        if builder.use_test_server:
            register_package(g, builder)

        g.text(" ")
        g.cyan_text("Starting twine.")
        g.text(" ")
        g.green_text("Enter your PyPi %s password to begin the upload." %
                     ("", "TEST SERVER")[test_pypi])
        if builder.use_test_server:
            builder.upload_to_pypi_test_site()
        else:
            builder.upload_to_pypi()
        g.text(" ")
        g.green_text("Upload complete.")
        g.text(" ")
        g.cyan_text("Check out your release on PyPi")
        g.text(" ")
        name = package.name
        url = "%s/%s" % (
            (builder.pypi_url, builder.pypi_test_url)[test_pypi], name)
        g.yellow_text(url)
        g.text(" ")
        g.print_footer()
        exit()
    # ------------------------------------End Giver mode
    #################################

    g.text(' ')
    g.title("PyRelease wizard")
    g.green_text("This wizard will help guide you through setting up %s "
                 "for release on pypi. Don't worry, it's easy! "
                 "Press ctrl-c at any time to exit to the terminal" %
                 package.name)

    # Check for a .pypirc file. It's required to upload to pypi.
    g.text(' ')
    if not os.path.exists(os.path.expanduser('~/.pypirc')):
        proceed = g.prompt(
            "Continue without .pypirc? -", True,
            "No .pypirc file found. You must create one if you want to upload "
            "to Pypi. Please refer to https://docs.python.org/2/distutils/pack"
            "ageindex.html#pypirc for more info. You can continue without it "
            "but you won't be able to upload to PyPi.")
        if not proceed:
            g.print_footer()
            click.Abort()

    # Make sure the version is correct.
    version = g.prompt(
        "Version", package.version or "0.1.0",
        "%s is set to version %s. Enter a new version or press enter "
        "to continue." % (package.name, package.version))

    result = package.set_version(version)
    if result is None:
        g.abort(
            "Invalid version. You must choose a version that is "
            "higher than, or equal to your current version.")

    # Go through config files
    g.text(' ')
    g.text("PyRelease will now attempt to locate any config files")

    for key, klass in package.user_info.items():
        choices = dict(
            pypirc="~/.pypirc - Used for uploading to PyPi. "
                   "*Needed if you also want to upload to PyPi.",
            gitconfig="~/.gitconfig - Used for interacting with git.",
            hgrc="~/.hgrc - Currently not used for anything. "
                 "* Safe to leave as None."
        )

        g.red_text("\n * Detected a %s file." % key)

        # TODO: Fix me, not all configs are the same..
        name = g.prompt("Username: ", klass.author or "None",
                        choices[key], step=False)

        email = g.prompt("Email ", klass.author_email or "None",
                         step=False)

        package.user_info[key].author = name
        package.user_info[key].author_email = email

    # Verify project name
    g.text(" ")
    package.name = g.prompt(
        "Release name:", package.name,
        "Is %s the name you want to go with for your release? "
        "We try to guess it based on the name of the file or "
        "directory you ran PyRelease in so it's not always what "
        "you may want. If you want, you can rename you script "
        "and next time you run PyRelease it will automatically "
        "pick up the change." % package.name)
    rv = str("".join([i for i in str(package.name) if i.isalpha()]))
    package.name = rv

    # Package short description
    g.text(" ")
    package.description = g.prompt(
        "Short Description:", package.description,
        "PyPackage tries to automatically fill the package "
        "description based on the first doc-string found "
        "in the target module. Sometimes this doesn't "
        "always turn out right, so here's your chance to "
        "fix it. This is the same description that will "
        "show on the PyPi package index so try and make "
        "it as short and descriptive as possible.")

    # Authors name
    g.text(" ")
    package.author = g.prompt(
        "Author: ", package.author,
        "Your name as you want it to appear in the documentation "
        "for your release.")

    # Authors e-mail
    g.text(" ")
    package.author_email = g.prompt(
        "E-mail: ", package.author_email,
        "Leaving an e-mail gives people who use your package a way to "
        "reach you with feedback and support.")

    # Verify requirements
    def list_dependencies():
        for dep in package.requirements:
            g.text(" ")
            g.red_text(dep)

    g.text(" ")
    g.text("PyRelease has analyzed %s and has found these dependancies." %
           package.name)
    list_dependencies()

    g.text(" ")
    add_deps = g.prompt(
        "Add dependencies to list? ", False,
        "You can append more dependencies to the list. You can't however "
        "delete entries, this will probably be implemented in the future.")
    if add_deps:
        g.text(" ")
        while 1:
            dependencies = g.prompt(
                "Please enter any dependencies you want to append to "
                "the list. Separate each entry with an empty space.", "")
            if dependencies != "":
                package.requirements.extend(dependencies.split(" "))
            list_dependencies()
            g.text(" ")
            confirm = g.prompt("Is this correct?"
                               % package.requirements, True)
            if confirm:
                break

    # Load up the Builder.
    g.text(" ")
    g.green_text("Loading builder.")
    builder = Builder(package, build_dir=target)
    g.text(" ")

    # Verify License
    _license = package.package_info['license']
    if _license is None:
        g.text(" ")
        proceed = g.prompt(
            "Choose a License -", True,
            "Having a license for your source code is always a good idea. "
            "By default PyRelease adds an MIT license to your source, if"
            "you haven't set the variable `__version__` in your script. "
            "You can choose from a few others that we have. If you want a "
            "license that's not in this list, enter None and copy a license "
            "file into the package directory before you build and it will "
            "be included. Or let us know and we can add the license you want. "
            "Yes to pick a license or no to skip.")
        if proceed:
            for l_name in builder.LICENSES.keys():
                g.text(" ")
                g.red_text("%s" % l_name)

            g.text(" ")
            _license = g.prompt(
                "Choose a License", "MIT",
                "Choose from the list, if the license you want isn't "
                "there let us know so we can add it.! Make sure you type "
                "the name exactly how you see it.")
        package.set_license(_license)

    g.red_text("Using license: %s" % package.license)
    g.text(" ")
    # build_docs = g.prompt(
    #     "Make pydoc help page? ", True,
    #     "Pyrelease can invoke pydoc to automatically create a index.html "
    #     "file with your script api auto-documented.")

    # Set build directory
    g.text(" ")
    build_dir = g.prompt(
        "Build directory", builder.build_dir,
        "You can specify a directory that you would like your "
        "package to be created in. Otherwise a default temp "
        "folder will be made automatically in the current working "
        "directory")
    builder.build_dir = os.path.abspath(build_dir)

    # --------------------------------------Build all packages.
    # TODO: Fix error reporting on this part and put some hooks
    # between the calls
    g.text(" ")
    g.cyan_text("Pyrelease is ready to build your package.")
    g.text(" ")
    click.pause()

    g.cyan_text("Building README.rst")
    builder.build_readme()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building LICENSE.md")
    builder.build_license()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building MANIFEST.in")
    builder.build_manifest()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building requirements.txt")
    builder.build_requirements()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Building setup.py")
    builder.build_setup()
    g.green_text("Complete.")

    g.text(" ")
    g.cyan_text("Creating package")
    builder.build_package()
    g.green_text("Complete!")

    errors = package.errors
    # -------------------------------- Package creation complete.

    if errors:
        g.red_text("Build completed with errors..!")
        g.abort(
            "There were errors detected during the build, "
            "please check the error.log file for more details.")
    else:
        g.green_text("Build completed successfully!")

    # Preview README.rst
    g.text(" ")
    preview_readme = g.prompt(
        "Preview README.rst file? ", True,
        "You can preview your auto-generated README.rst file now "
        "if you'd like. This will open up your default browser to "
        "a preview of the file. When you're ready to proceed again, "
        "come back to the termianl and press enter, which will end "
        "the browser session (but won't close the tab)")
    g.text(" ")
    if preview_readme:
        shell_session = builder.preview_readme()

        while 1:
            g.text(" ")
            click.pause()
            shell_session.kill()
            break
    URLS = dict(
        pypi="https://pypi.python.org/pypi/",
        test_pypi="https://testpypi.python.org/pypi/", )

    # Build files
    g.text(" ")
    g.cyan_text("Pyrelease is ready to build your package distros.")
    g.text(" ")
    click.pause()
    builder.build_distros(suppress=True)

    if builder.success:
        g.green_text("Builds finished without error.")
    # else:
    #     g.green_text("There were errors during the build, "
    #                  "look at the debug.log for more details.")

    g.text(" ")
    g.yellow_text("Have a look at your new package.")
    click.launch(os.path.abspath(builder.build_dir))

    # Upload files
    g.text(" ")
    g.cyan_text("Pyrelease is ready to upload your package!")
    g.text(" ")
    click.pause()
    g.text(" ")
    builder.use_test_server = g.prompt(
        "Use test PyPi server?", True,
        "It's always a good idea to check your project on the "
        "PyPi test site before committing to the regular site. "
        "Using the test site requires you to register the "
        "package first, but don't worry, we do that part too. "
        "[Y]es for test server or [n] for regular PyPi.")

    # TODO: Shorten this stuff.
    if builder.use_test_server:
        register_package(g, builder)
        builder.upload_to_pypi_test_site()
    else:
        builder.upload_to_pypi()

    g.text(" ")
    if not builder.success:
        # TODO: Figure out any error codes..
        # g.red_text("Upload completed with errors. "
        #            "Did you remember to set the correct version?")
        pass
    else:
        g.green_text("Upload completed successfully!")
    g.text(" ")
    view_on_pypi(g, builder, package, URLS)
    g.text(" ")
    if builder.use_test_server:
        upload = g.prompt(
            "Ready for upload?", True,
            "Are you're ready to put your release on Pypi? saw anything "
            "you want to fix first you can always re-run PyRelease after.")
        if upload:
            builder.use_test_server = False
            builder.upload_to_pypi()
            g.text(" ")
            view_on_pypi(g, builder, package, URLS)

    g.print_footer()


main = release

if __name__ == '__main__':
    main()
