#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script triggers a bug in apache (#45605).
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"

import re

from lib.trigger import ApacheTrigger


class Trigger(ApacheTrigger):
    """
    Trigger class for apache bug 45605
    """
    @property
    def program(self) -> str:
        """
        The program name
        """
        return "apache-45605"

    @property
    def helper_commands(self) -> list:
        """
        Gets a list of urls used to trigger the bug
        """
        return [
            "http://127.0.0.1:{port}/index.html",
            "http://127.0.0.1:{port}/apache_pb22.png"
        ] * 4

    @property
    def error_pattern(self):
        """
        The error pattern to search in Apache error_log to check if the bug was triggered
        """
        return re.compile(
            "^.* file fdqueue\.c, line 307, assertion \"!\(\(queue\)->nelts == \(queue\)->bounds\)\" failed$"
        )

    @property
    def benchmark_url(self) -> str:
        """
        The url to fetch for benchmarking means
        """
        return "http://127.0.0.1:{port}/index.html".format(port=self.conf.get("listening_port"))
