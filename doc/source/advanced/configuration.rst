Configuration
=============

This document covers more advanced configuration for the framework. If you want just a basic configuration, please see :ref:`tutorial_configuration`


.. _manual_configuration:

Manual Configuration
--------------------

Manual configuration can directly be added in :file:`conf/custom.conf`.

The parser used to read the configuration is based on Python's `ConfigParser <https://docs.python.org/3/library/configparser.html>`_.

An extended interpolation is enabled using ConfigParser's `ExtendedInterpolation <https://docs.python.org/3/library/configparser.html#configparser.ExtendedInterpolation>`_

This means you can use cross-sections references, like this :

Let's say you have a section named ``SQLITE``, containing a key ``INSTALL_DIRECTORY``. Then in the section ``DEADLOCK``, you can set ``INSTALL_DIRECTORY = ${SQLITE:INSTALL_DIRECTORY}``.


Variable Meanings
-----------------

Here are the different sections and variables used by |project| :

    * [DEFAULT] : this section is for change that should affect all other sections
        * programs : the programs |project| supports
        * log_level : the log level, to tweak the verbosity permanently. ``20`` by default
        * llvm_bitcode : boolean to decide whether llvm bitcode should be created when compiling or not. ``True`` by default
        * compiler : the compiler to use. ``base.clang`` by default
        * module_handling : whether the framework should install required python modules by itself or not. ``True`` by default
        * dependencies : |project| dependencies
        * git_protocol : the protocol to use when using git (ssh or https). ``ssh`` by default
        * default_directory : the default directory to store everything. ``~/bugbase-work`` by default.
        * log_file : the location of the log file. ``${default_directory}/error.log`` by default

    * [install] : this section is used by the install script
        * build_directory : the directory where to build all programs. ``${default_directory}/build`` by default
        * install_directory : the directory where to install programs. ``${default_directory}/install`` by default
        * source_directory : the directory where to store downloaded sources. ``${default_directory}/src`` by default
        * make_args : arguments to pass to make (comma separated). ``-j1`` by default

    * [utilities] : this section is used by utility programs : compilers, wllvm, etc
        * install_directory : the directory where to install utilities. ``${install:install_directory}/utils`` by default

    * [trigger] : this section contains information related to the trigger script
        * core_dump_location : directory to write coredumps into. ``/tmp/coredumps`` by default
        * core_dump_pattern : the coredump pattern. ``%E.core`` by default
        * core_dump_filter : the kernel coredump filter. ``0x7f`` by default
        * exp-results : the directory to store experiments results. ``${default_directory}/exp-results`` by default
        * workloads : the directory where to generate files for some triggers. ``${default_directory}/workloads`` by default

    * [plugins] : this section contains information related to plugins
        .. _additional_repositories:

        * additional_repositories : a list of third party repositories containing plugins, separated by a comma. Empty by default.
        * enabled_plugins : a list  of enabled plugins in the form $package.$name, separated by a comma. ``base.fail, base.success`` by default
