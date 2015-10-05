.. highlight:: rst

Getting Started
===============

This document is meant to give a quick introduction on how to configure and use the framework

Getting |project|
-----------------

Installing Bugbase from `Github <https://github.com/dslab-epfl/bugbase>`_ using git with ::

    $ git clone git@github.com:dslab-epfl/bugbase

Or via http ::

    $ git clone https://github.com/dslab-epfl/bugbase.git


You can also directly `download <https://github.com/dslab-epfl/bugbase/releases>`_ an archive of a release

.. _tutorial_configuration:

Configuring |project| for your needs
------------------------------------

|project| can be configured in two different ways:
    * Using the :program:`configure.py` script
    * Manually editing :file:`conf/custom.conf`

We will only cover using the :file:`configure.py` script here. To get more information on how to manually :file:`conf/custom.conf` please refer to :ref:`manual_configuration`

:program:`configure.py` is an interactive way of editing the configuration and ensures one does not break the configuration.
It is sufficient in general. For more detailed modification of the configuration parameters, please see :ref:`manual_configuration`.

To run :program:`configure.py`, simply go to the root of |project| and type::

    $ ./configure.py

You can also give arguments to this script. For more information about the :program:`configure.py` script, type::

    $ ./configure.py --help

You should pay attention to the plugins you enable. Plugins determine |project|'s capabilities. You can also add other plugin repositories to enable more features. If you want to learn more about plugins and how to create them, please read :ref:`packages`.

.. _tutorial_install:

Installing programs
-------------------

You can install a program in bugbase by running ::

    $ ./install.py ${program_name}

To install all the programs within |project| at once ::

    $ ./install.py all

To get more information and to see which programs are available, you can run ::

    $ ./install.py --help


To get more information on how to add new programs to |project|, please read :ref:`adding_programs`.

Running workloads
-----------------

For running workloads, you can run ::

    $ ./trigger.py ${plugin} ${program}

in order to execute the given program with the given plugin.

The trigger script has much more options than that. You can see them all by running ::

    $ ./trigger.py --help

Some plugins also have some options you can give to them. To view a particular plugin help, type ::

    $ ./trigger.py ${{plugin} --help


