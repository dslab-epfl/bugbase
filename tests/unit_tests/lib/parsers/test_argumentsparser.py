#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# pylint: disable=missing-docstring

"""
Tests for the configparser
"""


from lib.parsers.arguments import SmartArgumentParser
from tests.lib.decorators import mute
from tests.unit_tests import UnitTest


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class TestSmartArgumentParser(UnitTest):
    def setUp(self):
        self.argparser = SmartArgumentParser()
        self.subparser = self.argparser.add_subparsers()
        self.subparser.add_parser("test").set_defaults(test=2)
        self.argparser.add_argument("entries", nargs="+", type=int)

    def test_can_add_one_of_each(self):
        args = vars(self.argparser.parse_args(["test", "1"]))
        self.assertEqual(args, {'entries': [1], 'test': 2})

    def test_can_add_multiple_entries(self):
        args = vars(self.argparser.parse_args(["test", "1", "2", "3"]))
        self.assertEqual(args["test"], 2)
        self.assertSetEqual(set(args["entries"]), {1, 2, 3})

    @mute
    def test_if_wrong_argument(self):
        self.assertRaises(SystemExit, self.argparser.parse_args, ["test", "1", "2", "-n"])
