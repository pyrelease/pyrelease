# coding=utf-8
import os
import logging

from functools import partial
import click

logger = logging.getLogger('pyrelease')
logger.setLevel(logging.DEBUG)


class Generator(object):
    """This class is taken directly from the `quickstart.py` for `Lektor`
     the static site generator by Armin Ronacher Licensed under the BSD-3
     clause. I have added a few methods since.
     """

    def __init__(self):
        self.question = 0
        self.options = {}
        self.term_width = min(click.get_terminal_size()[0], 78)
        self.e = click.secho
        self.w = partial(click.wrap_text, width=self.term_width)

    def abort(self, message):
        click.echo('Error: %s' % message, err=True)
        raise click.Abort()

    def prompt(self,
               text,
               default=None,
               info=None,
               step=False,
               allow_none=False):
        # self.e('')
        if step:
            self.question += 1
            self.e('Step %d:' % self.question, fg='yellow')
        if info is not None:
            self.e(click.wrap_text(info, self.term_width - 2, '| ', '| '))
        text = '> ' + click.style(text, fg='green')

        if allow_none is True:
            rv = click.prompt(text, default=default, show_default=True)
            return rv
        elif default is True or default is False:
            return click.confirm(text, default=default)
        else:
            return click.prompt(text, default=default, show_default=True)

    def title(self, title):
        self.e(title, fg='cyan')
        self.e('=' * len(title), fg='cyan')
        self.e('')

    def red_text(self, text):
        self.e(self.w(text), fg='red')

    def green_text(self, text):
        self.e(self.w(text), fg='green')

    def yellow_text(self, text):
        self.e(self.w(text), fg='yellow')

    def cyan_text(self, text):
        self.e(self.w(text), fg='cyan')

    def text(self, text):
        self.e(self.w(text))

    def confirm(self, prompt):
        self.e('')
        click.confirm(prompt, default=True, abort=True, prompt_suffix=' ')

    def print_header(self):
        self.text(" ")
        self.title("PyRelease - Alpha -")
        self.yellow_text(
            "PyRelease is an open-source, MIT licensed. It was made in part by Illume "
            "and traBpUkciP (Scott Doucet) from a desire to make basic python script "
            "packaging easy and effective.")
        self.text(" ")

    def print_footer(self):
        self.text(" ")
        self.title("PyRelease")
        self.green_text(
            "Thanks for using PyRelease! If you have any suggestions please let us know "
            "either on GitHUb or by e-mail.")
        self.print_header()

    def cls(self):
        click.clear()
