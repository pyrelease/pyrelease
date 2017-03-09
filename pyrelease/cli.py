#!/usr/bin/env
import os
import logging

from .generator import Generator
import click

# ######## LOGGING #########
logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)

# File handler
handler = logging.FileHandler(os.path.join(os.getcwd(), 'build.log'), 'w')
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
    g.yellow_text("Have a look at your new package online!")
    g.text(" ")
    if builder.use_test_server:
        click.launch(urls['test_pypi'] + package.name)
    else:
        click.launch(urls['pypi'] + package.name)
    g.text(" ")
    click.pause()


def choose_license(g, default="MIT"):
    from .licenses import LICENSES
    for l_name in LICENSES.keys():
        g.text(" ")
        g.red_text("%s" % l_name)

    g.text(" ")
    choice = g.prompt(
        "Choose a License", default,
        "Choose from the list, if the license you want isn't "
        "there let us know so we can add it.! Make sure you type "
        "the name exactly how you see it.")
    return choice


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
        response = builder.register_pypi_test_package()
        g.text(" ")
        g.green_text("Registration complete.")
        return response


# Helper function
def create_pypirc(g, package, builder):
    g.text(' ')
    username = g.prompt(
        "Username:", package.author,
        "Enter your Pypi username here. If you don't have an "
        "account you can follow this link to create one. "
        "https://pypi.python.org/pypi?%3Aaction=register_form ")

    g.text(' ')
    validate = g.prompt(
        "Continue?", True,
        "You have entered %s, is this correct?" % username)
    if validate:
        return builder.build_pypirc(username)
    else:
        create_pypirc(g, package, builder)


