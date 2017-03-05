Examples
========

Some examples to demonstrate PyRelease usage.


helloworld
----------

No example section would be complete without it!

Instructions::

    $ cd examples/helloworld

    $ pyrelease .

*Follow the wizard*

 **Stop after the build phase**
::

    $ cd helloworld.0.1.1

    $ pip install . --user

    $ cd ~

    ~ $ helloworld
    Hello World!

    ~ $ helloworld Friend
    Hello Friend!


simple_example
--------------

An example of a config parser style package.

Instructions::

    $ cd examples/simple_example

    $ pyrelease .

*Follow the wizard*

 **Stop after the build phase**
::

    $ cd trabconfig.0.1.1

    $ pip install . --user

    $ python

    >>> import trabconfig

    >>> config = trabconfig.trabConfig()



cowsay
------

This is an example using a python implementation of cowsay (legalese below).

To install this one:

    $ cd examples/cowsay

    $ pyrelease .

*Follow the wizard*

 **Stop after the build phase**
::

    $ cd cowsay.1.0.0

    $ pip install . --user

    $ cd ~

    ~ $ helloworld
    Hello World!

    ~ $ helloworld Friend
    Hello Friend!



legals
------

cowsay-py is a python implementation of the cowsay program by
Tony Monroe: http://www.nog.net/~tony/warez/cowsay.shtml

Copyright 2011 Jesse Chan-Norris <jcn@pith.org>

LICENSE

cowsay-py is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

cowsay-py is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.