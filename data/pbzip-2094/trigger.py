#!/usr/bin/env python3
# coding=utf-8

"""
This script triggers a bug in pbzip2 (version 0.94).
"""

__author__ = "Baris Kasikci, baris.kasikci@epfl.ch"


from lib import constants
from lib.plugins import create_big_file
from lib.trigger import BaseTrigger


class Trigger(BaseTrigger):
    """
    Pbzip2-specific Intel PT tracing
    """
    def __init__(self):
        super().__init__()
        self.benchmark.pre_benchmark_run = self.pre_benchmark_run

    @property
    def file(self):
        """
        The file used for tests
        """
        return constants.ROOT_PATH + "/data/pbzip-2094/test.tar"

    @property
    def program(self) -> str:
        """
        The program name
        """
        return "pbzip-2094"

    @property
    def expected_failure(self) -> int:
        """
        Expected failure for our bug is 139
        """
        return 139

    @property
    def failure_cmd(self) -> str:
        """
        The command to run when we want to trigger the bug
        """
        return "{} -k -f -p2 {}".format(self.conf.get_executable(), self.file)

    @property
    def success_cmd(self) -> str:
        """
        The command to run when we don't want to trigger the bug. Here the bug is input independent, hence we send back
        self.failure_cmd
        """
        return self.failure_cmd

    def pre_benchmark_run(self) -> None:
        """
        For benchmarking purpose, we need a much bigger file for this. Let's create one and replace it in the command
        """
        path = create_big_file(2048)
        self.cmd = self.cmd.replace(self.file, path)
