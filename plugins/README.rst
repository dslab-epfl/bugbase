PLUGINS
=======

Plugin purposes
---------------

Plugins can be enabled or disabled via the configure script or in the custom.conf file.

They allow programmers to add more behaviors to the framework or to modify the behavior of different programs.

Only a short overview is given here. For more information, please build the complete documentation (see <https://github.com/dslab-epfl/bugbase/README.rst>`_.)


Creating a plugin
-----------------

Creating a plugin as been made the simplest possible:

    * create a ${plugin_name}.py file in the plugins directory
    * if needed add a ${plugin_name}.conf in the conf/plugins/ directory
    * create functions for each stage you want to execute
    * register your functions in a function called `initialize` in your plugin file by appending the function to be called to the correct moment from hooks.Registered
    * now enable your plugin and you are ready to go !
