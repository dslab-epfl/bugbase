#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Contains helper exceptions for bugbase framework
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class DistributionNotSupportedException(Exception):
    """
    Exception raised when a distribution is not supported by the program
    """
    def __init__(self, distribution: str="This distribution"):  # pylint: disable=super-init-not-called
        self.distribution = distribution

    def __str__(self):
        return "{} is not supported yet. Please ask the developer for support".format(self.distribution)


class InstallationErrorException(Exception):
    """
    Exception raised when an installation failed
    """
    def __init__(self, error_message: str):  # pylint: disable=super-init-not-called
        self.error_message = error_message

    def __str__(self):
        return "Installation Error : {}".format(self.error_message)


class ProgramTriggerFailedException(Exception):
    """
    Exception raised when a trigger failed
    """
    def __init__(self, error_message):  # pylint: disable=super-init-not-called
        self.error_message = error_message

    def __str__(self):
        return "Trigger Error : {}".format(self.error_message)


class ProgramNotInstalledException(Exception):
    """
    Exception raised when a not installed program tries to get accessed
    """
    def __init__(self, program_name: str):  # pylint: disable=super-init-not-called
        self.program_name = program_name

    def __str__(self):
        return "{} is not installed !".format(self.program_name)


class MissingDependency(Exception):
    """
    Exception raised when a plugin needs more dependencies (for instance optional dependencies)
    """
    def __init__(self, missing_dependency, python_module=False):  # pylint: disable=super-init-not-called
        self.missing = missing_dependency
        self.python_module = python_module

    def __str__(self):
        if self.python_module:
            return \
                "{dependencies} is missing, please install it by running `pip3 install {dependencies}`\
                 or via your system package manager".format(dependencies=self.missing)
        else:
            return "{dependencies} is missing, please install it through your system package manager".format(
                dependencies=self.missing
            )


class PluginIncompatibleException(Exception):
    """
    Exception raised when a program is not compatible with a plugin
    """
    def __init__(self, msg):  # pylint: disable=super-init-not-called
        self.msg = msg

    def __str__(self):
        return self.msg
