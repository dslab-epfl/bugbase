#!/usr/bin/env python3
# coding=utf-8

"""
Library for the test infrastructure of Bugbase
"""
from tests.lib.structures import Plugin, Compiler


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


def raise_(exc: Exception) -> None:
    """
    Utility function to raise an exception

    :param exc: the exception to raise
    :raise exc
    """
    raise exc
