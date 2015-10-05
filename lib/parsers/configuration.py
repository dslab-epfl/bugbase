#!/usr/bin/env python3
# coding=utf-8

"""
Various helpers built around the ConfigurationParser class
"""

__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


import os
import re
# noinspection PyProtectedMember
from configparser import ConfigParser, _UNSET, NoOptionError, NoSectionError, ExtendedInterpolation, SectionProxy

from lib import constants


CONF_FILES = [constants.ROOT_PATH + "/conf/default.conf", constants.ROOT_PATH + "/conf/custom.conf"]
GLOBAL_CONF = None


# noinspection PyShadowingBuiltins
# pylint: disable=redefined-builtin
def getlist(self, option: str, fallback: list=None, *, raw: bool=False, vars: dict=None) -> list:
    """
    Converts a SectionProxy cvs option to a list
    :param option: the option to get
    :param fallback: default value, if option does not exist
    :param raw: True to disable interpolation
    :param vars: additional substitutions
    :return: a list corresponding to the option
    """
    # pylint: disable=protected-access
    return self._parser.getlist(self._name, option, raw=raw, vars=vars, fallback=fallback)


# noinspection PyShadowingBuiltins
def getdir(self, option: str, fallback: str="", *, raw: bool=False, vars: dict=None) -> str:
    """
    Converts a SectionProxy cvs option to a directory
    :param option: the option to get
    :param fallback: default value if option does not exist
    :param raw: True to disable interpolation
    :param vars: additional substitutions
    :return: a sanitized string corresponding to the directory
    """
    return self._parser.getdir(self._name, option, raw=raw, vars=vars, fallback=fallback)


def get_core_path(self) -> str:
    """
    Gets the coredump location for the program
    :return: the absolute path to the expected coredump
    """
    return self._parser.get_core_path(self._name)


def get_executable(self) -> str:
    """
    Gets the executable for the SectionProxy
    :return: str to the executable
    """
    return self._parser.get_executable(self._name)


def get_library(self, lib: str) -> SectionProxy:
    """
    Returns the SectionProxy representing the library
    :param lib: string representing the library name
    :return: SectionProxy for the library
    """
    return self._parser.get_library(self._name, lib)

# Registers functions to the SectionProxy
SectionProxy.getlist = getlist
SectionProxy.get_core_path = get_core_path
SectionProxy.getdir = getdir
SectionProxy.get_executable = get_executable
SectionProxy.get_library = get_library


# noinspection PyShadowingBuiltins,PyShadowingBuiltins
class TypedConfigParser(ConfigParser):  # pylint: disable=too-many-ancestors
    """
    A list-aware Configuration parser
    """
    LIST_SEPARATOR = ","

    @staticmethod
    def _convert_to_list(value: str) -> list:
        """
        Converts a vcs string to a list
        :param value: string to convert
        :return: the corresponding list
        """
        return [item for item in re.split(r"{}\s*".format(TypedConfigParser.LIST_SEPARATOR), value) if item != ""]

    @staticmethod
    def _convert_to_dir(value: str) -> str:
        """
        Sanitizes the string given to expand users and vars for a directory
        :param value: un-sanitized string representing the directory
        :return: str : the sanitized string
        """
        return os.path.expanduser(os.path.expandvars(value))

    def getlist(self, section: str, option, *, raw: bool=False, vars=None, fallback=_UNSET) -> list:
        """
        Return a list value for the named option in the named section
        :param section: the section to search
        :param option: the wanted option
        :param raw: if True, will not interpolate values
        :param vars: additional substitutions
        :param fallback: fallback value
        :return: the given option as a list
        """
        try:
            return self._get(section, self._convert_to_list, option, raw=raw, vars=vars)
        except (NoSectionError, NoOptionError):
            if fallback is _UNSET:
                raise
            else:
                return fallback

    def getdir(self, section: str, option, *, raw: bool=False, vars=None, fallback=_UNSET) -> str:
        """
        Return a directory value for the named option in the named section
        :param section: the section to search
        :param option: the wanted option
        :param raw: if True, will not interpolate values
        :param vars: additional substitutions
        :param fallback: fallback value
        :return: the given option as a sanitized dir
        """
        try:
            return self._get(section, self._convert_to_dir, option, raw=raw, vars=vars)
        except (NoSectionError, NoOptionError):
            if fallback is _UNSET:
                raise
            else:
                return fallback


