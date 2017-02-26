PyRelease
=========


Development
-----------

Things that I'd like to get finished by next weekend.

**Documentation**
 - intro
 - quickstart


**Logging**
 - info channel for all build steps
 - it's gonna go fast so that has to be dealt with.
 - error messages should contain as much info as possible to help solve the problem. Include urls to documentation, etc..
 - if any user files don't parse print out a correct format (most have a __repr__ already, ala Remi)


**When to panic**
 - if there is a setup.py file (provide error message, only works for single files)
 - when package name already exists server sends 403 error


**Core features**
 - Auto generate License file based on scraped info from configs and/or package file(s)
 - Generate change log from git info
 - Tag and release in git
 - Get version number from Pypi (if package exists ?)
 - Support for data/ folders
 - Support for modules contained within package (ie: /Mypackage/mypackage/\_\_init\_\_.py or /Mypackage/mypackage/mypackage.py
 - Generate a README.rst for compatibilty with PyPi


**Testing**
 - Make a test directory structure containing invalid build scenarios to test against.