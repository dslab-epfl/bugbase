#!/usr/bin/env python3
# coding=utf-8

"""
Structures to test in the Base package
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from lib.configuration.coredump import setup_coredumps, change_coredump_filter
from plugins.base.success import Success
from tests.lib.structures import Compiler, Plugin, AnalysisPlugin


class BaseStructure:
    """
    Structures belonging to the Base package
    """
    @property
    def package(self) -> str:
        """ The package name : base """
        return "base"


# noinspection PyAbstractClass
class SuccessPlugin(BaseStructure, Plugin):
    """
    The Success plugin
    """
    @property
    def name(self) -> str:
        """ the plugin name """
        return "success"


# noinspection PyAbstractClass
class FailPlugin(BaseStructure, Plugin):
    """
    The Fail plugin
    """
    @property
    def name(self) -> str:
        """ the plugin name """
        return "fail"

    def pre_run(self):
        """ Sets up coredumps options before the run """
        setup_coredumps()
        change_coredump_filter()


# noinspection PyAbstractClass
class RRPlugin(BaseStructure, Plugin):
    """
    The Success plugin
    """
    @property
    def name(self) -> str:
        """ the package name """
        return "rr"


class BenchmarkPlugin(BaseStructure, AnalysisPlugin):
    """
    The Benchmark plugin, running with success
    """
    @property
    def name(self) -> str:
        """ the package name """
        return "benchmark"

    @property
    def main_plugin(self):
        """ The main plugin with which to run """
        return Success

    @property
    def priority(self):
        """ Benchmarking is very slow. It must thus be run before the others in order to maximize efficiency """
        return 2


# noinspection PyAbstractClass
class GccCompilerWithoutWllvmTest(BaseStructure, Compiler):
    """
    Compiles without wllvm with gcc
    """

    @property
    def bitcode(self):
        """ We don't want bitcode to be created """
        return False

    @property
    def name(self):
        """ the compiler name to use: gcc """
        return "gcc"


# noinspection PyAbstractClass
class ClangCompilerWithoutWllvmTest(BaseStructure, Compiler):
    """
    Compiles without wllvm with clang
    """

    @property
    def bitcode(self) -> bool:
        """ We don't want bitcode to be created """
        return False

    @property
    def name(self) -> str:
        """ the compiler name to use: clang """
        return "clang"


# noinspection PyAbstractClass
class ClangCompilerWithWllvmAndPluginsTest(BaseStructure, Compiler):
    """
    Tests building everything with wllvm and clang. Also tests all plugins against these programs
    """
    plugins = [SuccessPlugin(), FailPlugin(), RRPlugin(), BenchmarkPlugin()]

    @property
    def bitcode(self) -> bool:
        """ We want bitcode to be created """
        return True

    @property
    def name(self) -> str:
        """ The compiler name to use: clang """
        return "clang"

    @property
    def priority(self) -> int:
        """
        This compiler uses the custom wllvm, which has to be installed. PLus plugins, which have to be configured.
        We thus diminish a bit its priority
        """
        return 7

