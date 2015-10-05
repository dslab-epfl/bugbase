#!/usr/bin/env python
# coding=utf-8
# pylint: disable=invalid-name

"""
Tests for checking that all plugins are discoverable and usable
"""

__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


import importlib
import os

from lib import hooks, constants
from lib.plugins import BasePlugin
from tests.unit_tests import UnitTest


class TestAllCreatedPluginsRespectContracts(UnitTest):
    """
    Checks that all plugins respect the api
    """
    def test_all_plugin_file_contain_one_plugin(self) -> None:
        """
        Checks that all plugins can be imported, and have a class in their module allowing to call it
        """
        plugin_files = []

        for package in os.listdir(constants.PLUGINS_PATH):
            if not os.path.isdir(os.path.join(constants.PLUGINS_PATH, package)):
                continue

            for _file_ in os.listdir(os.path.join(constants.PLUGINS_PATH, package)):
                if _file_.endswith(".py"):
                    plugin_files.append("{}.{}".format(package, os.path.splitext(_file_)[0]))
                    importlib.import_module("plugins.{}.{}".format(package, os.path.splitext(_file_)[0]))

        plugins_classes = hooks.get_subclasses(BasePlugin)
        plugins = [plugin.__name__.lower() for plugin in plugins_classes]
        plugin_file_names = [
            _file_.split(".")[-1] for _file_ in plugin_files
            if "tests.test_" not in _file_ and "__init__" not in _file_
        ]
        self.assertEqual(set(plugins), set(plugin_file_names))
