#!/usr/bin/env python3
# coding=utf-8

"""
A plugin for Mozilla's Record Replay. See https://github.com/mozilla/rr
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


import os

from lib.installer import Installer
from lib.parsers.configuration import get_global_conf, get_plugin_conf
from lib.trigger import RawTrigger
from plugins.base.success import Success


class RR(Success):
    """
    Record Replay by Mozilla
    """
    help = "Mozilla's Record Replay"

    def pre_trigger_run(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        Updates the trigger command to run rr on top of the plugin's command
        :param trigger: the trigger that will run
        :param args: other arguments to pass to parents
        :param kwargs: other keywords arguments to pass to parents
        """
        super().pre_trigger_run(trigger=trigger, **kwargs)
        rr_location = os.path.join(get_global_conf().getdir("utilities", "install_directory"), "rr")
        trigger.cmd = "{} record {}".format(os.path.join(rr_location, "bin/rr"), trigger.cmd)

    @staticmethod
    def configure(force: bool) -> None:
        """
        Downloads RR from Github and installs it
        :param force: True to install even if nothing has changed
        """
        mozilla_rr = get_plugin_conf("base", "rr")
        installer = Installer.factory(mozilla_rr["rr"], force)
        installer.run()
