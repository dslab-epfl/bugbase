#!/usr/bin/env python3
# coding=utf-8

"""
This script triggers a bug in cppcheck (#148).
"""

from contextlib import suppress
import os
import shutil

from lib.parsers.configuration import get_global_conf
from lib import constants
from lib import hooks
from lib.trigger import BaseTrigger


__author__ = 'Benjamin Schubert, benjamin.schubert@epfl.ch'


class Trigger(BaseTrigger):
    """
    This trigger is for a bug in cppcheck 1.48, which is unable to parse a way of adding assembly code in it
    """
    def __init__(self):
        super().__init__()
        self.benchmark.pre_benchmark_run = self.pre_benchmark_run
        hooks.register_for_cleaning(self.post_trigger_clean)

    @property
    def program(self):
        """
        The program name
        """
        return "cppcheck-148"

    @property
    def failure_cmd(self) -> str:
        """
        To trigger this bug, we need to run a complete test on a file containing assembly
        """
        return "{} --enable=all -f -q {}".format(
            self.conf.get_executable(), constants.ROOT_PATH + "/data/cppcheck-148/trial-fail.cpp"
        )

    @property
    def expected_failure(self) -> int:
        """
        When failing in the way we expect, cppcheck will return a 139 error.
        """
        return 139

    @property
    def success_cmd(self) -> str:
        """
        To trigger a successful run, it is sufficient to replace the assembly code declaration by another type of
        declaration
        """
        return self.failure_cmd.replace("trial-fail.cpp", "trial-success.cpp")

    def pre_benchmark_run(self) -> None:
        """
        For benchmarking, we need to work on bigger files. We use transmission for this purpose
        """
        shutil.unpack_archive(
            os.path.join(get_global_conf().get("install", "source_directory"), "cppcheck-148/cppcheck-1.48.tar.gz"),
            "/tmp/cppcheck-148"
        )
        self.cmd = " ".join(self.cmd.split(" ")[:-1]) + " /tmp/cppcheck-148/cppcheck-1.48"

    # noinspection PyUnusedLocal
    @staticmethod
    def post_trigger_clean(*args, **kwargs) -> None:
        """
        After a successful run, we remove transmission if we used it
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        with suppress(FileNotFoundError):
            shutil.rmtree("/tmp/cppcheck-148")
