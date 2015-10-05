#!/usr/bin/env python3
# coding=utf-8

"""
A plugin to run a benchmark on top of another plugin, for comparison
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"

import os
import statistics

from lib.parsers.configuration import get_global_conf
from lib.plugins import AnalysisPlugin, MainPlugin
from lib.trigger import RawTrigger


class Benchmark(AnalysisPlugin):
    """
    The Benchmark plugin. Changes the trigger to be a Benchmark instance and runs it
    """
    help = "Benchmark the execution"
    benchmark_log = os.path.join(get_global_conf().getdir("trigger", "exp-results"), "benchmark.log")

    @classmethod
    def options(cls) -> str:
        """
        The options to launch the benchmark
        :return:
        """
        return ["-b", "--benchmark"]

    def pre_trigger_run(self, trigger: RawTrigger, *args, **kwargs) -> None:
        """
        initiates a benchmark instance, and modifies the trigger run callable by the trigger one
        :param trigger: the trigger instance to be run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        # noinspection PyCallingNonCallable
        benchmark = trigger.benchmark(trigger)
        benchmark.pre_benchmark_run()
        trigger.run = benchmark.run

    def post_trigger_run(self, trigger: RawTrigger, main_plugin: MainPlugin, *args, **kwargs) -> None:
        """
        Collects the benchmark results and saves them in a file
        :param trigger: the trigger instance that is run
        :param main_plugin: the main plugin under which we run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        if len(trigger.returned_information) == 1:
            mean = trigger.returned_information[0]
            stdev = 0
            variance = 0
        else:
            mean = statistics.mean(trigger.returned_information)
            stdev = statistics.stdev(trigger.returned_information)
            variance = statistics.variance(trigger.returned_information)

        if not os.path.exists(os.path.dirname(self.benchmark_log)):
            os.makedirs(os.path.dirname(self.benchmark_log))

        with open(self.benchmark_log, "a") as logs:
            logs.write("{name}, {plugin}, {slice_size}, {mean}, {stdev}, {variance} {total_numbers}\n".format(
                name=trigger.conf.get("name"),
                plugin=main_plugin.__class__.__name__,
                slice_size=kwargs.get("number", None),
                mean=mean,
                stdev=stdev,
                variance=variance,
                total_numbers=" ".join([str(data) for data in trigger.returned_information])))
