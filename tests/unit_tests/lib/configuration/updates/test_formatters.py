#!/usr/bin/env python
# coding=utf-8
# pylint: disable=missing-docstring

"""
Tests for question formatter
"""


from lib.configuration.update import format_list_numbered, format_closed_question
from tests.unit_tests import UnitTest


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


class FormatterTester(UnitTest):
    def test_format_empty_list(self):
        self.assertEqual(format_list_numbered([], _default_="yes"), ["None"])

    def test_format_list(self):
        list_unnumbered = ["one", "two", "three"]
        value = format_list_numbered(list_unnumbered, "one")
        self.assertIn("default", value[0])
        for i in range(0, 3):
            self.assertIn(str(i), value[i])

    def test_format_close_question(self):
        self.assertEqual(format_closed_question(True), "[Y/n]")
        self.assertEqual(format_closed_question(False), "[y/N]")
