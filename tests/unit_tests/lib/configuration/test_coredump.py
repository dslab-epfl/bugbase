#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=invalid-name,missing-docstring

"""
Tests for the coredump handling module
"""


from unittest.mock import patch, mock_open

import lib.configuration.coredump
from tests.lib import raise_
from tests.unit_tests import UnitTest


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


@patch("lib.configuration.coredump.launch_and_log_as_root", lambda cmd: raise_(Exception(" ".join(cmd))))
class TestCoredumps(UnitTest):
    call_regexp = r"^echo.*?sysctl.conf$"

    def test_updates_sysctl_if_coredump_not_there(self):
        with patch('lib.configuration.coredump.open', mock_open(), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj  # this is mandatory, https://bugs.python.org/issue21258
            mocked.return_value.__next__ = lambda obj: obj.readline()
            self.assertRaisesRegex(Exception, self.call_regexp, lib.configuration.coredump.change_coredump_pattern)

    def test_updates_sysctl_if_coredump_commented(self):
        data = "# /tmp/coredumps/%E.core"
        with patch('lib.configuration.coredump.open', mock_open(read_data=data), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj
            mocked.return_value.__next__ = lambda obj: obj.readline()
            self.assertRaisesRegex(Exception, self.call_regexp, lib.configuration.coredump.change_coredump_pattern)

    def test_updates_sysctl_if_coredump_after_comment(self):
        data = "kernel.core_pattern=2 # /tmp/coredumps/%E.core"
        with patch('lib.configuration.coredump.open', mock_open(read_data=data), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj
            mocked.return_value.__next__ = lambda obj: obj.readline()
            self.assertRaisesRegex(Exception, self.call_regexp, lib.configuration.coredump.change_coredump_pattern)

    # this can't be static because of the patch function which passes an argument
    def test_no_updates_sysctl_if_comment_after_coredump(self):  # pylint: disable=no-self-use
        data = "kernel.core_pattern=/tmp/coredumps/%E.core # this is for bugbase"
        with patch('lib.configuration.coredump.open', mock_open(read_data=data), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj
            mocked.return_value.__next__ = lambda obj: obj.readline()
            lib.configuration.coredump.change_coredump_pattern()

    def test_update_if_other_coredump(self):
        data = "kernel.core_pattern=/tmp/coredumps/%E.core\nkernel.core_pattern=/tmp/goat"
        with patch('lib.configuration.coredump.open', mock_open(read_data=data), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj
            mocked.return_value.__next__ = lambda obj: obj.readline()
            self.assertRaisesRegex(Exception, self.call_regexp, lib.configuration.coredump.change_coredump_pattern)

    # this can't be static because of the patch function which passes an argument
    def test_no_update_if_other_coredump_commented(self):  # pylint: disable=no-self-use
        data = "kernel.core_pattern=/tmp/coredumps/%E.core\n# kernel.core_pattern=/tmp/goat"
        with patch('lib.configuration.coredump.open', mock_open(read_data=data), create=True) as mocked:
            mocked.return_value.__iter__ = lambda obj: obj
            mocked.return_value.__next__ = lambda obj: obj.readline()
            lib.configuration.coredump.change_coredump_pattern()
