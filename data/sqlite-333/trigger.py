#!/usr/bin/env python3
# coding=utf-8

"""
This script triggers a bug in sqlite (3.3.3)
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from contextlib import suppress
import logging
import psutil
import os
import subprocess
import time

from lib import constants
from lib.trigger import BaseTrigger


class Trigger(BaseTrigger):
    """
    SQLite deadlock bug trigger
    """
    @property
    def program(self) -> str:
        """
        The program name, sqlite-333
        """
        return "sqlite-333"

    @property
    def failure_cmd(self) -> str:
        """
        The command to run for failing runs. It is simply calling the executable
        """
        return self.conf.get_executable()

    @property
    def success_cmd(self) -> str:
        """
        The success or failure is not input dependent, hence we have the same command to run
        """
        return self.failure_cmd

    @property
    def expected_failure(self) -> int:
        """
        When failing, sqlite will return 1
        """
        return 1

    @staticmethod
    def clean() -> None:
        """
        Cleans test files afterwards
        """
        with suppress(FileNotFoundError):
            os.remove(os.path.join(constants.ROOT_PATH, "testdb-1"))

    def run(self):
        """
        To run this program, we launch the command and wait until it is in a waiting state, which means it deadlocked.
        We will then kill it and return
        :return: 0|1|None on success|failure|unexpected result
        """
        logging.verbose(self.cmd)
        proc = subprocess.Popen(
            self.cmd.split(" "), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, preexec_fn=self.__preexec_fn__,
        )

        x = 0
        counter = 0
        while proc.poll() is None:
            if psutil.Process(proc.pid).status() == psutil.STATUS_SLEEPING:
                counter += 1
                if counter >= 1000:
                    proc.send_signal(11)
                    time.sleep(1)
                    self.clean()
                    return self.check_success(1)
                else:
                    time.sleep(0.01)
                    continue
            x += 1
            counter = 0
            time.sleep(0.01)

        self.clean()
        return self.check_success(proc.wait())
