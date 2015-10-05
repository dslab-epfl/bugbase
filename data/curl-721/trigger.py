#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script triggers a bug in curl (version 7.21).
"""

__author__ = "Baris Kasikci, baris.kasikci@epfl.ch"


from lib.plugins import create_big_file
from lib.trigger import BaseTrigger


class Trigger(BaseTrigger):
    """
    Curl-721-specific Trigger
    """
    def __init__(self):
        super().__init__()
        self.benchmark.pre_benchmark_run = self.pre_benchmark_run

    @property
    def program(self) -> str:
        """
        The program name
        """
        return "curl-721"

    @property
    def failure_cmd(self) -> str:
        """
        The command to trigger the bug. Here we call curl with an even number of brackets, which triggers the bug
        """
        return self.conf.get_executable() + " {}{"

    @property
    def expected_failure(self) -> int:
        """
        When triggering our bug, curl returns error code 139.
        """
        return 139

    @property
    def success_cmd(self) -> str:
        """
        To trigger a non failing run, we simply have to download something that is correct. For example google.ch
        """
        return self.conf.get_executable() + " http://www.msnbc.msn.com/id/21773401/"

    def pre_benchmark_run(self) -> None:
        """
        For benchmarking purpose, downloading a file from the internet is too much throughput limited. We fallback to
        a big file created on our disk
        """
        path = create_big_file(1024*15)
        self.cmd = self.cmd.rsplit(" ", 1)[0] + " file://{}".format(path)
