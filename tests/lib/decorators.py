#!/usr/bin/env python3
# coding=utf-8

"""
Decorators to ease test creation
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from functools import wraps
import os
from unittest.mock import patch


def mute(func: callable) -> callable:
    """
    Patches stderr and stdout for this function in order to silent any output it could have
    :param func: the function to patch
    :return: the function, silenced
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Patches stderr and stdout as devnull and returns the function
        :param args: arguments to pass to the underlying function
        :param kwargs: keyword arguments to pass to the underlying function
        """
        with open(os.devnull, "w") as devnull:
            with patch('sys.stdout', devnull), patch('sys.stderr', devnull):
                func(*args, **kwargs)

    return wrapper
