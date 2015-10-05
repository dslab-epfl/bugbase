#!/usr/bin/env python
# coding=utf-8

"""
Formatter to display information on the screen
"""

__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


def format_list_numbered(_list_: list, _default_: str) -> list:
    """
    Helper function to format a list and add numbers at the beginning
    :param _list_: the list to format
    :param _default_: the default value
    :return: a new formatted list
    """
    if len(_list_) == 0:
        return ["None"]

    return [
        "{}: {} (default)".format(index, value) if value == _default_
        else "{}: {}".format(index, value)
        for index, value in enumerate(_list_)
    ]


def format_closed_question(value: bool) -> str:
    """
    Formats a closed question answer depending on the default
    :param value: bool for the default
    :return: str
    """
    if value:
        return "[Y/n]"
    return "[y/N]"
