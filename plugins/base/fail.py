#!/usr/bin/env python3
# coding=utf-8

"""
A simple plugin implementation for failing run
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from contextlib import suppress
import logging
import os
import shutil
import time

from lib.plugins import MainPlugin
from lib.constants import PLUGIN_ERROR
from lib.parsers.configuration import get_global_conf
from lib.trigger import RawTrigger


class Fail(MainPlugin):
    """
    The base plugin implementation for triggering failing runs
    """
    extension = "fail"
    help = "Simple trigger for failing runs"

    def pre_trigger_run(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Updates the coredumps information in order to generate some correctly
        :param trigger: the trigger instance to use
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        trigger_full_path = trigger.cmd.split(" ")[0]
        if os.path.exists("{}-{}".format(trigger_full_path, self.extension)):
            trigger.cmd = trigger.cmd.replace(trigger_full_path, "{}-{}".format(trigger_full_path, self.extension))
            trigger.conf["executable"] = "{}-{}".format(trigger.conf.get("executable"), self.extension)

        os.makedirs(get_global_conf().getdir("trigger", "core_dump_location"), exist_ok=True)

        core_path = trigger.conf.get_core_path()
        logging.verbose("core_path: %(core_path)s", dict(core_path=core_path))

        with suppress(OSError):
            logging.debug("attempting to delete old coredump at %(core_path)s", dict(core_path=core_path))
            os.remove(core_path)

    def check_trigger_success(self, error: int, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Checks that the program indeed failed with the registered error code and that a coredump was generated
        :param error: the error code of the program
        :param trigger: the trigger instance we are running
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|PLUGIN_ERROR on success|failure
        """
        time.sleep(0.1)  # wait for the kernel to generate the coredump. It might take some time under heavy load
        core_path = trigger.conf.get_core_path()

        if os.path.exists(trigger.conf.getdir("install_directory") + "/core"):
            shutil.move(trigger.conf.getdir("install_directory") + "/core", core_path)

        if os.path.exists(os.path.join(os.getcwd(), "core")):
            shutil.move(os.path.join(os.getcwd(), "core"), core_path)

        if os.path.exists(trigger.conf.getdir("install_directory") + "/var/core"):
            shutil.move(trigger.conf.getdir("install_directory") + "/var/core", core_path)

        main_core_path = "-".join(core_path.split("-")[:-1])

        if os.path.exists(main_core_path):
            shutil.move(main_core_path, core_path)

        if os.path.isfile(core_path):
            logging.info("Coredump generated at %(core_path)s", dict(core_path=core_path))

        else:
            logging.error("Could not generate coredump for %(name)s", dict(name=trigger.conf.get("name")))
            return PLUGIN_ERROR

        if error is None:
            logging.error("A bug was indeed triggered, but not the expected one. be careful !")
            return PLUGIN_ERROR
        elif error:
            logging.info("The correct bug was triggered")
            return 0
        else:
            logging.error("The bug did not reproduce, program exited with %(error_code)s", dict(error_code=error))
            return PLUGIN_ERROR

    def post_trigger_clean(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Saves all coredumps to the exp-results directory
        :param trigger: the trigger instance that we run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        destination_folder = os.path.join(get_global_conf().getdir("trigger", "exp-results"), trigger.conf.get("name"))

        with suppress(FileNotFoundError):
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            shutil.move(
                trigger.conf.get_core_path(),
                os.path.join(destination_folder, os.path.basename(trigger.conf.get_core_path()))
            )
