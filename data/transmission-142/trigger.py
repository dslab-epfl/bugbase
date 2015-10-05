#!/usr/bin/env python3
# coding=utf-8

"""
This script triggers a bug in transmission (version 1.42).
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


import subprocess

from lib.exceptions import ProgramTriggerFailedException
from lib.trigger.benchmark import BaseBenchmark
from lib.trigger import BaseTrigger


class TransmissionBenchmark(BaseBenchmark):
    """
    Transmission benchmark is expected to return 1 instead of 0
    """
    def benchmark_helper(self) -> None:
        """
        Launches transmission and raises an exception if 1 is not returned
        :raise ProgramTriggerFailedException
        """
        if subprocess.call(self.trigger.cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL) != 1:
            raise ProgramTriggerFailedException("Failed launching benchmark command {}".format(self.trigger.cmd))


class Trigger(BaseTrigger):
    """
    Trigger for the transmission program
    """
    @property
    def program(self):
        """
        The program name
        """
        return "transmission-142"

    @property
    def benchmark(self) -> TransmissionBenchmark:
        """
        We need a special Benchmarking suite for transmission, as a correct run will return 1
        """
        return TransmissionBenchmark

    @property
    def failure_cmd(self) -> str:
        """
        Triggers the bug in transmissioncli
        """
        return "{}/bin/transmissioncli -n {}/bin/transmissioncli /tmp/test.torrent".format(
            self.conf.getdir("install_directory"), self.conf.getdir("install_directory")
        )

    @property
    def success_cmd(self) -> str:
        """
        The bug is not input dependant, send the same command as for failure
        """
        return self.failure_cmd

    @property
    def expected_failure(self) -> int:
        """
        When failing with the bug we want, transmission will return 134
        """
        return 134

    def check_success(self, error_code: int, *args, **kwargs) -> int:
        """
        When running transmission, we expect an error code of 1, which makes it simpler as we don't have to download
        a real torrent from the internet. We therefore consider 1 is a success
        :param error_code: the error code returned by transmission
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|failure|unexpected error
        """
        if error_code == 1:
            error_code = 0
        return super().check_success(error_code)
