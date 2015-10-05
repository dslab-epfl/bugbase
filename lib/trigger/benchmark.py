#!/usr/bin/env python3
# coding=utf-8

"""
Benchmark helper for triggers. Each benchmark is linked to a trigger class from lib.trigger
"""

from abc import abstractmethod, ABCMeta
from contextlib import suppress
import logging
import multiprocessing
import os
import subprocess
import timeit
import time

from lib.helper import launch_and_log, show_progress
from lib.parsers.configuration import get_global_conf

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class RawBenchmark(metaclass=ABCMeta):
    """
    The base benchmarking class. Defines the bare minimum to run the benchmarks
    """
    def __init__(self, trigger):
        self.trigger = trigger

    @abstractmethod
    def run(self, *args, **kwargs) -> int:
        """
        Called to run the benchmark
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|failure|unexpected ending
        """
        pass

    # noinspection PyMethodMayBeStatic
    def pre_benchmark_run(self) -> None:
        """
        Is called before the benchmark is run in order to setup things if needed (changing command line, etc)
        """
        pass

    @property
    def expected_results(self) -> int:
        """ The number of positive results awaited """
        return get_global_conf().getint("benchmark", "wanted_results")

    @property
    def maximum_tries(self) -> int:
        """ The maximum number of tries to do before declaring a failure """
        return get_global_conf().getint("benchmark", "maximum_tries")

    @property
    def kept_runs(self) -> int:
        """ The total number of run kept """
        return get_global_conf().getint("benchmark", "kept_runs")


class BaseBenchmark(RawBenchmark):
    """
    Basic benchmarking class for program that require nothing external to trigger
    """
    def benchmark_helper(self) -> None:
        """
        Launches the trigger command
        :raise subprocess.CalledProcessError
        """
        subprocess.check_call(self.trigger.cmd.split(" "), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def run(self, *args, **kwargs) -> int:
        """
        Benchmarks the execution 20 times and stores the last 10 results (to avoid side effects) in self.trigger.result.
        Runs at most 100 times before deciding the run is a failure.
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|1 on success|failure
        """
        logging.verbose(self.trigger.cmd)
        results = []
        tries = 0
        while len(results) < self.expected_results and tries < self.maximum_tries:
            try:
                results += timeit.repeat(self.benchmark_helper, repeat=1, number=1)
            except subprocess.CalledProcessError:
                logging.warning("A trigger failed, retrying one more time")
            tries += 1

            show_progress(len(results), self.expected_results, section="trigger")

        if tries >= 100:
            # We failed in 100 iterations
            return 1

        logging.verbose("Run times : %(time)s secs", dict(time=results))
        self.trigger.returned_information = results[self.expected_results - self.kept_runs:]
        return 0


class BenchmarkWithHelper(RawBenchmark):
    """
    Benchmarking class for program with a client-server scheme
    """
    def __init__(self, trigger) -> None:
        super().__init__(trigger)
        self.triggers = []

    def client_run(self) -> None:
        """
        Launches all client threads and waits for them to finish
        :trigger lib.trigger.RawTrigger
        """
        for thread in self.triggers:
            thread.start()

        for thread in self.triggers:
            thread.join()

    def run(self, *args, **kwargs) -> int:
        """
        Benchmarks the execution time of 20 runs and stores the last 10 results (to avoid side effects) in
        self.trigger.result.
        Runs at most 100 times before deciding the run is a failure.
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: 0|1 on success|failure
        """
        results = []
        tries = 0

        while len(results) < self.expected_results and tries < self.maximum_tries:
            tries += 1
            try:
                proc_start = self.trigger.Server(self.trigger.cmd)
                proc_start.start()

                time.sleep(self.trigger.delay)
                results_queue = multiprocessing.Queue()  # pylint: disable=no-member

                self.triggers = []
                for command in self.trigger.helper_commands:
                    self.triggers.append(
                        self.trigger.helper(command, results=results_queue, **self.trigger.named_helper_args)
                    )

                result = timeit.repeat(self.client_run, number=1, repeat=1)
            finally:
                with suppress(subprocess.CalledProcessError):
                    launch_and_log(self.trigger.stop_cmd.split(" "))

                for thread in self.triggers:
                    thread.terminate()

            values = []
            for _ in self.triggers:
                values.append(results_queue.get_nowait())

            if self.trigger.check_success(values) != 0:
                logging.warning("Trigger did not work, retrying")
                continue

            results += result

            show_progress(len(results), self.expected_results, section="trigger")

            time.sleep(2)

        if tries >= 100:
            return 1

        logging.verbose("Run times : {} secs".format(results))
        self.trigger.returned_information = results[self.expected_results - self.kept_runs:]
        return 0


class ApacheBenchmark(RawBenchmark):
    """
    Benchmarking class specific to Apache, using apache-bench utility
    """
    def run(self, *args, run_number: int=0, **kwargs) -> int:
        """
        Benchmarks the number of requests per second an apache server can handle
        Runs at most 100 times before deciding the run is a failure
        :param args: additional arguments
        :param run_number: the number of time the benchmark has run
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|failure|unexpected result
        """
        proc_start = self.trigger.Server(self.trigger.cmd)
        proc_start.start()

        time.sleep(self.trigger.delay)
        cmd = "ab -n 30000 -c 1 {}".format(self.trigger.benchmark_url).split(" ")
        logging.verbose(cmd)

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, **kwargs)
        except subprocess.CalledProcessError as exc:
            for line in exc.output.decode().split("\n"):
                logging.debug(line)

            return self.retry(*args, run_number=run_number, **kwargs)

        else:
            success = self.trigger.check_success()
            if success:
                return self.retry(*args, run_number=run_number, **kwargs)

            self.trigger.result = []
            for line in output.decode().split("\n"):
                if line.startswith("Requests per second:"):
                    self.trigger.returned_information = [float(line.split(":")[1].strip().split(" ")[0])]

            with suppress(subprocess.CalledProcessError):
                launch_and_log(self.trigger.stop_cmd.split(" "))

            if len(self.trigger.returned_information) == 0:
                return self.retry(*args, run_number=run_number, **kwargs)

        logging.verbose("Requests per second : {}".format(self.trigger.returned_information[0]))

        return success

    def retry(self, *args, run_number: int=0, **kwargs) -> int:
        """
        Updates the number of time the program has run and relaunches it

        :param args: additional arguments
        :param run_number: the number of time the benchmark has run
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|failure|unexpected result
        """
        with suppress(subprocess.CalledProcessError):
            launch_and_log(self.trigger.stop_cmd.split(" "))

            with suppress(FileNotFoundError), \
                    open(os.path.join(self.trigger.conf.getdir("install", "install_directory"))) as httpd_pid:
                pid = int(httpd_pid.read())
                launch_and_log(["kill", str(pid)])

        run_number += 1
        if run_number > self.maximum_tries:
            return 1

        logging.warning("An error occurred while launching apache, retrying")

        self.trigger.clean_logs()
        return self.run(*args, run_number=run_number, **kwargs)
