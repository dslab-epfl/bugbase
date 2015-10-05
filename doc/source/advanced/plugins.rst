.. _packages:

Packages and Plugins
====================

This document explains how to create and install plugin packages.

|project| plugin architecture
-----------------------------

Plugins in |project| are organized in packages, stored under :file:`plugins`. Packages are git repositories, which get pulled in their own subdirectory.

Adding a new package
--------------------

Adding a new package can either be done with the configure script, see :ref:`tutorial_configuration` or directly by hand in the :ref:`plugins section <additional_repositories>`.


Creating a package
------------------

The architecture of a package is :
    * :file:`root`, the root of repository
        * :file:`README.md` for documentation about the package
        * :file:`compilers` a directory containing information about specific compilers used for the plugins
            * :file:`compiler1.conf`, a compiler configuration file, see :ref:`compilers_plugin`
            * etc
        * :file:`conf`, a directory containing different configuration information
        * :file:`tests`, a directory containing tests for the package. see :ref:`testing_a_package`
        * :file:`plugin1.py`, a plugin. see :ref:`creating_a_plugin`
        * etc

However, nothing of this is mandatory, so you can just add the files and directory you need only.


.. _creating_a_plugin:

Creating a plugin
-----------------

There are three types of plugin in |project|:
    * :ref:`meta_plugin` that orchestrate the way one or more main plugin run
    * :ref:`main_plugin` that are run as the main event handler of the trigger script
    * :ref:`analysis_plugin`, that are run as an overlay over the main plugins
    * :ref:`installation_plugin`, that are run after the installation


There exist a base class for each of them in :file:`lib/plugins.py`.

Therefore, creating a plugin is as simple as implementing the required functions in a subclass of the desired plugin.

.. warning::
    Only one plugin should be created by file

.. warning::
    The plugin class should have the same name as the file (case does not matter)


.. _meta_plugin:

Meta Plugin
^^^^^^^^^^^

To create a MetaPlugin, implement :

.. autoclass:: lib.plugins.MetaPlugin
    :members: before_run, after_run

.. _main_plugin:

Main Plugin
^^^^^^^^^^^

To create a MainPlugin, implement :

.. autoclass:: lib.plugins.MainPlugin
    :members: extension, check_trigger_success

More call points are defined. For more information please see the source code.


.. _analysis_plugin:

Analysis Plugin
^^^^^^^^^^^^^^^

To create an analysis plugin, you might want to implement :

.. autoclass:: lib.plugins.AnalysisPlugin
    :members: options, pre_trigger_run, post_trigger_run

More call points are defined. For more information please see the source code.


.. _installation_plugin:

Installation Plugin
^^^^^^^^^^^^^^^^^^^

To create an installation plugin, implement :

.. autoclass:: lib.plugins.InstallPlugin
    :members: options, post_install_run

More call points are defined. For more information please see the source code.


.. _compilers_plugin:

Adding a specific compiler
--------------------------

|project| support the addition of new compilers, to allow, for instance, adding llvm passes to clang.

New compilers have to be added in package/compilers/compiler_name.conf.

The format for a compiler file is as follow:
    * [install] : the install section as for programs. For a complete overview of its options, please see :ref:`install_conf`. You will surely want to define :
        * name : your compiler name : must match the file name without extension
        * utility : defines whether or not this is a utility program. say ``True`` here
    * [env] : the environment section. Each key-value pair defined here will be added to the environment configuration before running the compilation. You will surely want to add :
        * CC : the C compiler to use (usually clang or gcc)
        * CXX : as CC but for C++
        * PATH : will be appended to the system path, to find your compiler first. The easiest is to define it as ${install:install_directory}/bin

And that's it. The configure.py will take care of downloading and installing your compiler automatically, so you don't have anything else to do.

.. warning::
    The name in the [install] section must match the file name


.. _testing_a_package:

Testing a package
-----------------

In order to have a reliable framework, tests are very important. |project| already offers multiple utility functions to speed up writing your tests for your packages.

.. warning::
    In order to be discoverable, all tests must be in package_name/tests/test_* files

.. warning::
    In order to be run, all tests must subclass one of the class shown below.

Testing a compiler
^^^^^^^^^^^^^^^^^^

|project| provides a convenience class to test new compilers. This means you only have to implement :

.. autoclass:: tests.lib.structures.Compiler
    :members: name, bitcode, package, plugins

.. note::
    It is a good practice to have two versions of these test : one with and one without bitcode, if someone wants one or the other.

Testing a plugin
^^^^^^^^^^^^^^^^

As for compilers, plugin also have a convenience class. This means you only have to implement :

.. autoclass:: tests.lib.structures.Plugin
    :members: package, name

.. note:: Don't forget to register your plugin in a Compiler.plugins list, in order to have it tested !
.. note:: a more specialized plugin for analysis is also available in tests.lib.structures.AnalysisPlugin
