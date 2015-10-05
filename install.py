#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This scripts is a script to use to install and configure programs.
"""

import multiprocessing
import traceback
from argparse import ArgumentParser
import logging

from lib.exceptions import InstallationErrorException
from lib.helper import show_progress
from lib.parsers import arguments
from lib.parsers.configuration import get_global_conf, get_program_conf
from lib import constants, hooks
import lib.logger
from lib.installer import Installer


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


PROGRAMS_SOURCE_PATH = constants.ROOT_PATH + "/data/"
PROGRAMS = get_global_conf().getlist("install", "programs")


def parse_args() -> (list, bool):
    """
    Creates a parser for command lines attributes and parses them
    :return: the programs to install and Force
    """
    parser = ArgumentParser(
        description="An automated install script for our Benchmarks", parents=[arguments.get_verbosity_parser()]
    )
    parser.add_argument(
        "-f", "--force", help="Force reinstall if already installed", action="store_true", dest="force_installation"
    )
    parser.add_argument(
        "programs", nargs="+", type=str, help="the programs you want to install. Must be in : {} or all."
        .format(" ".join(PROGRAMS)))

    # pylint: disable=no-member
    parser.add_argument(
        "-p", "--processes", type=int, default=multiprocessing.cpu_count(),
        help="the number of process the script can use to build. Default : {}".format(multiprocessing.cpu_count())
    )

    hooks.register_for_install(parser=parser)

    args = parser.parse_args()

    logging.getLogger().setLevel(args.logging_level)

    _programs = args.programs
    if "all" in _programs:
        args.programs = PROGRAMS
    else:
        for _ in _programs:
            if _ not in PROGRAMS:
                parser.print_help()
                exit(1)

    return vars(args)


def main(programs, force_installation, processes, **kwargs):
    """
    the main function. runs installers
    :param programs: the programs to install
    :param force_installation: if the installation must be done if the program was already installed
    :param kwargs: additional parameters to pass to the plugins
    """
    # pylint: disable=no-member,too-few-public-methods
    class InstallerProcess(multiprocessing.Process):
        """
        An Installer for a list of programs.
        :param _programs: the list of programs to launch
        :param _report_queue: the queue where to report the return value
        :param _max_tasks: the semaphore to acquire at the end to release a new worker
        """
        def __init__(
                self, _programs: list, _report_queue: multiprocessing.Queue, _max_tasks: multiprocessing.Semaphore
        ):
            super().__init__()
            self.programs = _programs
            self.report_queue = _report_queue
            self.max_tasks = _max_tasks

        def run(self):
            """ Installs the programs and reports the value """
            error = None
            try:
                for _installer in self.programs:
                    try:
                        if (not _installer.run()) and _installer.conf.get("executable", None):
                            hooks.create_executables(installer=_installer)
                            hooks.post_install_run(installer=_installer, **kwargs)
                    except InstallationErrorException as exception:
                        logging.error(exception.error_message)
                        logging.error("Won't install %(program)s", dict(program=_installer.conf.get("name")))
                        error = constants.INSTALL_FAIL
            except Exception as exc:  # pylint: disable=broad-except
                error = constants.INSTALL_FAIL
                logging.error(exc)
                logging.debug("".join(traceback.format_tb(exc.__traceback__)))

            finally:
                logging.verbose("Cleaning environment")
                hooks.post_install_clean(**kwargs)
                self.max_tasks.release()
                self.report_queue.put((error or 0, self.programs[0].conf.get("name")))

    installers = []
    report_queue = multiprocessing.Queue()
    max_tasks = multiprocessing.Semaphore(processes)

    for program in programs:
        max_tasks.acquire()
        lib.logger.start_new_log_section(program, "installation")
        program_conf = get_program_conf(program)

        installer = InstallerProcess(
            [Installer.factory(program_conf[prog], force_installation) for prog in program_conf.sections()],
            report_queue,
            max_tasks
        )
        installer.start()
        installers.append(installer)

    return_value = 0
    counter = 0
    for _ in installers:
        counter += 1
        value, program = report_queue.get(block=True)
        if value:
            return_value = value
            logging.error("%(prog)s failed to compile correctly", dict(prog=program))

        show_progress(counter, len(installers))

    return return_value


if __name__ == "__main__":
    try:
        lib.logger.setup_logging()
        hooks.load_plugins()
        exit(main(**parse_args()))
    except KeyboardInterrupt:
        exit(1)
