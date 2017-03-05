from __future__ import print_function
import sys

__version__ = "0.1.1"   # This will set the version
__license__ = "MIT"     # This sets the license

# The package description comes from the docstring of the
# first function in __all__
__all__ = ["main"]


def say_hello(name):
    print("Hello " + name + "!")


def main():
    """My hello world application"""
    args = sys.argv
    if len(args) > 1:
        name = args[1]
    else:
        name = "world"
    say_hello(name)
