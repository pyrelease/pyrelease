PyRelease -Alpha-
=================

Sick of having 40 files in a python repo to release some code into the world?
PyPackage generates all the boilerplate code that the python packaging world
decides we need and publishes your package to PyPi. A link to the blog_ that
started it all.

*Tested on Python 3.6. and Python 2.7*

**Features**

- CLI interface with setup wizard for creating packages interactively
- Automatically creates a Github and PyPi compatible README file with browser preview
- Automatic entry-point script creation if file has main function
- Automatic setup.py file creation
- Automatically detects and includes data folder
- Automatically add or pick from an assortment of Licenses
- Automatically finds dependencies and creates a requirements.txt file.
- Automatic creation of package wheels and binaries
- Build steps are split into many stages allowing for custom hooks at almost any point of the build.
- Uploads to PyPi *main* server OR *testing* server

This doesn't cover everything, check out the code if you want to see more.


**DISCLAIMER:**

PyRelease is in alpha stage so if something doesn't seem to be working right, it
probably isn't. Crashes are a great opportunity for a bug report so please don't
hesitate to leave one, but take care to make it as detailed as possible so as to
not pee in my cereal.


Why should I use this?
----------------------

As an example, you have a python file that you have found to be useful
and would like to put together all the supporting files to make it available
on PyPi. Simply point PyPackage at the file and in seconds you'll have a
release that can usually be put straight onto PyPi with little to no modification.

This is great for files that are useful amongst co-workers or friends and
allows you to make them pip installable in *seconds* and creates all the
relevant packaging material to go with it.

This is what you get when you run your script through PyPackage.

- A README.rst that is compatible on PyPi *and* GitHub
- A proper setup.py file that provides an entry point to the scripts `main` function
- A MANIFEST.in file that knows to include a `data` folder
- An auto-generated requirements list for your package dependencies
- wheels and source distros are created automatically
- Things like license and version auto-discovered from the code
- Finished package is created in a folder with the version as part of the name for simplicity
- *Your package becomes pip installable in seconds with a homepage on PyPi that isn't totally mangled*

**tl;dr**

Turn this::

    - folder
        - myscript.py

into this::

    - folder
        - myscript.0.1.1
            - myscript.py
            - README.rst
            - MANIFEST.in
            - LICENSE.md
            - requirements.txt
            - setup.py
        - myscript.py

Automagically.


**PyRelease uses these third party libraries**

- Click_
- restview_
- twine_
- pyyaml_

Installation
------------

Download Package from github, unzip into a directory and open up the
terminal. From the same directory that you unzipped the files run::

    $ python setup.py install


Or you can use pip::

    $ pip install -e . --user


This will install pyrelease in "editable" mode and any changes you make
to the source code will be reflected when you run the pyrelease. This way
you can work on and modify the code without having to rebuild and install
pyrelease everytime you modify the code.

**Note:** To be able to upload to the PyPi server and test server you must
have a ~/.pypirc file with these sections::

    [distutils]
    index-servers=
        pypi
        testpypi

    [testpypi]
    repository = https://testpypi.python.org/pypi
    username = *Test PyPi Username*     # Enter your PyPi Test Site username here

    [pypi]
    repository = https://pypi.python.org/pypi
    username = *PyPi Username*          # Enter your PyPi username here


Command-Line-Interface
----------------------

To run, just cd to the folder of the your target python file and type::

    $ pyrelease-cli [target]


or just::

    $ pyrelease [path]


Try one of the scripts from the examples folder to get an idea of how
it works::

    $ cd examples/simple_example
    $ pyrelease-cli trabconfig.py


PyRelease will attempt to package whatever file you point it to . You
can also use other targets like "." or a single python script (file) or
`__init__.py` file.

The way it works is during the build, if the target package has a `main`
function, then it will be assumed this is a `script` and will be added to
the setup.py file as a console script entry point, which can then be
accessed from the command line by the same name as the source file. ex: If
the package name is `mypackage` and has a `main` function in the script,
it can be run from the command line by typing `$ mypackage`, which will
run whatever was in that `main` method.

If there's no main function then no entry point is made and the `package`
will be setup to run and install like any other python `package`. From
there you can use the library in python by importing as usual.


Where are the switches?
-----------------------

PyRelease is meant to be as simple as possible so it attempts to gather
information on the package as "naturally" as it can. User information is
fetched from user config files in the home directory, in particular it
checks for a .gitconfig and a .pypirc file, the latter of which is required
to upload your package to PyPi with PyRelease. It also get info from the
source file itself, in particular it looks for a few magic variables
and the docstring of the first callable found in the `__all__` magic
variable.

Here's a list of the things you can do to alter PyReleases behavior when
interacting with your release:

Alter magic variable.

 **__all__**
    - The first function found in this list will have its docstring used as the packages short description *by default*, the short description can be changed if there's an error so don't worry.

 **__license__**
    - If this is set PyPackage will attempt to include it with the package. This works using a template engine so more licenses can be added rather easily if requested. Currently included licenses can be found in the `pyrelease/licenses/` folder.

 **__version__**
    - If this is set then PyRelease will make this the default version when creating your release.

 **def main():**
    - If your package has a main function it becomes the script entry point once installed and invoked from the command line.

 **data** folder
    - If there is a folder named `data` alongside the script it will be included in the MANIFEST and packaged alongside the rest of the files in the release.


