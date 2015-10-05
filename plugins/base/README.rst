Base Package
============

This is Bugbase main package concerning plugins. It is shipped with Bugbase and offers basic plugins to be built on.

Currently provided plugins are :

    * :ref:`fail`
    * :ref:`success`
    * :ref:`rr`
    * :ref:`benchmark`
    * :ref:`overhead`


.. _fail:

fail
----

This plugin is used to trigger bugs in executables that have one defined. A run will be successful if the program fails the way it is intended to fail.

.. _success:

success
-------

This plugin makes a successful run for the given program. It can be used as a basic bloc for runs that have to be successful

.. _rr:

rr
--

This plugin makes successful runs using the RecordReplay tool from Mozilla

.. todo:: insert RR link


.. _benchmark:

benchmark
---------

This plugin allows for custom benchmarking. It is meant to be used with another plugin to direct the run.

It will give bigger workloads to the executed program and compute the time it needs to complete the tasks a given number of time for more accuracy

.. _overhead:

overhead
--------

This plugin builds upon benchmark and allows the comparison of multiple running time on multiple programs and can report the result as a graph
