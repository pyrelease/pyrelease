import sys


__all__ = ['MyMainClass', 'main']
__version__ = '0.1.1'
__license__ = 'BSD-2'


class MyMainClass(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "<MyMainClass(value=%s)>" % self.value

if __name__ == '__main__':
    args = sys.argv

    hero = None
    if len(args) <= 1:
        hero = MyMainClass("Default")
    else:
        hero = MyMainClass(*args[1])
