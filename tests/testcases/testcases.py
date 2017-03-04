import sys
import click
import requests


__all__ = ['MyMainClass', 'main']
__version__ = '0.1.1'
__license__ = 'BSD-2'
#################################


class MyMainClass(object):
    """ My package short description """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "<MyMainClass(value=%s)>" % self.value


def main():
    args = sys.argv
    if len(args) <= 1:
        return MyMainClass("Default")
    else:
        return MyMainClass(*args[1:])
