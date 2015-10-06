Bugbase : reliable experiments
==============================

What is Bugbase ?
-----------------

Bugbase is a framework for evaluating bug detection and root cause diagnosis tools.

It was developed as part of an Intel-EPFL collaboration in the context of the [Failure Sketching](http://dslab.epfl.ch/pubs/gist.pdf) work.


How can Bugbase help me ?
--------------------------

If you have a bug detection/classification/root cause diagnosis tool to evaluate, bugbase allows you to do that with a simple plugin architecture.

Using Bugbase
-------------

This is a quick introductory guide on how to use Bugbase. If you want more information, please see the `complete documentation`_.

Getting the sources
^^^^^^^^^^^^^^^^^^^

Install Bugbase from `Github <https://github.com/dslab-epfl/bugbase>`_ using git with ::

    $ git clone git@github.com:dslab-epfl/bugbase

Configuring Bugbase
^^^^^^^^^^^^^^^^^

Bugbase has a `configure.py` script that will automatically install various plugins and configure Bugbase to work the way you want ::

    $ ./configure.py


You can also edit `conf/custom.conf` . Details are explained in the complete documentation (see `complete documentation`_)

Preparing benchmarks
^^^^^^^^^^^^^^^^^^^^

Once you have configured Bugbase, you need to install the programs to run your experiments on ::

    $ ./install.py ${program_names or all} #(see ./install.py --help for more information)


Running experiments
-------------------

Experiments can be launched with `run.py` ::

    $ ./run.py <plugin> <program_name>

For example you could use : ::

    $ ./run.py success pbzip-2094

For more information, please see ::

    $ ./run.py --help


.. _complete documentation:

Building documentation
----------------------

You can obtain the complete documentation by ::

    $ sudo apt-get install python3-sphinx

And then you can build the documentation by ::

    $ cd ${bugbase_root}/doc; make {html,pdf, etc}

This will generate the Bugbase documentation in your the preferred format.
