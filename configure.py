#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This is an automated way to configure the working environment when working with bugbase
"""

from argparse import ArgumentParser
import logging

from lib import hooks, logger, exceptions
from lib.parsers import arguments
from lib.configuration.coredump import setup_coredumps
from lib.configuration.dependencies import install
from lib.configuration import update


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


def parse_args() -> tuple:
    """
    Creates a parser for command lines attributes and parses them
    :return: True if the program is to run interactively
    """
    parser = ArgumentParser(
        description="An automated configure script for Bugbase usage", parents=[arguments.get_verbosity_parser()]
    )
    parser.add_argument(
        "--default", help="use default values and don't ask anything (non-interactive mode)",
        action="store_false", dest="interactive"
    )
    parser.add_argument(
        "-f", "--force", help="Force reinstall of all programs if used",
        action="store_true", dest="force"
    )

    args = parser.parse_args()

    logging.getLogger().setLevel(args.logging_level)

    return args.interactive, args.force


def main(__interactive__: bool, force: bool) -> None:
    """
    Updates the configuration if the program is to be run interactively,
    then install necessary items
    :param __interactive__: if the config has to be updated
    :param force: True to force reinstall of the programs, else will only install the ones that are not installed
    """
    if __interactive__ and update.update():
        logging.error("An error occurred, could not finish configuration")
        return 1

    try:
        install(force)
        setup_coredumps()

        hooks.load_plugins()
        hooks.configure(force)
    except (exceptions.InstallationErrorException, exceptions.DistributionNotSupportedException) as exception:
        logging.error(exception)
        logging.error("Configure script failed. Please rerun it after correcting errors. You can add --default in order"
                      " to skip questions")
        return 1

    finally:
        logging.verbose("Cleaning environment")


if __name__ == "__main__":
    try:
        logger.setup_logging()
        exit(main(*parse_args()))
    except KeyboardInterrupt:
        exit(1)
