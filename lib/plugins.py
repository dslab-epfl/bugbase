#!/usr/bin/env python3
# coding=utf-8

"""
Multiple helper class for plugins creation. All plugins implemented are required to at least extend BasePlugin.
"""


# noinspection PyProtectedMember
from argparse import _SubParsersAction, ArgumentParser
from abc import abstractmethod, ABCMeta
import logging
import os
import shutil

from lib.installer import Installer
from lib.installer.context_managers import ExtensionPatcherManager
from lib.parsers.configuration import get_global_conf
from lib.trigger import RawTrigger


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class BasePlugin(metaclass=ABCMeta):
    """
    The base plugin architecture. Used for plugin discovery and calls.
    """
    help = None

    def configure(self, *args, **kwargs) -> None:
        """
        Function called on configure, after the base is done

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass

    @classmethod
    def register_for_install(cls, *args, **kwargs) -> None:
        """
        Function called before parsing arguments for install, used to enable a plugin for installation

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass

    @classmethod
    def register_for_trigger(cls, parser, subparser, *args, **kwargs) -> None:
        """
        Function called before parsing arguments for trigger, used to enable a plugin when triggering

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass

    def pre_trigger_run(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Function called before running the trigger.

        :param trigger: the trigger instance to run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass

    def post_trigger_run(self, trigger: RawTrigger, error: int, *args, **kwargs) -> None:
        """
        Function called after the trigger ran successfully running the trigger.

        :param trigger: the trigger that has run
        :param error: the error code returned by the trigger
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass

    def post_trigger_clean(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Function called before the trigger exits. This is always run, whatever happens.

        :param trigger: the trigger that has run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass


class MainPlugin(BasePlugin, metaclass=ABCMeta):
    """
    Implements the minimum for a main plugin for trigger runs. For a plugin to be used in this case, it must inherit
    this one
    """
    @property
    @abstractmethod
    def extension(self) -> str:
        """
        The extension to identify this plugin. Will be appended if needed on the plugin-specific binary
        """

    @classmethod
    def register_for_trigger(cls, subparser: _SubParsersAction, *args, **kwargs) -> ArgumentParser:
        """
        Registers the plugin as an option to run with for trigger

        :param subparser: the subparser on which to register
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: the parser created by registering, to allow subclasses to register options when running
        """
        parser = subparser.add_parser(cls.__name__.lower(), help=cls.help)
        parser.set_defaults(main_plugin=cls())  # pylint: disable=abstract-class-instantiated
        return parser

    @abstractmethod
    def check_trigger_success(self, trigger: RawTrigger, error: int, *args, **kwargs) -> int:
        """
        Main plugins are responsible of determining if the run was successful or not. This function gets called to do
        this

        :param trigger: the trigger that has run
        :param error: the error code returned by the trigger
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|constants.PLUGIN_ERROR on success|error
        """

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    def create_executable(self, installer: Installer, extension: str=None, version_number: int=None, force: bool=False,
                          *args, **kwargs) -> int:
        """
        Creates a special executable to run for this plugin if needed. If a patch is supplied by the form
        "program-name-version-extension.patch", it will automatically get used to create a new version

        :param installer: the installer instance that is used
        :param extension: the extension to add to the binary, usually the plugin name
        :param version_number: if multiple version are required for a plugin, this will get appended to it
        :param force: force creation even if no patch is provided
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: None|0 if nothing happened or installation is successful
        """
        extension = extension or self.extension
        executable_suffix = "{}-{}".format(extension, version_number) if version_number else extension

        for lib in installer.conf.getlist("libraries"):
            lib_installer = Installer.factory(installer.conf.get_library(lib), False)
            with ExtensionPatcherManager(lib_installer, extension) as lib_patcher:
                if lib_patcher.is_patched or force:
                    lib_installer.configure()
                    lib_installer.make()
                    lib_installer.install()
                    force = True

        with ExtensionPatcherManager(installer, extension) as patcher:
            if not patcher.is_patched and not force:
                logging.verbose("No need to create special executable for {}".format(extension))
                return

            installer.make()
            executable = os.path.join(installer.working_dir, installer.conf.get("bitcode_file"))
            destination = "{}-{}".format(installer.conf.get_executable(), executable_suffix)
            logging.verbose("Copying {} to {}".format(executable, os.path.join(installer.install_dir, destination)))
            shutil.copy(executable, os.path.join(installer.install_dir, destination))

        for lib in installer.conf.getlist("libraries"):
            lib_installer = Installer.factory(installer.conf.get_library(lib), False)
            if force:
                lib_installer.configure()
                lib_installer.make()
                lib_installer.install()

        return 0


class AnalysisPlugin(BasePlugin, metaclass=ABCMeta):
    """
    Implements available actions for an analysis plugin. That is a plugin that runs on top of a main plugin to provide
    more functionality, analysis, benchmarking and so on
    """
    @classmethod
    @abstractmethod
    def options(cls) -> list:
        """
        A list of dashed options to use for enabling this plugin. Beware of conflicts with others

        :return: the options to enable the plugin
        """

    @classmethod
    def register_for_trigger(cls, parser: ArgumentParser, *args, **kwargs) -> None:
        """
        Registers the plugin as being available to run with the trigger

        :param parser: the parser on which to register
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        parser.add_argument(*cls.options(), action="append_const", dest="analysis_plugins", const=cls, help=cls.help)


class InstallPlugin(BasePlugin, metaclass=ABCMeta):
    """
    Implements available actions to a plugin that is meant to run after an installation, for example to do one time
    analysis on the binaries
    """
    @classmethod
    @abstractmethod
    def options(cls) -> list:
        """
        A list of dashed options to use for enabling this plugin
        """

    @abstractmethod
    def post_install_run(self, *args, **kwargs) -> None:
        """
        Called once the binary was compiled, main entry point for this type of plugins

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """

    @classmethod
    def register_for_install(cls, parser: ArgumentParser, *args, **kwargs) -> None:
        """
        Registers the plugin as being available to run after installation

        :param parser: the parser on which to register
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        parser.add_argument(*cls.options(), action="append_const", dest="analysis_plugins", const=cls, help=cls.help)

    @staticmethod
    def post_install_clean(*args, **kwargs) -> None:
        """
        Called after installation is done.

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        pass


class MetaPlugin(BasePlugin, metaclass=ABCMeta):
    """
    Implements available actions to a plugin that is meant to orchestrate the run, for example choose other plugins to
    run and take actions afterwards (such as comparing two different implementations for speed and so on)
    """
    @classmethod
    def register_for_trigger(cls, subparser: _SubParsersAction, *args, **kwargs):
        """
        Registers the plugin as an option to run for the trigger

        :param subparser: the subparser on which to register
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return the parser created by registering, to allow subclasses to register options when running
        """
        parser = subparser.add_parser(cls.__name__.lower(), help=cls.help)
        parser.set_defaults(main_plugin=cls())  # pylint: disable=abstract-class-instantiated
        return parser

    @abstractmethod
    def before_run(self, *args, **kwargs) -> dict:
        """
        Called once before the complete run. Should return a dictionary of the form:
            dict = {
                "main_plugins": list of MainPlugins to run
                "analysis_plugins": list of analysis plugins to use
            }

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: list of MainPlugin
        """
        pass

    @abstractmethod
    def after_run(self, *args, **kwargs) -> int:
        """
        Called once all plugins have run.

        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0 | Positive Integer on success | failure
        """
        pass


def create_big_file(size: int=1) -> str:
    """
    Used to create a very big file to use for some processing

    :param size: the number of times to duplicate the file, increasing its size
    :return: the file path
    """
    return_file = os.path.join(get_global_conf().getdir("trigger", "workloads"), "{}-{}.tar".format("workloads", size))
    if os.path.exists(return_file):
        return return_file

    os.makedirs(os.path.dirname(return_file), exist_ok=True)

    with open(return_file, "w") as big_file:
        for _ in range(size):
            big_file.write("0" * (1024 ** 2))

    return return_file
