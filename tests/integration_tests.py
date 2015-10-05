#!/usr/bin/env python3
# coding=utf-8

"""
Integration tests for the complete framework

This file automatically discovers all Compiler subclasses in 'plugins/${package}/tests/*' and runs all programs
against them and their declared plugins concurrently.
"""

from contextlib import suppress
import importlib
import logging
import multiprocessing
import os
import shutil
import time
import unittest

from install import main
from lib import get_subclasses
from lib.configuration import dependencies
from lib.constants import PLUGINS_PATH, ROOT_PATH
from lib.exceptions import ProgramNotInstalledException
from lib.logger import setup_logging
from lib.parsers.configuration import get_global_conf, get_trigger_conf
from lib.plugins import BasePlugin
import run
from tests import TEST_DIRECTORY, SAVE_DIRECTORY
from tests.lib.structures import Compiler, Program, Plugin


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


# prepare a manager for synchronization
RESOURCES_MANAGER = multiprocessing.Manager()  # pylint: disable=no-member


def bound_value(value: int, minimum: int=0, maximum: int=9) -> int:
    """
    Bounds a value between an upper and lower bound

    :param value: the value to bound
    :param minimum: the minimal allowed value
    :param maximum: the maximal allowed value
    :return: the bounded value
    """
    return minimum if value < minimum else maximum if value > maximum else value


class TestRunner(unittest.TestCase):
    """
    The Test runner, containing all integration tests, numbered
    """
    log_directory = os.path.join(get_global_conf().getdir("trigger", "default_directory"), "tests-results", "logs")
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls) -> None:
        """
        The class setup, ensures the log directory is ready
        """
        # pylint: disable=no-member
        get_global_conf().set("install", "make_args", "-j,-l{}".format(multiprocessing.cpu_count()))
        setup_logging()

    class EnvManager:  # pylint: disable=too-few-public-methods
        """
        An environment manager for the runs. Saves automatically logs of failing runs
        """
        def __init__(self, _compiler_: Compiler, file_suffix: str):
            self.compiler = _compiler_
            self.filename = "{}-{}-{}-{}.txt".format(
                _compiler_.package, _compiler_.name, "{}wllvm".format("" if _compiler_.bitcode else "no-"), file_suffix
            )

        def __enter__(self):
            logging.getLogger().setLevel(0)
            wllvm = "wllvm" if self.compiler.bitcode else "no-wllvm"
            get_global_conf().set("install", "compiler", "{}.{}".format(self.compiler.package, self.compiler.name))
            get_global_conf().set("install", "llvm_bitcode", str(self.compiler.bitcode))
            get_global_conf()["DEFAULT"]["default_directory"] = \
                os.path.join(TEST_DIRECTORY, self.compiler.package, self.compiler.name, wllvm)
            get_global_conf().set("install", "source_directory", os.path.join(ROOT_PATH, "src"))

            handlers = logging.getLogger().handlers
            while len(handlers) > 0:
                handlers[0].close()
                logging.getLogger().removeHandler(handlers[0])

            logging.getLogger().addHandler(logging.FileHandler(os.path.join(TestRunner.log_directory, self.filename)))

            get_global_conf().set(
                "plugins",
                "enabled_plugins",
                ",".join(["{}.{}".format(plugin.package, plugin.name) for plugin in self.compiler.plugins])
            )
            for plugin in self.compiler.plugins:
                importlib.import_module("plugins.{}.{}".format(plugin.package, plugin.name))

        # noinspection PyUnusedLocal
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:  # pragma nocover as this is only on fail and our tests should not fail
                shutil.move(
                    os.path.join(TestRunner.log_directory, self.filename),
                    os.path.join(SAVE_DIRECTORY, self.filename)
                )  # pragma nocover idem

    def configure(self, compiler: Compiler) -> None:
        """
        Configures the environment to run with the given compiler

        :param compiler: the compiler to use
        """
        try:
            with TestRunner.EnvManager(compiler, "configure"):
                self.assertFalse(
                    dependencies.install(False), "Could not install dependencies for {} with{} bitcode".format(
                        compiler.name, "out" if compiler.bitcode else ""
                    )
                )

            for plugin_info in compiler.plugins:
                log_file = "{}-{}-configuration".format(plugin_info.package, plugin_info.name)
                with TestRunner.EnvManager(compiler, log_file):
                    plugin = [
                        subclass for subclass in get_subclasses(BasePlugin)
                        if subclass.__name__.lower() == plugin_info.name
                    ][0]
                    self.assertFalse(plugin().configure(force=False))
        finally:
            compiler.is_configured.set()

    def compile(self, _compiler_: Compiler, _program_: Program) -> None:
        """
        Compiles and installs the given program with the given compiler

        :param _compiler_: the compiler to use
        :param _program_: the program to compile
        """
        _compiler_.is_configured.wait()
        try:
            with TestRunner.EnvManager(_compiler_, _program_.name):
                error = main([_program_.name], True, 1)
                self.assertFalse(error, "The program {} failed to compile with {}".format(
                    _program_.name, get_global_conf().get("install", "compiler")))

                # Checks that bitcode was indeed created at the correct place
                if _compiler_.bitcode:
                    conf = get_trigger_conf(_program_.name)
                    self.assertTrue(os.path.exists(conf.get_executable() + ".bc"))
        finally:
            _program_.is_installed.set()

    def run_main_plugin(self, _compiler_: Compiler, _plugin_: Plugin, _program_: Program):
        """
        Runs the given plugin against the given program

        :param _compiler_: the compiler used to compile the program
        :param _plugin_: the plugin to test
        :param _program_: the program to test
        """
        _program_.is_installed.wait()

        with _program_.lock, TestRunner.EnvManager(_compiler_, "{}-{}".format(_plugin_.name, _program_.name)):
            plugin = [
                subclass for subclass in get_subclasses(BasePlugin)
                if subclass.__name__.lower() == _plugin_.name
            ][0]
            if hasattr(_plugin_, "main_plugin"):
                analysis_plugins = [plugin]
                plugin = _plugin_.main_plugin
            else:
                analysis_plugins = []

            _plugin_.pre_run()
            # noinspection PyBroadException
            try:
                self.assertFalse(run.trigger_bug(_program_.name, plugin(), analysis_plugins=analysis_plugins))
            except ProgramNotInstalledException:
                raise unittest.SkipTest("{} is not installed".format(_program_.name))
            except Exception:  # with concurrency, tests might fail. Let's retry once
                time.sleep(2)  # let's sleep a bit before, timing might be bad
                self.assertFalse(run.trigger_bug(_program_.name, plugin(), analysis_plugins=analysis_plugins))
            time.sleep(2)


