from os import path
from setuptools import setup
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

__version__ = '0.1.0'

SETUP_DIR = path.abspath(path.dirname(__file__))


# get the dependencies and installs
with open(path.join(SETUP_DIR, 'requirements.txt')) as f:
    all_reqs = f.read().split('\n')


install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]


setup(
    name='pyrelease',
    version=__version__,
    long_description=read_md('README.rst'),
    license='MIT',
    author='Scott Doucet',
    author_email='duroktar@gmail.com',
    description='A simple config parser that supports JSON and YAML',
    packages=['pyrelease'],
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points={
        'console_scripts': [
            'pyrelease=pyrelease.cli:main',
            'pyrelease-cli=pyrelease.cli:main',
        ],
    },
)
