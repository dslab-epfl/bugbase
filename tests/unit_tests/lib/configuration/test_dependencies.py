#!/usr/bin/env python
# coding=utf-8
# pylint: disable=missing-docstring

"""
Tests for dependency handler
"""

import logging
import os
from unittest import mock
import sys

import lib.configuration.dependencies
import lib.helper
from lib.parsers.configuration import get_global_conf
from tests.lib import raise_
from tests.unit_tests import UnitTest


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class InstallTester(UnitTest):
    def setUp(self):
        logging.verbose = logging.debug

    def launch_and_log_modules(self, cmd, expected):
        self.assertEqual("--user" in cmd, expected)

    @staticmethod
    def test_no_module_handling():
        get_global_conf().set("install", "module_handling", "false")
        with \
                mock.patch("lib.configuration.dependencies.install_python_modules", lambda: raise_(Exception("NO"))),\
                mock.patch("lib.configuration.dependencies.install_wllvm", lambda _: 0),\
                mock.patch("lib.configuration.dependencies.get_programs_dependencies", lambda: []):
            lib.configuration.dependencies.install(True)

    def test_module_handling(self):
        get_global_conf().set("install", "module_handling", "true")
        with \
                mock.patch("lib.configuration.dependencies.install_python_modules", lambda: raise_(Exception("NO"))),\
                mock.patch("lib.configuration.dependencies.install_wllvm", lambda _: 0),\
                mock.patch("lib.configuration.dependencies.get_programs_dependencies", lambda: []):
            try:
                lib.configuration.dependencies.install(True)
            except Exception as exc:  # pylint: disable=broad-except
                self.assertEqual(str(exc), "NO")

    def test_program_dependencies(self):
        get_global_conf().set("install", "programs", "transmission-142")
        dependencies = lib.configuration.dependencies.get_programs_dependencies()
        self.assertIn("libssl-dev", dependencies)

    def test_install_modules_in_venv(self):
        with mock.patch(
            "lib.configuration.dependencies.launch_and_log",
            lambda cmd, error_msg: self.launch_and_log_modules(cmd, False)
        ):
            sys.real_prefix = "/root/test"
            sys.prefix = sys.base_prefix
            lib.configuration.dependencies.install_python_modules()

    def test_install_modules_in_pyenv(self):
        with mock.patch(
            "lib.configuration.dependencies.launch_and_log",
            lambda cmd, error_msg: self.launch_and_log_modules(cmd, False)
        ):
            sys.prefix = os.path.join(sys.base_prefix, "another")
            lib.configuration.dependencies.install_python_modules()

    def test_install_modules_system(self):
        with mock.patch(
            "lib.configuration.dependencies.launch_and_log",
            lambda cmd, error_msg: self.launch_and_log_modules(cmd, True)
        ):
            sys.prefix = sys.base_prefix
            if hasattr(sys, "real_prefix"):
                del sys.real_prefix  # pragma nocover
            lib.configuration.dependencies.install_python_modules()

    def test_installer_selects_wllvm(self):
        with mock.patch(
            "lib.configuration.dependencies.Installer.run",
            lambda x: raise_(Exception(x.conf.get("name")))
        ):
            try:
                lib.configuration.dependencies.install_wllvm(True)
            except Exception as exc:  # pylint: disable=broad-except
                self.assertEqual(str(exc), "wllvm")
