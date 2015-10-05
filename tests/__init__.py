#!/usr/bin/env python
# coding=utf-8

"""
Main module for tests. All tests should inherit this, in order to implement the base necessary functions to have
"""

__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


import os

from lib.parsers.configuration import get_global_conf


TEST_DIRECTORY = os.path.join(get_global_conf().getdir("trigger", "default_directory"), "tests-results")
SAVE_DIRECTORY = os.path.join(TEST_DIRECTORY, "saved")
