#!/usr/bin/env python3
# coding=utf-8

"""
This script triggers a bug in cppcheck (#152).
"""
from lib.parsers.configuration import get_global_conf

__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


from contextlib import suppress
import os
import shutil

from lib import hooks
from lib import constants
from lib.trigger import BaseTrigger


class Trigger(BaseTrigger):
    """
    This is the trigger for a bug in cppcheck 1.52
    """
    def __init__(self):
        super().__init__()
        self.benchmark.pre_benchmark_run = self.pre_benchmark_run
        hooks.register_for_cleaning(self.post_trigger_clean)

    @property
    def program(self) -> str:
        """
        The program name
        """
        return "cppcheck-152"

    @property
    def failure_cmd(self) -> str:
        """
        Runs cppcheck with everything enabled against a maliciously crafted file
        """
        return "{} --enable=all -f -q {}".format(
            self.conf.get_executable(), constants.ROOT_PATH + "/data/cppcheck-152/trial-fail.cpp"
        )

    @property
    def expected_failure(self) -> int:
        """
        When failing, cppcheck will return a 139 error code
        """
        return 139

    @property
    def success_cmd(self) -> str:
        """
        For a successful run, it is sufficient to run cppcheck on a correctly formatted file
        """
        return self.cmd.replace("trial-fail.cpp", "trial-success.cpp")

    def pre_benchmark_run(self) -> None:
        """
        When benchmarking, it is better to have a bigger workload. We use transmission for this purpose
        """
        shutil.unpack_archive(
            os.path.join(get_global_conf().get("install", "source_directory"), "cppcheck-152/cppcheck-1.52.tar.gz"),
            "/tmp/cppcheck-152"
        )
        self.cmd = " ".join(self.cmd.split(" ")[:-1]) + " /tmp/cppcheck-152/cppcheck-1.52"

    # noinspection PyUnusedLocal
    @staticmethod
    def post_trigger_clean(*args, **kwargs) -> None:
        """
        After the run, we clean the transmission file if needed
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        with suppress(FileNotFoundError):
            shutil.rmtree("/tmp/cppcheck-152")
