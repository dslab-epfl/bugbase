#!/usr/bin/env python3
# coding=utf-8

"""
Different structures to easily represent tested data

This enable automated integration tests to take place easily, navigating through this data with automatic discovery
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from abc import abstractmethod, ABCMeta
import threading


class Compiler(metaclass=ABCMeta):  # pylint: disable=no-self-use
    """
    A basic representation of a compiler
    """
    plugins = []

    @property  # pragma nocover
    @abstractmethod
    def package(self) -> str:
        """ The package to which the compiler belongs """

    @property  # pragma nocover
    @abstractmethod
    def name(self) -> str:
        """ The name of the compiler """

    @property  # pragma nocover
    @abstractmethod
    def bitcode(self) -> bool:
        """ Whether or not to use bitcode with this compiler """

    @property
    def priority(self) -> int:
        """
        The compiler's priority. Compilers that can be installed by the package manager should be run first, as it
        will give more time for the compilation of the others, thus maximizing multiprocessing testing
        """
        return 5

    def __init__(self, event: threading.Event):
        self.is_configured = event


class Plugin(metaclass=ABCMeta):  # pylint: disable=no-self-use
    """
    A basic representation of a plugin
    """
    @property  # pragma nocover
    @abstractmethod
    def package(self) -> str:
        """ The package to which the package belongs"""

    @property  # pragma nocover
    @abstractmethod
    def name(self) -> str:
        """ The name of the plugin """

    def pre_run(self) -> str:
        """ Runs before the tests, if ever something is needed for them to work """

    @property
    def priority(self) -> int:
        """
        The priority of the plugin. Slower plugins should have higher priority in order to maximize tests efficiency
        """
        return 5


class AnalysisPlugin(Plugin, metaclass=ABCMeta):
    """
    A basic representation of an analysis plugin
    """
    @property  # pragma nocover
    @abstractmethod
    def main_plugin(self) -> object:
        """ The main plugin with which to run """


class Program:  # pylint: disable=too-few-public-methods
    """
    A basic representation of a package
    """
    def __init__(self, name: str, lock: threading.Lock, event: threading.Event):
        self.name = name
        self.lock = lock
        self.is_installed = event