In a situation where you have a package that exists where the code is
located in __init__.py and the folder is the name of the package, then
PyRelease will name your release based on the folder name and include
the folder in the package release with the same layout. For example::

    - croutonlib/
        - __init__.py

Now assuming `__version__` is defined in `__init__.py` to be '1.1.1', here's
how you could call pyrelease with just a dot from the `croutonlib/` directory::

    $ pyrelease .

Which would give you::

    - croutonlib/
        - __init__.py
        - croutonlib.1.1.1/
            - croutonlib/
                - __init__.py
            - README.rst
            - MANIFEST.in
            - LICENSE.md
            - requirements.txt
            - setup.py

You can also call pyrelease with a dot in a directory where instead of the code
being in the `croutonlib/__init__.py` file it's in a file that shares its
name with its parent folder, for example 'megascript/megascript.py`


Giver Mode
----------

** Giver mode is out of order right now kiddos. Sorry!**

Cause sometime you just want it to hurry up and giver. The command line
switch --giver or just -G activates it. Here's an example::

    pyrelease --giver myscript.py


Sometimes though when ya giver, ya wanna be just a little be careful, so
there is a switch that sets the pypi test server as the destination, -T
or --test-pypi. Or just giver, whatever fills your boots.


Tests
-----

There are tests located in the `pyrelease/tests` folder. I recommend running
them with `nose` which can be installed with the included `requirements_dev.txt`
file. From the directory that PyRelease is located enter these commands::

    $ pip install -r requirements_dev.txt

    $ python -m nose

For a test coverage report use this command instead::

    $ python -m nose --with-coverage --cover-package pyrelease


Show All Console Messages
-------------------------

By default you won't see any of the scroll that normally occurs when you
invoke setuptools or twine or the webbrowser loader. You can turn these
messages on with the -V or --verbose switch. If you're experiencing trouble
this may help you determine the cause.


Logging
-------

If you experience any problems you can always check the error.log that will
be in the same directory that you originally ran pyrelease. It clears after
every session so if you want to save one or submit it you should change the
name or move it to another location.


Pro-Tip
-------

Pyrelease should be non-destructive of your files but be sure to make a
backup first if you do want to test on your own scripts. (I've never lost
a file with it but I don't wanna be *that* guy, so ***make backups***)


How does it Work?
-----------------

I have a small test package setup in `examples/simple_example/`. To try it
out just run::

    $ pyrelease-cli trabconfig.py

or::

    $ pyrelease trabconfig.py

Make sure you run it from inside `examples/simple_example/` . The finished
files are saved by default into a folder tagged with the version and name
of the package. It should include README.rst, LICENSE.md, MANIFEST.in,
and setup.py files, as well as copied over everything in the `data` folder
(if there was one). PyRelease also creates a log file containing all the
steps you made up to, and -hopefully- including the error. The file will
be named `error.log` and found in the current working directory.
For example, a file named my_script.py version 0.8.5 will produce a folder
named `/my_script.0.8.5`.


**Note:** This log clears at the start of each run so save any logs
you want to preserve as another file name. I intend to implement a rotating
file handler for the logger, but I've just been so busy writing out this
giant f^%&ing readme file I haven't got around to it yet ;)

Oh that's another thing, if this happens to help you in any way, consider
contributing back by helping with the todo list down there, or even help
by submitting any bugs or suggestion that might come your way. It's all
appreciated.



Things to know
--------------

Pyrelease is only for single file scripts.. There are many tools available
which would be more suitable for bigger projects and therefore pyrelease
intends to do one thing and to do it well, and that's stick to single file
scripts.


Development
-----------

The `PyPackage` class gathers and stores your package info and gets plugged
into the `Builder` class, which further breaks down the build sequence.

The CLI is tested to run in Python 2.7 and 3.6. That code is found in
`pyrelease/cli.py`. The CLI themed generator class is now in the
`pyrelease/generator.py` module.

The config file gathering logic is found in userdata.py (.gitconfig scraper, etc..)

There is a logger available for basic info messages. Just use `logger.info`
etc. to use it. There are a few shell helper functions located in shelltools.py.


Todo
----

Feel free to modify this to your hearts content. And if you want to help
with anything absolutely please do so, either by pull request or email,
whatever suits you.

**Documentation**

- frontpage
- intro
- quickstart
- api


**Logging**

- error messages should contain as much info as possible to help solve the problem. Include urls to documentation, etc..


**When to panic**

- if there is a setup.py file (provide error message, only works for single files)
- when package name already exists server sends 403 error


**Core features**

- Auto generate License file based on scraped info from configs and/or package file(s)
- Generate change log from git info
- Tag and release in git
- Get version number from Pypi (if package exists ?)
- Get info from git.
- Check name against PyPi servers for collisions
- Better support for modules contained within package (ie: /Mypackage/mypackage/\_\_init\_\_.py or /Mypackage/mypackage/mypackage.py


**Testing**

- Make a test directory structure containing invalid build scenarios to test against.
- Anything test related at all will be helpful.


Contributors
------------

Illumi -

- Creator
- Programming

Duroktar

- Programming
- Docs
- This stinkin' ginormous readme


License
-------
MIT - 2017 illume


.. _Click: http://click.pocoo.org/5/
.. _restview: https://mg.pov.lt/restview/
.. _twine: https://pypi.python.org/pypi/twine
.. _pyyaml: https://github.com/yaml/pyyaml
.. _blog: http://renesd.blogspot.ca/2017/02/what-would-python-packaging-zero-look.html