from os import path
from setuptools import setup


__version__ = '0.1.0'

SETUP_DIR = path.abspath(path.dirname(__file__))


with open(path.join(SETUP_DIR, 'README.rst')) as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(SETUP_DIR, 'requirements.txt')) as f:
    all_reqs = f.read().split('\n')


install_requires = [x.strip() for x in all_reqs if 'git+' not in x]


setup(
    name='pyrelease',
    version=__version__,
    long_description=long_description,
    license='MIT',
    author='traBpUkciP',
    author_email='duroktar@gmail.com',
    description='A simple single file package builder.',
    packages=['pyrelease',
              'pyrelease.licenses',
              'pyrelease.templates'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'pyrelease=pyrelease.cli:main',
            'pyrelease-cli=pyrelease.cli:main',
        ],
    },
)
