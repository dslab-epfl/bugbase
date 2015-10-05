#!/usr/bin/env python
# coding=utf-8
# pylint: disable=invalid-name

"""
Module to test that all registered programs can be used
"""

__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


import os

from lib import constants
from lib.parsers.configuration import get_global_conf
from tests.unit_tests import UnitTest


class TestAllProgramsAreUsed(UnitTest):
    """
    Checks that all programs are usable
    """
    def test_all_programs_are_registered(self) -> None:
        """
        Checks that all programs registered have a directory and vice-versa
        """
        programs_registered = set(get_global_conf().getlist("install", "programs"))
        program_dirs = set(os.listdir(constants.PROGRAMS_SOURCE_PATH))
        self.assertSetEqual(programs_registered, program_dirs)