def load_compilers() -> None:
    """
    Imports all tests in the plugins/packages directory, to allow for Compiler instance discoveries
    """
    for package in os.listdir(PLUGINS_PATH):
        if os.path.isdir(os.path.join(PLUGINS_PATH, package)) and package != "__pycache__":
            for test_file in os.listdir(os.path.join(PLUGINS_PATH, package, "tests")):
                importlib.import_module("plugins.{}.tests.{}".format(package, os.path.splitext(test_file)[0]))


def add_plugin_run(_compiler_: Compiler, _program_: Program, plugin: Plugin) -> None:
    """
    Adds a plugin to run against the given program
    :param _compiler_:
    :param _program_:
    :param plugin:
    :return:
    """
    function_name = "test_9{}_{}_{}".format(bound_value(plugin.priority), plugin.name, _program_.name)
    setattr(
        TestRunner,
        function_name,
        lambda x, comp=_compiler_, prog=_program_, plug=plugin: TestRunner.run_main_plugin(x, comp, plug, prog)
    )
    setattr(getattr(TestRunner, function_name), "__name__", function_name)


def add_programs_compile(compiler: Compiler) -> None:
    """
    For all programs, add them to the compiler run list and register a plugin call for them

    :param compiler: the compiler to use
    """
    for program_name in get_global_conf().getlist("install", "programs"):
        program = Program(program_name, RESOURCES_MANAGER.Lock(), RESOURCES_MANAGER.Event())
        function_name = "test_5{}_{}_{}_{}wllvm_{}".format(
            bound_value(compiler.priority),
            compiler.package,
            compiler.name,
            "no-" if not compiler.bitcode else "",
            program.name
        )
        setattr(
            TestRunner,
            function_name,
            lambda x, comp=compiler, prog=program: TestRunner.compile(x, comp, prog)
        )
        setattr(getattr(TestRunner, function_name), "__name__", function_name)

        for plugin in compiler.plugins:
            add_plugin_run(compiler, program, plugin)


def add_compilers(_compilers_: list) -> None:
    """
    For all compiler in _compilers_, add a configure script for them and register all programs for them

    :param _compilers_: the list of compilers to use
    """
    for compiler_class in _compilers_:
        compiler = compiler_class(RESOURCES_MANAGER.Event())
        function_name = \
            "test_1{}_{}_{}_{}wllvm".format(
                bound_value(compiler.priority),
                compiler.package,
                compiler.name,
                "no-" if not compiler.bitcode else ""
            )
        setattr(TestRunner, function_name, lambda x, comp=compiler: TestRunner.configure(x, comp))
        setattr(getattr(TestRunner, function_name), "__name__", function_name)

        add_programs_compile(compiler)


def clean_working_directory() -> None:
    """ Removes old logs before running """
    with suppress(FileNotFoundError):
        shutil.rmtree(TestRunner.log_directory)
    with suppress(FileNotFoundError):
        shutil.rmtree(SAVE_DIRECTORY)

    os.makedirs(TestRunner.log_directory)
    os.makedirs(SAVE_DIRECTORY)


# Add all functions to TestRunner on initialization
clean_working_directory()
load_compilers()
COMPILERS = get_subclasses(Compiler)
add_compilers(COMPILERS)
