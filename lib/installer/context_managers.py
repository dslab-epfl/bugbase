#!/usr/bin/env python
# coding=utf-8

"""
Some context Managers to safely modify installers during creation of custom versions
"""

# pylint: disable=too-few-public-methods

import os
import fcntl

from lib import constants


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


class EnvironmentManager:
    """
    A manager to safely modify the environment variables of an installer for a run
    """
    def __init__(self, installer, updates: dict):
        self.installer = installer
        self.env = None
        self.updates = updates

    def __enter__(self):
        self.env = self.installer.env.copy()
        self.installer.env.update(self.updates)

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.installer.env = self.env.copy()


class ExtensionPatcherManager:
    """
    A manager to safely patch sources for a given extension. Automatically checks if the patch exists
    """
    def __init__(self, installer, extension: str, directory=None):
        self.installer = installer
        self.directory = directory or self.installer.working_dir
        self.patch = []
        self.patches_path = self.installer.patches_path
        self.is_patched = False

        for plugin_directory in os.listdir(constants.PLUGINS_PATH):
            if not os.path.isdir(os.path.join(constants.PLUGINS_PATH, plugin_directory)):
                continue

            if "{}.py".format(extension) in os.listdir(os.path.join(constants.PLUGINS_PATH, plugin_directory)):
                patches_path = os.path.join(constants.PLUGINS_PATH, plugin_directory, "patches")

                patch = "{}-{}.patch".format(self.installer.conf.get("display_name"), extension)
                if os.path.exists(os.path.join(patches_path, patch)):
                    self.patches_path = patches_path
                    self.patch = [patch]
                    self.is_patched = True

    def __enter__(self):
        self.installer.patch(self.patch, self.directory, patches_path=self.patches_path)
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.installer.patch(self.patch, self.directory, reverse=True, patches_path=self.patches_path)


class LastAccessManager:
    """
    A manager to touch a list of file at entrance and exit
    """
    def __init__(self, files: list):
        self.files = files

    def __enter__(self):
        for _file_ in self.files:
            os.utime(_file_)

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        for _file_ in self.files:
            os.utime(_file_)


class FileLock:
    """
    A lock system using files to be consistent across processes
    """
    def __init__(self, file):
        self.__lock_file__ = file
        self.__fd = None

    def __enter__(self):
        self.__fd = open(self.__lock_file__, "w")
        fcntl.lockf(self.__fd, fcntl.LOCK_EX)

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.lockf(self.__fd, fcntl.LOCK_UN)
        self.__fd.close()