class ProgramParser(TypedConfigParser):  # pylint: disable=too-many-ancestors
    """
    A bugbase specific program configuration parser
    """
    def __init__(self, defaults=None) -> None:
        """
        Always use extended interpolation
        """
        super().__init__(defaults=defaults, interpolation=ExtendedInterpolation())

    def read(self, file_names: list, encoding: str=None) -> None:
        """
        Reads the configuration file normally, adding a default installation configuration beforehand, to specify
         default values then transforms relative paths to absolute paths
        :param file_names: the configuration files
        :param encoding: the configuration files encoding
        """
        file_names.append(os.path.join(constants.CONF_PATH, "install.conf"))
        super().read(file_names, encoding)

        for section in self.sections():
            if self.has_option(section, "install_directory"):
                if self.getboolean(section, "system_package", fallback=False):
                    self.set(section, "install_directory", "/usr")
                    continue
                elif self.getboolean(section, "utility", fallback=False):
                    install_dir = GLOBAL_CONF.get("utilities", "install_directory")
                else:
                    install_dir = GLOBAL_CONF.get("install", "install_directory")
                self.set(
                    section, "install_directory",
                    os.path.expanduser(os.path.expandvars(
                        os.path.join(install_dir, self.get(section, "install_directory").lstrip("/"))))
                )

    def get_core_path(self, section: str) -> str:
        """
        Search for the coredump name in the section, and if found, builds the full path to it
        :param section: the section in which to search
        :return: the full path to the coredump
        :raise NoOptionError if coredump is not a registered option
        """
        core_name = self.get(section, "executable")
        if not core_name:
            raise NoOptionError
        core_pattern = get_global_conf().get("trigger", "core_dump_pattern")
        core_location = get_global_conf().getdir("trigger", "core_dump_location")

        # pylint: disable=no-member
        core_pattern = core_pattern.replace("%E", self.get_executable(section).replace("/", "!"))
        core_pattern = core_pattern.replace("%e", core_name)

        return os.path.join(core_location, core_pattern)

    def get_executable(self, section: str) -> str:
        """
        Returns the executable path of the program
        :param section: the section representing the program
        :return: the full path to the executable
        :raise NoOptionError if coredump is not a registered option
        """
        return os.path.join(
            self.getdir(section, "install_directory"),
            self.get(section, "executable_directory"),
            self.get(section, "executable").lstrip("/")
        )

    def get_library(self, section: str, library: str) -> SectionProxy:
        """
        Returns a SectionProxy configuration for the given library of the program
        :param section: the section representing the program
        :param library: the library name
        :return: a SectionProxy containing the library configuration
        :raise NoOptionError if no such library exists
        """
        if library in self.get(section, "libraries") and library in self.sections():
            return self[library]
        raise NoOptionError


class CompilerParser(TypedConfigParser):  # pylint: disable=too-many-ancestors
    """
    A bugbase specific program configuration parser
    """
    def __init__(self, defaults=None) -> None:
        """
        Always use extended interpolation
        """
        super().__init__(defaults=defaults, interpolation=ExtendedInterpolation())

    def read(self, file_names: list, encoding: str=None) -> None:
        """
        Reads the configuration file normally, adding a default installation configuration beforehand, to specify
         default values then transforms relative paths to absolute paths
        :param file_names: the configuration files
        :param encoding: the configuration files encoding
        """
        file_names.append(os.path.join(constants.CONF_PATH, "install.conf"))
        super().read(file_names, encoding)

        for section in self.sections():
            if section == "env":
                continue

            for option in self.items(section):
                section_dict = self._unify_values(section, None)
                raw_option = self.optionxform(option[0])
                value = section_dict[raw_option]
                self.set(section, option[0], value)

        self.defaults().clear()
        for section in self.sections():
            if self.has_option(section, "install_directory"):
                if self.getboolean(section, "system_package", fallback=False):
                    self.set(section, "install_directory", "/usr")
                    continue
                elif self.getboolean(section, "utility", fallback=False):
                    install_dir = GLOBAL_CONF.get("utilities", "install_directory")
                else:
                    install_dir = GLOBAL_CONF.get("install", "install_directory")
                self.set(
                    section, "install_directory",
                    os.path.expanduser(os.path.expandvars(
                        os.path.join(install_dir, self.get(section, "install_directory").lstrip("/"))))
                )


def get_global_conf() -> TypedConfigParser:
    """
    If the global configuration was not loaded, loads it and return the global configuration
    :return: the scripts configuration
    """
    global GLOBAL_CONF  # pylint: disable=global-statement
    if GLOBAL_CONF is None:
        GLOBAL_CONF = TypedConfigParser(interpolation=ExtendedInterpolation())
        GLOBAL_CONF.read(CONF_FILES)
    return GLOBAL_CONF


def reload_global_conf() -> TypedConfigParser:
    """
    Reloads the global configuration and returns the new one
    :return: the scripts configuration
    """
    global GLOBAL_CONF  # pylint: disable=global-statement
    if GLOBAL_CONF:
        GLOBAL_CONF = None
    return get_global_conf()


def get_program_conf(name: str) -> ProgramParser:
    """
    Gets the configuration for the named program
    :param name: program to fetch
    :return: the program configuration parser
    """
    path = os.path.join(constants.PROGRAMS_SOURCE_PATH, name, "install.conf")
    config_parser = ProgramParser()
    config_parser.read([path])
    return config_parser


def get_compiler_conf(package: str, name: str) -> CompilerParser:
    """
    Gets the configuration for the named compiler
    :param package: the package to which the compiler belongs
    :param name: the compiler name
    :return: the configuration for the compiler
    """
    path = os.path.join(constants.ROOT_PATH, "plugins", package, "compilers", "{}.conf".format(name))
    config_parser = CompilerParser()
    config_parser.read([path])
    return config_parser


def get_plugin_conf(package: str, name: str) -> ProgramParser:
    """
    Gets the configuration for the named plugin
    :param package: the package to which the plugin belongs
    :param name: the name of the plugin
    :return: the program configuration parser
    """
    path = os.path.join(constants.ROOT_PATH, "plugins", package, "conf", "{}.conf".format(name))
    config_parser = ProgramParser()
    config_parser.read([path])
    return config_parser


def get_trigger_conf(name: str) -> SectionProxy:
    """
    Gets the configuration for the trigger
    :param name: the trigger to get
    :return: a proxy containing all available information
    """
    config_parser = get_program_conf(name)
    for section in config_parser.sections():
        if config_parser.has_option(section, "executable"):
            return config_parser[section]
    raise NoOptionError
