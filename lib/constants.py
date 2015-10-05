#!/usr/bin/env python3
# coding=utf-8

"""
A module to handle some constants used in all the program
"""

__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


import os


ROOT_PATH = "/".join(os.path.realpath(__file__).split("/")[:-2])
PROGRAMS_SOURCE_PATH = os.path.join(ROOT_PATH, "data")
CONF_PATH = os.path.join(ROOT_PATH, "conf")
PLUGINS_PATH = os.path.join(ROOT_PATH, "plugins")


PROGRAM_ARGUMENT_ERROR = 1
CONFIGURATION_FAIL = 4
MAKE_FAIL = 8
INSTALL_FAIL = 16
SOURCE_PREPARATION_ERROR = 32
PATCH_ERROR = 64
PROGRAM_TRIGGER_FAIL = 128
PLUGIN_ERROR = 255
