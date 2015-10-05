#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This extends logging.Logger to add a verbose level and an automated setup for bugbase
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


import logging
import os
import sys

try:
    from rainbow_logging_handler import RainbowLoggingHandler as ConsoleHandler
except ImportError:
    from logging import StreamHandler as ConsoleHandler

from lib.parsers.configuration import get_global_conf


VERBOSE = 15


def logger_verbose(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    A logger function for a level between _NOTSET and DEBUG (VERBOSE_DEBUG)
    :param self: the instance object
    :param message: the message to log
    :param args: additional arguments
    :param kwargs: additional keyword arguments
    """
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, **kwargs)  # pylint: disable=protected-access


def logging_verbose(msg: str, *args, **kwargs) -> None:
    """
    Log a message with severity 'VERBOSE_DEBUG' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    :param msg: the message to log
    :param args: additional arguments
    :param kwargs: additional keyword arguments
    """
    if len(logging.root.handlers) == 0:
        logging.basicConfig()
    logging.root.verbose(msg, *args, **kwargs)


def setup_logging() -> None:
    """
    Sets up the logging module to have a verbose option and formats the Console handler and File handler
    """
    logging.addLevelName(VERBOSE, "VERBOSE")
    logging.Logger.verbose = logger_verbose
    logging.verbose = logging_verbose
    logging.VERBOSE = VERBOSE

    # define console handler
    console_handler = ConsoleHandler(sys.stderr)
    if hasattr(console_handler, "_column_color"):
        # noinspection PyProtectedMember
        # pylint: disable=protected-access
        console_handler._column_color['%(message)s'][logging.VERBOSE] = ('cyan', None, False)

    console_formatter = logging.Formatter("[%(asctime)s] %(levelname)s : %(message)s", "%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.VERBOSE)

    # define file handler
    if not os.path.exists(os.path.dirname(get_global_conf().getdir("install", "log_file"))):
        os.makedirs(os.path.dirname(get_global_conf().getdir("install", "log_file")))
    file_handler = logging.FileHandler(get_global_conf().getdir("install", "log_file"))

    # add handlers
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)

    logging.getLogger().setLevel(get_global_conf().getint("install", "log_level"))


def start_new_log_section(section_name: str, section_type: str) -> None:
    """
    Helper to separate two logging sessions in the log file
    :param section_name: the name of the section
    :param section_type: the type of the section
    """
    logging.debug("#"*120)
    section_specifier = "##{:^116}##".format("{} for {}".format(section_type.upper(), section_name.upper()))
    logging.debug(section_specifier)
    logging.debug("#"*120)
