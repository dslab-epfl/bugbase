#!/usr/bin/env python3
# coding=utf-8

"""
Multiple helpers for triggering the bugs more easily. All Triggers should be subclasses of RawTrigger
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from abc import ABCMeta, abstractmethod
from contextlib import suppress
import queue
import multiprocessing
import logging
import os
import re
import subprocess
import resource
from threading import Thread
import time

from lib.helper import launch_and_log
from lib.trigger.benchmark import BenchmarkWithHelper, ApacheBenchmark, RawBenchmark, BaseBenchmark
from lib.trigger.helper import BaseHelper, UrlFetcherHelper
from lib.parsers.configuration import get_trigger_conf


class RawTrigger(metaclass=ABCMeta):
    """
    The base trigger for the bugs. All bug triggers should inherit it
    """
    def __init__(self):
        """
        Fetches the configuration of the program and stores it in conf.
        """
        self.__cmd__ = None
        self.__returned_information__ = None
        self.conf = get_trigger_conf(self.program)

    @property  # pragma nocover
    @abstractmethod
    def program(self) -> str:
        """ The program to run """

    @property  # pragma nocover
    @abstractmethod
    def benchmark(self) -> RawBenchmark:
        """ The Benchmarking class to use for this class """

    @abstractmethod
    def run(self) -> int:
        """
        The main function used to make the program trigger the bug. Should return the value of self.check_success()
        :return: 0|1|None on success|failure|unexpected error
        """

    @abstractmethod
    def check_success(self, *args, **kwargs) -> int:
        """
        Checks whether the run was successful or not
        :param args: other arguments
        :param kwargs: other keyword arguments
        :return: 0|1|None on success|failure|unexpected result
        """

    @property
    def cmd(self) -> str:
        """
        The command to execute in a subprocess
        """
        return self.__cmd__

    @cmd.setter
    def cmd(self, cmd: str) -> None:
        """
        cmd setter
        :param cmd: the new command
        """
        self.__cmd__ = cmd

    @property
    def returned_information(self) -> list:
        """
        Used to store results for the runs. This is by default None, and analysis plugins (such as benchmark) can add
        things to it
        """
        return self.__returned_information__

    @returned_information.setter
    def returned_information(self, returned_information: object) -> None:
        """
        Sets the result to the given value
        :param returned_information: the object to set up as a result
        """
        self.__returned_information__ = returned_information

    @staticmethod
    def __preexec_fn__() -> None:
        """
        A helper for setting the RLIMIT object to infinity, to be able to return full coredumps
        """
        resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


# noinspection PyAbstractClass
class BaseTrigger(RawTrigger, metaclass=ABCMeta):
    """
    A base trigger for running a single program and checking if the error is the good one
    """
    def __init__(self):
        super().__init__()
        self.cmd = self.failure_cmd

    @property  # pragma nocover
    @abstractmethod
    def failure_cmd(self) -> str:
        """ Defines the command to run on failure runs """

    @property  # pragma nocover
    @abstractmethod
    def success_cmd(self) -> str:
        """
        Defines the command to run on successful runs. This can be the same as failure_cmd for cases where the bug is
        not input dependent.

        In this case just define as:

        @property
        def success_cmd(self) -> str:
            return self.failure_cmd
        """

    @property  # pragma nocover
    @abstractmethod
    def expected_failure(self) -> int:
        """ The error code the program should return if the bug was successfully triggered """

    @property
    def benchmark(self) -> BaseBenchmark:
        """
        returns the benchmarking class to use for this
        """
        return BaseBenchmark

    def check_success(self, error_code: int, *args, **kwargs) -> int:
        """
        Checks for the success of the trigger result.
        :param error_code: the error code returned by the trigger
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|expected failure|unexpected failure
        """
        if error_code == self.expected_failure:
            return 1

        if error_code == 0:
            return 0

        logging.verbose("Got error code {}, expected {}".format(error_code, self.expected_failure))
        return None

    def run(self) -> int:
        """
        Runs the cmd program in a subprocess, with rlimit set and checks the output to be sure that it is the correct
        bug
        :return: 0|1|None on success|failure|unexpected result
        """
        logging.verbose(self.cmd)
        error_code = 0
        try:
            # noinspection PyTypeChecker
            launch_and_log(self.cmd, shell=True, preexec_fn=self.__preexec_fn__)
        except subprocess.CalledProcessError as exc:
            error_code = exc.returncode

        return self.check_success(error_code=error_code)


# noinspection PyAbstractClass
class TriggerWithHelper(RawTrigger, metaclass=ABCMeta):
    """
    A trigger using a helper thread for spawning process. Especially useful when triggering bug on servers with clients
    """
    class Server(Thread):
        """
        Thread to launch the subprocess for the server, in case some server don't go in background
        """
        def __init__(self, command: str):
            super().__init__()
            self.__output__ = None
            self.command = command

        def run(self):
            """
            Launches the command and waits for the output
            """
            with suppress(subprocess.CalledProcessError):
                launch_and_log(self.command.split(" "), preexec_fn=TriggerWithHelper.__preexec_fn__)

    def __init__(self):
        super().__init__()
        self.__cmd__ = self.start_cmd

    @property  # pragma nocover
    @abstractmethod
    def helper(self) -> BaseHelper:
        """ The helper to use """

    @property  # pragma nocover
    @abstractmethod
    def delay(self) -> int:
        """ The delay to wait between each program call, to let the server time to set up correctly """

    @property  # pragma nocover
    @abstractmethod
    def helper_commands(self) -> list:
        """ A list of commands to call in the helpers """

    @property  # pragma nocover
    @abstractmethod
    def start_cmd(self) -> str:
        """ A function that will be executed by subprocess to start the server """

    @property  # pragma nocover
    @abstractmethod
    def stop_cmd(self) -> str:
        """ A function that will be executed by subprocess. This should start the server """

    @property
    def benchmark(self) -> BenchmarkWithHelper:
        """
        Returns the benchmarking class to use with this class
        """
        return BenchmarkWithHelper

    @property
    def timeout(self) -> int:  # pylint: disable=no-self-use
        """
        Timeout in seconds to wait before killing the thread. Will be done once per helper command
        """
        return None

    @property
    def named_helper_args(self) -> dict:  # pylint: disable=no-self-use
        """
        Additional arguments to pass to the helper
        """
        return {}

    def run(self) -> int:
        """
        Main function. Calls every other one in order to make the bug trigger
        :return: 0|1|None on success|failure|unexpected event
        """
        try:
            logging.verbose(self.cmd)
            proc_start = self.Server(self.cmd)  # this is not a typo. Using cmd is REQUIRED for the sake of plugins
            proc_start.start()

            time.sleep(self.delay)

            triggers = []
            results_queue = multiprocessing.Queue()  # pylint: disable=no-member
            for command in self.helper_commands:
                # noinspection PyCallingNonCallable
                triggers.append(self.helper(command, results=results_queue, **self.named_helper_args))

            for thread in triggers:
                thread.start()

            for thread in triggers:
                thread.join(self.timeout)

            for thread in triggers:
                thread.terminate()

        finally:
            with suppress(subprocess.CalledProcessError):
                launch_and_log(self.stop_cmd.split(" "))

        results = []
        for _ in triggers:
            with suppress(queue.Empty):
                results.append(results_queue.get_nowait())

        time.sleep(self.delay)
        return self.check_success(results=results)


# noinspection PyAbstractClass
class ApacheTrigger(TriggerWithHelper):
    """
    A trigger specifically designed for apache
    """
    @property  # pragma nocover
    @abstractmethod
    def error_pattern(self) -> str:
        """ The error pattern to search in error_log """

    @property
    def benchmark(self) -> ApacheBenchmark:
        """
        Returns the correct benchmark for Apache programs (Using Apache Bench utility)
        """
        return ApacheBenchmark

    @property
    def start_cmd(self) -> str:
        """
        The start command for apache
        """
        return "{}/bin/httpd -k start".format(self.conf.getdir("install_directory"))

    @property
    def stop_cmd(self) -> str:
        """
        The stop command for apache
        """
        return "{}/bin/httpd -k stop".format(self.conf.getdir("install_directory"))

    def clean_logs(self) -> None:
        """
        Cleans the log files before running an experiment
        """
        with suppress(FileNotFoundError):
            os.remove(os.path.join(self.conf.getdir("install_directory"), "logs/error_log"))
            os.remove(os.path.join(self.conf.getdir("install_directory"), "logs/access_log"))

    @property
    def env(self) -> dict:  # pylint: disable=no-self-use
        """
        The environment variables to use when running process
        """
        _env_ = os.environ.copy()
        _env_["APACHE_RUN_USER"] = _env_["USER"]
        _env_["APACHE_RUN_GROUP"] = _env_["USER"]
        return _env_

    @property
    def delay(self) -> int:
        """
        A delay of 2 should be sufficient for all apache's instance
        """
        return 2

    @property
    def named_helper_args(self) -> dict:
        """
        Adds the listening port and the number of iteration to do to the arguments passed to the helper
        """
        return {
            "port": self.conf["listening_port"],
            "iterations": 1000
        }

    @property
    def helper(self) -> UrlFetcherHelper:
        """
        By default, triggering apache's bug is done with the UrlFetcherHelper
        """
        return UrlFetcherHelper

    def check_success(self, *args, **kwargs) -> int:
        """
        Checks in the error log for the string we expect
        :param args: other arguments
        :param kwargs: other keyword arguments
        :return: 0|1|None on success|Failure|unexpected error
        """
        if not os.path.exists(os.path.join(self.conf.getdir("install_directory"), "logs/error_log")):
            return 0

        with open(os.path.join(self.conf.getdir("install_directory"), "logs/error_log")) as error_log:
            for line in error_log:
                if re.match(self.error_pattern, line):
                    logging.debug(line)
                    logging.debug("Found the pattern in apache's error log")
                    return 1

        logging.debug("No error pattern in apache's error log")
        return 0

    def run(self) -> int:
        """
        clean apache's log before calling it's parent run function and returning its value
        :return 0|1|None on success|failure|unexpected failure
        """
        self.clean_logs()
        return super().run()