def giver(g, package, target, test_pypi):
        import random
        from .builder import Builder

        builder = Builder(package, build_dir=target)
        builder.use_test_server = test_pypi

        g.cls()

        g.print_header()
        g.red_text("   Giver Mode %s" % ("", "TEST SERVER")[test_pypi])

        message = [
            "Preparing data",
            "Reticulating splines",
            "Collecting data",
            "Prepping release",
        ]

        g.text(" ")
        msg = random.choice(message)
        with click.progressbar(length=7, label=msg) as bar:
            builder.create_build_dir()
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
@click.argument('project', default=".")
@pass_context
def release(g, project, giver, test_pypi, verbose, target):
    """Releasing python code - an experiment in zero config releases.

    Pyrelease gathers info for package, fills out necessary files, builds,
    then uploads to PyPi.
    """
    from .pyrelease import PyPackage
    from .builder import Builder

    package = PyPackage(project, verbose=verbose)

    if package is None:
        g.abort("Release failed, see the error log for more details.")

    # ------------------------------------Giver mode
    # TODO: Move me into a click command group
    if giver:
        giver(g, package, target, test_pypi)
    #######################################

    # ---------------- Clear the screen and start wizard
    g.cls()

    # ---------------------------------- Load from project file?
    if os.path.exists('release.info'):
        g.text(" ")
        load_savefile = g.prompt(
            "Load save file?", True,
            "PyRelease has detected a save file in the current directory.")

        if load_savefile:
            package.load()

    # ---------------------------------- Wizard intro
    g.text(' ')
    g.title("PyRelease wizard")
    g.green_text("This wizard will help guide you through setting up %s "
                 "for release on pypi. Don't worry, it's easy! "
                 "Press ctrl-D at any time to exit to the terminal" %
                 package.name)

    # ---------------------------------- Verify project name
    g.text(" ")
    package.name = g.prompt(
        "Release name", package.name,
        "Is %s the name you want to go with for your release? "
        "We try to guess it based on the name of the file or "
        "directory you ran PyRelease in, so it's not always what "
        "you may want. Only letters and numbers and decimals are"
        "allowed in the name." % package.name)
    rv = str("".join([i for i in str(package.name) if i.isalpha() or i == "."]))
    package.name = rv

    # ---------------------------------- Package short description
    g.text(" ")
    package.description = g.prompt(
        "Short Description", package.description,
        "PyPackage tries to automatically fill the package "
        "description based on the doc-string found in the "
        "first function listed in __all__. This doesn't "
        "always turn out right, so here's your chance to "
        "fix it. This is the same description that will "
        "show on the PyPi package index so try and make "
        "it as short and descriptive as possible.")

    # ---------------------------------- Make sure the version is correct.
    g.text(" ")
    version = g.prompt(
        "Version", package.version or "0.1.0",
        "%s is set to version %s. Enter a new version or press enter "
        "to continue." % (package.name, package.version), allow_none=False)
    package.version = version

    # ---------------------------------- Authors name
    g.text(" ")
    if package.author is None:
        package.author = package.user_info['gitconfig'].author
    package.author = g.prompt(
        "Author", package.author,
        "Your name as you want it to appear in the documentation "
        "for your release.")

    # ---------------------------------- Authors e-mail
    g.text(" ")
    package.author_email = g.prompt(
        "E-mail", package.author_email,
        "Leaving an e-mail gives people who use your package a way to "
        "reach you with feedback and support.")

    # ---------------------------------- Verify License

    g.text(" ")
    _license = package.license

    if _license:
        proceed = g.prompt(
            "Found license %s" % _license, True,
            "PyRelease has found a license variable in your package. Is %s "
            "the license you want to use?" % _license)
        if not proceed:
            _license = choose_license(g, _license)

    else:
        proceed = g.prompt(
            "Choose a License", True,
            "Having a license for your source code is always a good idea. "
            "By default PyRelease will add an MIT license to your source if "
            "no `__version__` variable was found in your module. However "
            "you can choose from a few others that we have. If you want a "
            "license that's not in this list, enter None and copy a license "
            "file into the package directory before you build and it will "
            "be included. Or let us know and we can add the license you want. "
            "Yes to pick a license or no to skip.")
        if proceed:
            _license = choose_license(g)

    package.license = _license

    g.text(" ")
    g.red_text("Using license %s" % package.license)

    # ---------------------------------- Verify requirements
    g.text(" ")
    g.text("PyRelease has analyzed %s and has found these dependancies." %
           package.name)

    def list_dependencies():
        if not package.requirements:
            g.text(" ")
            g.red_text("No dependencies detected")
        for dep in package.requirements:
            g.text(" ")
            g.red_text(dep)
    list_dependencies()

    g.text(" ")
    add_deps = g.prompt(
        "Add more dependencies to list?", False,
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

    # ----------------------- Save project?.
    g.text(" ")
    save_package = g.prompt(
        "Save project setting?", True,
        "PyRelease can save your configuration into a release.info file "
        "that can be used for future builds of %s" % package.name)
    if save_package:
        package.save()
        g.text(" ")
        g.cyan_text("    File saved.")

    # ----------------------- Load up the Builder.
    g.text(" ")
    g.green_text("Loading builder.")
    builder = Builder(package, build_dir=target)

    # ---------------------------------- Go through config files
    g.text(' ')
    g.text(' ')
    g.cyan_text("PyRelease will now attempt to locate any config files.")

    # ---------- Check for a .pypirc file. It's required to upload to pypi.
    g.text(' ')
    if not os.path.exists(os.path.expanduser('~/.pypirc')):
        g.red_text("    No .pypirc detected.")
        g.text(' ')
        proceed = g.prompt(
            "Create .pypirc?", True,
            "Would you like to create a .pypirc with the wizard? You can "
            "continue without it but you won't be able to upload to PyPi. "
            "https://docs.python.org/2/distutils/packageindex.html#pypirc")

        # Create the .pypirc
        if proceed:
            create_pypirc(g, package, builder)
            package.update_user_info()

    for key, config in package.user_info.items():
        choices = dict(
            pypirc="~/.pypirc - Used for uploading to PyPi. "
                   "*Needed if you also want to upload to PyPi.",
            gitconfig="~/.gitconfig - Used for interacting with git.",
            hgrc="~/.hgrc - Currently not used for anything. "
                 "* Safe to leave as None."
        )

        g.red_text("\n * Detected a %s file." % key)

        # TODO: Fix me, not all configs are the same..
        name = g.prompt("Username: ", config.author or "None",
                        choices[key], step=False)

        email = g.prompt("Email ", config.author_email or "None",
                         step=False)

        package.user_info[key].author = name
        package.user_info[key].author_email = email

    # ----------------------------------Set the build directory
    g.text(" ")
    build_dir = g.prompt(
        "Build directory", os.path.relpath(builder.build_dir),
        "You can specify a directory that you would like your "
        "package to be created in. This can also be handed in "
        "from the command line with the '-T' or '--target' "
        "option. If no value is passed in your folder will be "
        "made automatically in the current working directory")
    builder.build_dir = os.path.abspath(build_dir)

    # ------------------------------ Build pydocs
    # g.text(" ")
    # build_docs = g.prompt(
    #     "Make pydoc help page? ", True,
    #     "Pyrelease can invoke pydoc to automatically create a index.html "
    #     "file with your script api auto-documented.")

    #
    # Create the dir, will safely rename if path already exists

    # ---------------------------------- Build all packages.
    # TODO: Fix error reporting on this part and put some hooks between the calls
    g.text(" ")
    g.cyan_text("Pyrelease is ready to build your package.")

    g.text(" ")
    click.pause()

    builds = [
        (builder.create_build_dir, "Directories"),
        (builder.build_readme, "README.rst"),
        (builder.build_license, "LICENSE.md"),
        (builder.build_manifest, "MANIFEST.in"),
        (builder.build_requirements, "requirements.txt"),
        (builder.build_setup, "setup.py"),
        (builder.build_package, "Finished Release")
    ]

    g.text(" ")
    with click.progressbar(builds,
                           label="Status") as jobs:
        for build in jobs:
            g.green_text(" Building %s" % build[1])
            build[0]()

    errors = package.errors
    g.text(" ")
    if errors:
        g.red_text("Build completed with errors..!")
        g.abort(
            "There were errors detected during the build, "
            "please check the error.log file for more details.")
    else:
        g.green_text("Build completed successfully!")

    # ---------------------------------- Preview README.rst
    g.text(" ")
    preview_readme = g.prompt(
        "Preview README.rst file?", False,
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

    # ---------------------------------- Build files
    g.text(" ")
    g.cyan_text("Pyrelease is ready to build your package distros.")

    g.text(" ")
    build_distros = g.prompt(
        "Build Distros?", True,
        "For your release to be installable it needs to be built. "
        "The next step will build your project into an installable "
        "package, which can be uploaded or shared and installed via"
        "`python setup.py install` or `pip install . `")

    if build_distros:
        g.text(" ")
        g.yellow_text("    Building..")
        g.text(" ")
        builder.build_distros(suppress=True)

    if builder.success:
        g.green_text("Builds finished without error.")
    # else:
    #     g.green_text("There were errors during the build, "
    #                  "look at the debug.log for more details.")

    # ---------------------------------- Open file explorer
    g.text(" ")
    g.cyan_text("Your release has been built! Take a look..")
    click.launch(os.path.abspath(builder.build_dir))

    g.text(" ")
    click.pause()

    # ---------------------------------- Upload files
    g.text(" ")
    g.cyan_text("You're package is ready to be uploaded.")
    g.text(" ")
    builder.use_test_server = g.prompt(
        "Use test PyPi server?", True,
        "It's always a good idea to check your project on the "
        "PyPi test site before committing to the regular site. "
        "Using the test site requires you to register the "
        "package first, but don't worry, we do that part too. "
        "Yes for test server or no for regular PyPi.")

    if builder.use_test_server:

        g.text("")
        g.green_text("Registering Package")

        g.text("")
        # This is a function so giver can use it.
        register_package(g, builder)

        # Confirm upload to TEST SERVER
        g.text("")
        commit = g.prompt("Upload?", True,
                          "Continue to upload to the test site.")

        if commit:
            # Upload to TEST
            g.text(" ")
            g.green_text("Uploading to PyPi TEST site..")
            builder.upload_to_pypi_test_site(suppress=verbose)
            # if not builder.errors:
            #     # Show in browser
            #     g.text(" ")
            #     view_on_pypi(g, builder, package, URLS)
            # else:
            #     g.red_text(builder.errors)

    # Confirm upload to MAIN SERVER
    g.text("")
    upload = g.prompt("Upload to PyPi MAIN SERVER?", False,
                      "If you're satisfied with your release then you can "
                      "now upload it to PyPi, this is your last chance to "
                      "make any changes to your package.")

    if upload:
        # Upload to MAIN
        g.text("")
        proceed = g.prompt("You're really, really, sure?", True)

        if proceed:
            g.text("")
            g.green_text("Uploading to PyPi..")
            builder.upload_to_pypi(suppress=verbose)
            g.text(" ")
            view_on_pypi(g, builder, package, URLS)

    # Get errors etc..
    g.text(" ")
    if builder.uploaded:
        if not builder.success:
            # TODO: Figure out any error codes..
            # g.red_text("Upload completed with errors. "
            #            "Did you remember to set the correct version?")
            pass
        else:
            g.text(" ")
            g.yellow_text("    All uploads completed successfully!")

    click.pause("Press any button to finish.")
    g.text(" ")
    g.print_footer()


main = release

if __name__ == '__main__':
    main()
