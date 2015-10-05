#!/usr/bin/env python
# coding=utf-8

"""
Main module for unit tests. All unit tests should inherit this, to be discovered
"""

__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


import abc
import unittest


class UnitTest(unittest.TestCase, metaclass=abc.ABCMeta):
    """
    A base IntegrationTesting class
    """
    unittest = True
