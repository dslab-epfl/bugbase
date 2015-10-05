Bugbase : reliable experiments
==============================

What is Bugbase ?
-----------------

Bugbase is a framework for benchmarking instrumentation tools on programs.

It was developed as part of an Intel-EPFL collaboration around concurrency bugs, thus the current strong focus of
Bugbase concerning concurrency bugs.


Why should I use Bugbase ?
--------------------------

When you have to run multiple kinds of instrumentation on the same program, need to benchmark each one, and repeat this for a dozen of programs, the process quickly becomes cumbersome.

Bugbase was developed to remove this burden from the developer and allows running and repeating these tests easily.

Did you write a paper and a third party has doubts about the meaningfulness of your data and you need to re-test everything again and you can't reproduce your data ? Or someone simply asked you your protocol to reproduce it themselves and you end up having to configure everything for them ?

Bugbase allows you to avoid that, streamlining the whole process and allowing your experiments to be reproduced easily


Using Bugbase
-------------

This is a quick introductory guide on how to use Bugbase. If you want to have more information, please see `complete documentation`_.

Getting the sources
^^^^^^^^^^^^^^^^^^^

Installing Bugbase from `Github <https://github.com/dslab-epfl/bugbase>`_ using git with ::

    $ git clone git@github.com:dslab-epfl/bugbase

Configure Bugbase
^^^^^^^^^^^^^^^^^

Bugbase provides a script `configure.py` that will provide you an automated way of installing various plugins and configure Bugbase to work the way you want ::

    $ ./configure.py


You can also, for more precise configuration edit `conf/custom.conf` which details are explained in the complete documentation (see `complete documentation`_)

Preparing benchmarks
^^^^^^^^^^^^^^^^^^^^

Once you have configured Bugbase, you need to install programs to run your experiments on ::

    $ ./install.py ${program_names or all} #(see ./install.py --help for more information)


Running experiments
-------------------

Running experiments can be launched through the `run.py` executable ::

    $ ./run.py <plugin> <program_name>

For example you could use : ::

    $ ./run.py success pbzip-2094

For more information, please see ::

    $ ./run.py --help


.. _complete documentation:

Building documentation
----------------------

As this README is not sufficient to show all of Bugbase features and interest, a complete documentation is shipped with it.

The documentation is built using Sphinx, which you can install by running ::

    $ sudo apt-get install python3-sphinx

And then you can build the documentation like ::

    $ cd ${bugbase_root}/doc; make {html,pdf, etc}

This will generate Bugbase documentation in your preferred format.
