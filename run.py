#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This is the main program for bugbase, allowing to run programs against a set of plugins
"""


import importlib
import logging
import os
import sys

from lib.configuration.coredump import change_coredump_filter
from lib.exceptions import ProgramNotInstalledException, PluginIncompatibleException
from lib.constants import PROGRAM_ARGUMENT_ERROR
from lib.hooks import load_plugins, register_for_trigger, pre_trigger_run, check_trigger_success, post_trigger_run, \
    post_trigger_clean, before_run, after_run
from lib.plugins import MainPlugin, MetaPlugin
from lib.parsers.arguments import SmartArgumentParser
from lib.parsers.configuration import get_global_conf, get_trigger_conf
from lib import logger
from lib.parsers import arguments


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


PROGRAMS = get_global_conf().getlist("trigger", "programs")


def parse_args(args: list) -> dict:
    """
    Create a parser for command line attributes and parses them
    :param args: the arguments to parse
    :return: parsed arguments
    """
    parser = SmartArgumentParser(
        description="Triggers some bug in listed programs", parents=[arguments.get_verbosity_parser()]
    )
    plugin_parser = parser.add_subparsers(metavar="plugin")
    parser.add_argument("bugs", nargs="+", type=str, help="one of {} or all".format(", ".join(PROGRAMS)), metavar="bug",
                        choices=PROGRAMS+["all"])

    register_for_trigger(parser=parser, subparser=plugin_parser)

    parsed_args = parser.parse_args(args)

    # noinspection PyUnresolvedReferences
    logging.getLogger().setLevel(parsed_args.logging_level)

    _bugs = parsed_args.bugs
    if "all" in _bugs:
        parsed_args.bugs = [
            program for program in PROGRAMS
            if os.path.exists(get_trigger_conf(program).get("install_directory"))
        ]
    else:
        for _ in _bugs:
            if _ not in PROGRAMS:
                parser.print_help()
                exit(PROGRAM_ARGUMENT_ERROR)

    return vars(parsed_args)


def trigger_bug(bug: str, main_plugin: MainPlugin, **kwargs: dict) -> int:
    """
    Trigger a bug against the main_plugin
    :param bug: the bug to trigger
    :param main_plugin: the plugin against which to trigger
    :param kwargs: additional keywords arguments to pass
    :return: 0|!0 on success| failure
    """
    plugin_args = kwargs.copy()

    try:
        logging.info("Triggering %(bug)s", dict(bug=bug))

        trigger = importlib.import_module("data.{}.trigger".format(bug)).Trigger()

        plugin_args.update(
            {
                "main_plugin": main_plugin,
                "trigger": trigger
            }
        )

        if not os.path.exists(trigger.conf.getdir("install_directory")):
            raise ProgramNotInstalledException(trigger.conf.get("name"))

        pre_trigger_run(**plugin_args)

        plugin_args["error"] = trigger.run()

        error = check_trigger_success(**plugin_args)
        if error:
            logging.error("%(bug)s did not run successfully", dict(bug=bug))
            return error

        post_trigger_run(**plugin_args)

    finally:
        logging.verbose("Cleaning environment")
        post_trigger_clean(**plugin_args)


def main(bugs: list, main_plugin: MainPlugin or MetaPlugin, **kwargs: dict) -> None:
    """
    Run all given bugs
    :param bugs: bugs to run
    :param main_plugin: the main plugin enabled for the run
    :param kwargs: additional information for bug triggering
    """
    change_coredump_filter()

    if isinstance(main_plugin, MetaPlugin):
        plugins = before_run(main_plugin=main_plugin, bugs=bugs, **kwargs)
        main_plugins = plugins["main_plugins"]
        kwargs["analysis_plugins"] = plugins["analysis_plugins"]
    else:
        main_plugins = [main_plugin]

    return_values = []
    exceptions = []
    for plugin in main_plugins:
        for bug in bugs:
            try:
                logger.start_new_log_section(bug, "triggering")
                return_values.append(trigger_bug(bug=bug, main_plugin=plugin, **kwargs))
            except (PluginIncompatibleException, ProgramNotInstalledException) as exc:
                logging.warning(exc)
                exceptions.append(exc)

    err = None
    if isinstance(main_plugin, MetaPlugin):
        err = after_run(
            main_plugin=main_plugin, plugins=main_plugins, bugs=bugs,
            return_values=return_values, exceptions=exceptions, **kwargs
        )
    elif len(exceptions):
        err = 1

    return err or any(return_values)


if __name__ == "__main__":
    try:
        logger.setup_logging()
        load_plugins()
        exit(main(**parse_args(sys.argv[1:])))
    except KeyboardInterrupt:
        exit(1)
