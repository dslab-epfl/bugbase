#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script triggers a bug in apache (#21287).
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"

import re

from lib.trigger import ApacheTrigger


class Trigger(ApacheTrigger):
    """
    Trigger for bug 21287 in Apache
    """
    @property
    def program(self) -> str:
        """
        The program name
        """
        return "apache-21287"

    @property
    def helper_commands(self) -> list:
        """
        Gets the list of urls to fetch in order to make the bug occur
        """
        return ["http://127.0.0.1:{port}/pippo.php?variable=1111"] * 2

    @property
    def error_pattern(self):
        """
        The error pattern to search in Apache's error_log to see if bug was triggered
        """
        return re.compile("^\*\*\* Error in `.*/bin/httpd.*': free\(\): invalid pointer: 0x.* \*\*\*$")

    @property
    def benchmark_url(self) -> str:
        """
        Gets the url to fetch when benchmarking
        """
        return "http://127.0.0.1:{}/pippo.php?variable=1111".format(self.conf.get("listening_port"))
