TEMPLATE = """\
from os import path
from setuptools import setup{find_packages}

SETUP_DIR = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(SETUP_DIR, 'README.rst')) as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(SETUP_DIR, 'requirements.txt')) as f:
    all_reqs = f.read().split('\\n')


setup(
    name='{name}',
    version='{version}',
    description='{description}',
    long_description=long_description,
    url='{url}',
    author='{author}',
    author_email='{author_email}',
    license='{license}',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    {packages}
    {py_modules}
    {install_requires}
    {console_scripts}
)
"""

CONSOLE_SCRIPTS = """entry_points={{
        'console_scripts': [
            '{0}={1}:main',
        ],
    }},"""

PACKAGE_CONSOLE_SCRIPTS = """entry_points={{
        'console_scripts': [
            '{0}={1}.{2}:main',
        ],
    }},"""
