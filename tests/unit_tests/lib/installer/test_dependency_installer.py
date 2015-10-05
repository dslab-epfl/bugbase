#!/usr/bin/env python
# coding=utf-8
# pylint: disable=invalid-name

"""
Tests for checking that all plugins are discoverable and usable
"""


import subprocess
from unittest import mock

import lib.exceptions
from lib.installer.dependency_installer import DependenciesInstaller
from tests.lib.decorators import mute
from tests.lib import raise_
from tests.unit_tests import UnitTest


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


class TestDependencyInstaller(UnitTest):
    """
    Tests for the DependencyInstaller
    """
    def test_unsupported_distro_raises_exception(self):
        """ Checks that using an unsupported distribution will raise an exception and not return """
        with mock.patch('platform.dist', lambda: ("Goat", "13.37", "tsy")):
            with self.assertRaises(lib.exceptions.DistributionNotSupportedException):
                DependenciesInstaller.factory([])

    @mute
    def test_retries_with_update_on_error(self):
        """ Checks that the installer will try a second time on error """
        with mock.patch(
            "lib.installer.dependency_installer.AptBasedInstaller.get_missing_packages",
            lambda x, y: [1, 2, 3]
        ), mock.patch(
            'lib.installer.dependency_installer.AptBasedInstaller.install',
            lambda x, y: raise_(subprocess.CalledProcessError(2, "just a test"))
        ), mock.patch(
            'lib.installer.dependency_installer.AptBasedInstaller.update_sources',
            lambda x: raise_(subprocess.SubprocessError)
        ):
            with self.assertRaises(subprocess.SubprocessError):
                DependenciesInstaller.factory([]).run()

    @mute
    def test_give_up_after_second_error(self):
        """ Checks that the installer gives up after 2 tries """
        with mock.patch(
            "lib.installer.dependency_installer.AptBasedInstaller.get_missing_packages",
            lambda x, y: ["1", "2", "3"]
        ), mock.patch(
            'lib.installer.dependency_installer.AptBasedInstaller.install',
            lambda x, y: raise_(subprocess.CalledProcessError(2, "just a test"))
        ), mock.patch(
            'lib.installer.dependency_installer.AptBasedInstaller.update_sources',
            lambda x: 0
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                DependenciesInstaller.factory([]).run()
