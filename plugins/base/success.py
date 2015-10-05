#!/usr/bin/env python3
# coding=utf-8

"""
Simple trigger to run a successful run on the program.
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from contextlib import suppress
import logging
import os

from lib.constants import PLUGIN_ERROR
from lib.plugins import MainPlugin
from lib.trigger import RawTrigger


class Success(MainPlugin):
    """
    Simple plugin to trigger successful runs
    """
    help = "Simple trigger for successful runs"

    @property
    def extension(self) -> str:
        """
        success
        :return: "success"
        """
        return "success"

    def pre_trigger_run(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Runs before trigger. Changes the trigger command if a success_cmd is provided, then updates the executable
        :param trigger: The trigger instance that is run
        :param args: other arguments to pass to parents
        :param kwargs: other keyword arguments to pass to parents
        """
        with suppress(AttributeError):
            # noinspection PyUnresolvedReferences
            trigger.cmd = trigger.success_cmd

        trigger_full_path = trigger.cmd.split(" ")[0]
        if os.path.exists("{}-{}".format(trigger_full_path, self.extension)):
            trigger.cmd = trigger.cmd.replace(trigger_full_path, "{}-{}".format(trigger_full_path, self.extension))
            trigger.conf["executable"] = "{}-{}".format(trigger.conf.get("executable"), self.extension)

    def check_trigger_success(self, error, trigger, *args, **kwargs):
        """
        Checks that the trigger ended successfully. This is True if error is 0
        :param error: the result given by the trigger
        :param trigger: the trigger instance that is run
        :param args: other arguments to pass to parents
        :param kwargs: other arguments to pass to parents
        :return: 0|PLUGIN_ERROR on success|failure or unexpected failure
        """
        if error is None:
            logging.error("The bug failed with an unknown error code")
            return PLUGIN_ERROR

        if error:
            return PLUGIN_ERROR

        else:
            logging.info("%(name)s ran successfully", dict(name=trigger.conf.get("name")))
            return 0
