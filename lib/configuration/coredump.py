#!/usr/bin/env python3
# coding=utf-8

"""
A module to handle the update for handling coredumps system wide
"""

import logging
import os
import subprocess

from lib.helper import launch_and_log_as_root
from lib.parsers.configuration import get_global_conf


__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


def create_coredump_directory() -> None:
    """
    Creates the coredump directory and gives access to anybody
    """
    logging.debug("Creating the coredump storage directory")
    core_dump_location = get_global_conf().get("trigger", "core_dump_location")

    os.makedirs(core_dump_location, exist_ok=True)

    os.chmod(core_dump_location, 0o777)


def change_coredump_pattern() -> None:
    """
    Changes the coredump pattern system wide
    """
    core_dump_location = get_global_conf().get("trigger", "core_dump_location")
    core_dump = os.path.join(core_dump_location, get_global_conf().get("trigger", "core_dump_pattern"))

    last = False
    with open("/etc/sysctl.conf") as _file:
        for _line in _file:
            if core_dump in _line and ("#" not in _line or _line.index("#") > _line.index(core_dump)):
                last = True
            elif "kernel.core_pattern" in _line and\
                    ("#" not in _line or _line.index("#") > _line.index("kernel.core_pattern")):
                last = False

    if last:
        return

    command = ["echo", '"kernel.core_pattern={}"'.format(core_dump), ">>", "/etc/sysctl.conf"]
    try:
        launch_and_log_as_root(command)
        launch_and_log_as_root(["sysctl", "-p"])
    except subprocess.CalledProcessError:
        logging.warning("Please add 'kernel.core_pattern=%(pattern)s' to /etc/sysctl.conf", dict(pattern=core_dump))
        raise


def change_coredump_filter() -> None:
    """
    Changes the coredump filter for the process and its children
    """
    logging.debug("Changing coredump filter")
    coredump_filter = get_global_conf().get("trigger", "core_dump_filter")

    with open("/proc/{}/coredump_filter".format(os.getpid()), "w") as core_file:
        core_file.write(coredump_filter)


def setup_coredumps() -> None:
    """
    Updates all the coredumps settings at once
    """
    logging.info("Updating coredumps information")
    create_coredump_directory()
    change_coredump_filter()
    change_coredump_pattern()
