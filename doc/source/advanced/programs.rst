.. _adding_programs:

Adding Programs
===============

To be usable by |project|, a program needs two things:
    * to be declared in :file:`conf/default.conf` of :file:`conf/custom.conf`.
    * to have its own directory in :file:`data/`

The directory for the program has the following infrastructure :
    * :file:`patches` : a set of patches to make the program work, containing files :file:`*.patch`
    * :file:`src` : directory containing different sources if needed
    * :file:`install.conf` : a file explaining how to install the program, see :ref:`install_conf`
    * :file:`README.md` : a file explaining the bug and from where it is taken
    * :file:`trigger.py` : the base trigger file to exploit the bug in the program, see :ref:`trigger_py`



.. _install_conf:

Install.conf format
-------------------

The :file:`install.conf` is a `ini formatted file <http://en.wikipedia.org/wiki/INI_file>`_ read using the `configparser module <https://docs.python.org/3/library/configparser.html>`_ using `extended interpolation <https://docs.python.org/3/library/configparser.html#configparser.ExtendedInterpolation>`_

Example
^^^^^^^

For example, here is the configuration file from pbzip2 version 0.9.4. For a complete overview of required and additional arguments, please see :ref:`install_conf_arguments`

    | [PBZIP]
    | name = pbzip-2094
    | url = http://www.compression.ca/pbzip2/pbzip2-0.9.4.tar.gz
    |
    | patches_pre_config = makefile.patch
    | configure = False
    |
    | depend = libbz2-dev
    |
    | executable = pbzip2
    |
    | buggy_file = pbzip2.cpp
    | buggy_function = consumer
    | buggy_line_number = 1004


.. note::
    It is possible to have multiple sections in the same file, for when you need helpers (like php for apache or using a library). For example see program apache-21287

.. _install_conf_arguments:

Install.conf arguments
^^^^^^^^^^^^^^^^^^^^^^

This is the list of required arguments for an install.conf section:
    * name : the name of the program, must match the directory name
    * executable : the executable name
    * buggy_file : the file where the bug is
    * buggy_function : the function where the bug is
    * buggy_line_number : the line number where the bug is
    * one of :
        * url : the url to fetch the sources
        * git_repo : the git repository from which to fetch the sources
        * svn_repo : the svn repository from which to fetch the sources


These other options are also given if you need more control :
    * display_name : the name of the program as displayed to the user, defaults to ``${name}``
    * working_dir : the directory where to compile the sources. Will be prepended by the build_dir from the global configuration. Defaults to ``${name}``
    * install_directory : the directory where to install sources. Will be prepended by the install_dir from the global configuration. Defaults to ``${name}``
    * configure : the program to use for configuration. Defaults to ``configure``, can also be cmake or False for no configuration
    * executable_directory : the place where the executable is installed, to create calling functions. Defaults to ``bin/``
    * libraries : a CSV list of libraries the program relies on, which have to be defined in the same :file:`install.conf`
    * depend : a CSV list of packages on which the program depends
    * patches_pre_config : a CSV list of patches names to be applied before configuration
    * patches_post_config : a CSV list of patches names to be applied after configuration
    * patches_post_install : a CSV list of patches names to be applied after installation
    * copy_post_install : a CSV list of files to copy to some install directory. The default format is file_name=>path
    * configure_args : arguments to pass to the configure script
    * make_args : arguments to pass to the make command


.. _trigger_py:

trigger.py format
-----------------

The trigger.py file will certainly be the most complicated part to add a new program. That's why |project| provides several helpers to ease the process :

    * .. autoclass:: lib.trigger.RawTrigger
    * .. autoclass:: lib.trigger.BaseTrigger
    * .. autoclass:: lib.trigger.TriggerWithHelper
    * .. autoclass:: lib.trigger.ApacheTrigger

Most case could be handled by BaseTrigger and TriggerWithHelper, for respectively basic programs and client-server ones. Apache has a special trigger, as there are several apache bugs in the repository. More more specific triggers could come if we see many of the same type.

To create a trigger for a program, you should therefore just subclass one of these and define the abstract class they contain. You can have more control over it by overriding more functions.

Be careful when defining the trigger class, to correctly define the commands. Here are their explanation :
    * for simple triggers:

        * `success_cmd`: this command should launch a successful run. Can be the same as `failure_cmd` if the run is not input dependant
        * `failure_cmd`: this command should launch a failing run. Can be the same as `success_cmd` if the run is not input dependant

    * for client-server triggers:
        * `start_cmd`: this command should start the server
        * `stop_cmd`: this command should stop the server

The code is well documented, so you are encouraged to read it if you miss something. Otherwise you can also read examples such as pbzip-2094, memcached-127 or any apache depending on your need.

.. warning::
    You should always at least subclass RawTrigger, in order to make sure your trigger is compatible with the framework


.. _benchmark.py:

benchmark.py format
-------------------

For basic cases (client only) programs, there should be no real need to do anything, except perhaps use a larger test-case.

If you need to modify the environment before a benchmarking run, you should, in __init__.py of the trigger, allocate a callable to self.benchmark.pre_benchmark_run.

For more complicated use cases, you can see :
    * .. autoclass:: lib.trigger.benchmark.RawBenchmark
    * .. autoclass:: lib.trigger.benchmark.BaseBenchmark
    * .. autoclass:: lib.trigger.benchmark.BenchmarkWithHelper
    * .. autoclass:: lib.trigger.benchmark.ApacheBenchmark

.. note::
    A benchmark run should store in self.trigger.returned_information a list containing the results of the run.

.. note::
    Preferably, throw the first few runs to ensure consistency and reduce side effects.

Testing new programs
^^^^^^^^^^^^^^^^^^^^

Testing is important to get a stable framework. Fortunately, you don't have to write a single line to get your program tested !

Tests are automatically generated by |project| at runtime for every program.
