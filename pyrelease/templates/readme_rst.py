TEMPLATE = """\
{name}
===============================


.. image:: https://img.shields.io/pypi/v/{name}.svg
        :target: https://pypi.python.org/pypi/{name}


{description}


* Documentation: {url}
* License: {license}


Installation
============


Stable release
--------------

To install {name}, run this command in your terminal:

.. code-block:: console

    $ pip install {name}

This is the preferred method to install {name}, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for {name} can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/{author}/{name}

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/{author}/{name}
.. _tarball: https://github.com/{author}/{name}/tarball/master

Usage
=====

To use {name} in a project::

    import {name}



Credits
=======

* {author} {author_email}


This package was created with PyRelease_ package maker.

.. _PyRelease: TODO: Get this address
"""
