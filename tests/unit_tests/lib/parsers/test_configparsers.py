#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=invalid-name

"""
Unittests for the lib.configparser module
"""

__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


from tempfile import NamedTemporaryFile

from lib.parsers.configuration import CompilerParser
from tests.unit_tests import UnitTest


class TestCompilerParser(UnitTest):
    """
    Tests for the compiler configuration reader
    """
    def test_update_install_section_no_loose_interpolation(self):
        """
        Tests that the interpolation is not lost when removing the default dictionary
        """
        with NamedTemporaryFile(mode="w+") as _file_:
            _file_.write("[install]\n")
            _file_.write("name = just_a_test")
            _file_.seek(0)

            config = CompilerParser()
            config.read([_file_.name])
            config.set("install", "name", "not_just_a_test")

            self.assertEqual(config.get("install", "name"), config.get("install", "display_name"))
