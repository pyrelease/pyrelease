#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
import sys
import click
import requests


__all__ = ['MyMainClass', 'main']
__version__ = '0.1.1'
__license__ = 'BSD-2'


class MyMainClass(object):
    """MyMainClass docstring Description"""

    def __init__(self, value):
        self.value = value
        self.cli = click

    def print(self, text):
        self.cli.echo = text

    def __repr__(self):
        return "<MyMainClass(value=%s)>" % self.value


def main():
    print("In main")