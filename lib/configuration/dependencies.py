#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Handle the installations of dependencies for the configuration of the repo
"""

from contextlib import suppress
from configparser import NoOptionError
import logging
import os
import sys

from lib.installer import dependency_installer, Installer
from lib import constants
from lib.helper import launch_and_log
from lib.parsers.configuration import get_global_conf, ProgramParser, get_program_conf, get_plugin_conf, \
    get_compiler_conf


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


def install_wllvm(force: bool) -> None:
    """
    Installs wllvm
    :param force: force installation if package is already installed
    """
    conf = ProgramParser()
    conf.read([os.path.join(constants.CONF_PATH, "utils/wllvm.conf")])
    Installer.factory(conf["WLLVM"], force).run()


def install_python_modules() -> None:
    """
    Install necessary python modules for the scripts and aesthetics

    :raise subprocess.CalledProcessError
    """
    logging.verbose("Installing python dependencies")
    requirements = os.path.join(constants.CONF_PATH, "requirements.pip")
    cmd = ["pip3", "install", "-r", requirements]
    # pylint: disable=no-member
    if (not (hasattr(sys, 'real_prefix') and sys.prefix != sys.real_prefix)) and (sys.prefix == sys.base_prefix):
        # we are not in a virtualenv. Let's install the packages as user
        cmd.insert(2, "--user")
    launch_and_log(cmd, error_msg="Could not install python module")


def get_programs_dependencies() -> list:
    """
    Collects all programs dependencies and returns them in a list
    :return: list of program dependencies
    """
    dependencies = []
    programs = get_global_conf().getlist("install", "programs")

    for program in programs:
        conf = get_program_conf(program)

        for section in conf.sections():
            with suppress(NoOptionError):
                dependencies += conf.getlist(section, "depend")

    for plugin in get_global_conf().getlist("plugins", "enabled_plugins"):
        conf = get_plugin_conf(*plugin.split("."))
        for section in conf.sections():
            with suppress(NoOptionError):
                dependencies += conf.getlist(section, "depend")

    return dependencies


def install(force: bool) -> None:
    """
    Install all the necessary above programs and modules

    :param force: force installation if package is already installed
    :raise subprocess.CalledProcessError on error
    """
    logging.info("Installing required programs and modules")
    packages_to_install = set(get_global_conf().getlist("install", "dependencies"))

    if get_global_conf().getboolean("install", "module_handling"):
        packages_to_install.add("python3-pip")  # pylint: disable=no-member

    compiler = get_global_conf().get("install", "compiler")
    compiler_conf = get_compiler_conf(*compiler.split("."))

    for section in compiler_conf.sections():
        if section in ["env", "install"]:
            continue

        packages_to_install.update(compiler_conf[section].getlist("depend", fallback=[]))

    packages_to_install.update(get_programs_dependencies())
    packages_to_install.update(compiler_conf.getlist("install", "depend", fallback=[]))

    dependency_installer.DependenciesInstaller.factory(list(packages_to_install)).run()

    Installer.factory(compiler_conf["install"], force).run()

    if get_global_conf().getboolean("install", "module_handling"):
        install_python_modules()

    if get_global_conf().getboolean("install", "llvm_bitcode"):
        install_wllvm(force)
