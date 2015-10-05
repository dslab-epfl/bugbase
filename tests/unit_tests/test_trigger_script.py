#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=invalid-name

"""
Tests for the trigger entry point
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


import logging
import os

from lib import hooks
from lib.parsers.configuration import get_global_conf
from tests.lib.decorators import mute
from tests.unit_tests import UnitTest
import run


class TestTriggerScript(UnitTest):
    """
    Multiple unittest for the trigger script entry point
    """
    @classmethod
    def setUpClass(cls):
        """
        Loads all enabled plugins before running
        """
        hooks.load_plugins()
        logging.VERBOSE = logging.DEBUG
        logging.verbose = logging.debug

    def test_coredump_filter(self) -> None:
        """
        Checks that the coredump filter indeed gets changed
        """
        run.change_coredump_filter()
        my_filter = get_global_conf().get("trigger", "core_dump_filter")
        with open("/proc/{}/coredump_filter".format(os.getpid())) as proc_file:
            value = proc_file.read()

        self.assertEqual(my_filter, hex(int(value, 16)))

    @mute
    def test_argument_parser_void_exits(self) -> None:
        """
        Tests that the script cannot be called with no argument
        """
        self.assertRaises(SystemExit, run.parse_args, [])

    @mute
    def test_argument_parser_without_plugin_exits(self) -> None:
        """
        Tests that not giving a plugin exits
        """
        self.assertRaises(SystemExit, run.parse_args, ["pbzip-2094"])

    @mute
    def test_argument_parser_without_bug_exits(self) -> None:
        """
        Tests that not giving a bug exits
        """
        self.assertRaises(SystemExit, run.parse_args, ["success"])

    @mute
    def test_argument_parser_with_non_existing_bug_exits(self) -> None:
        """
        Tests that giving an non-existent program exits
        """
        self.assertRaises(SystemExit, run.parse_args, ["success", "garbage"])

    @mute
    def test_cannot_add_two_verbosity_args(self) -> None:
        """
        Checks that verbosity arguments are indeed exclusive
        """
        self.assertRaises(SystemExit, run.parse_args, ["success", "pbzip-2094", "-q", "-v"])
        self.assertRaises(SystemExit, run.parse_args, ["success", "pbzip-2094", "-d", "-v"])
        self.assertRaises(SystemExit, run.parse_args, ["success", "pbzip-2094", "-q", "-v"])

    def test_argument_parser_accept_one_bug(self) -> None:
        """
        Tests that it is possible to give one bug and one plugin
        """
        args = run.parse_args(["success", "pbzip-2094"])
        self.assertEqual(len(args["bugs"]), 1)
