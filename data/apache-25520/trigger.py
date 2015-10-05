#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script triggers a bug in apache (#25520).
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"

import re

from lib.trigger import ApacheTrigger


class Trigger(ApacheTrigger):
    """
    Trigger for apache 25520
    """
    @property
    def program(self) -> str:
        """
        gets the program name
        """
        return "apache-25520"

    @property
    def helper_commands(self) -> list:
        """
        list of urls to fetch on the server to make the server crash
        """
        return [
            "http://127.0.0.1:{port}/index.html.en",
            "http://127.0.0.1:{port}/index.html.fr"
        ] * 4

    @property
    def error_pattern(self):
        """
        The pattern to search in Apache's error_log, to know if the error happened
        """
        return re.compile("^.*child pid .* exit signal Segmentation fault \(11\), possible coredump in .*/apache-25520")

    @property
    def benchmark_url(self) -> str:
        """
        The url to fetch for benchmarking
        """
        return "http://127.0.0.1:{port}/index.html.fr".format(port=self.conf.get("listening_port"))

    @property
    def named_helper_args(self) -> dict:
        """
        Adds the listening port and the number of iteration to do to the arguments passed to the helper
        """
        return {
            "port": self.conf["listening_port"],
            "iterations": 100
        }
