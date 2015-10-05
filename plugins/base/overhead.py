#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This module is used to compute and report runtime difference between other plugins (compared to the base.success plugin)
"""


# noinspection PyProtectedMember
from argparse import _SubParsersAction
import math
import random

from lib import get_subclasses
from lib.exceptions import MissingDependency
from lib.plugins import MetaPlugin, MainPlugin
from plugins.base.benchmark import Benchmark
from plugins.base.success import Success


try:
    import matplotlib
    matplotlib.use('Agg')  # this is required in a GUI-less environment
    import matplotlib.pyplot
    import matplotlib.patches
except ImportError:
    matplotlib = None

try:
    import numpy
except ImportError:
    numpy = None


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class Overhead(MetaPlugin):
    """
    This plugin allows to run instrumented runs and compare time spent against a normal run
    """
    help = "A trigger to automatically measure overhead of other plugins"
    available_plugins = {}
    required = Benchmark

    def __init__(self):
        super().__init__()
        self.graph_destination = None

    @classmethod
    def register_for_trigger(cls, subparser: _SubParsersAction, *args, **kwargs):
        """
        Registers for the trigger, add option to specify a number when selecting the plugin
        :param subparser: the parser to use
        :param args: additional arguments to pass to parents
        :param kwargs: additional keyword arguments to pass to parents
        """
        for plugin in get_subclasses(MainPlugin):
            if plugin == Success:
                continue
            cls.available_plugins[str(plugin).rsplit(".", 1)[1].rstrip("'>").lower()] = plugin()

        parser = super().register_for_trigger(subparser, *args, **kwargs)
        parser.add_argument(
            "-p", "--plugin", action="append", help="the bug to benchmark. Can be used multiple times",
            dest="overhead_plugins", required=True, choices=[plugin for plugin in cls.available_plugins]
        )
        parser.add_argument(
            "-g", "--graph", dest="graph_destination",
            help="Generate a overhead report as a graph (you will need matplotlib for this)"
        )

    def before_run(self, overhead_plugins, analysis_plugins, graph_destination, *args, **kwargs):
        """
        Checks that all dependencies are met and sets up plugins

        :param overhead_plugins: list of plugins for which to run main
        :param analysis_plugins: analysis plugins to enable
        :param graph_destination: where to store the graph
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        :return: dict containing main_plugins and analysis_plugins
        """
        if graph_destination:
            if not matplotlib:
                raise MissingDependency("matplotlib", python_module=True)
            elif not numpy:
                raise MissingDependency("numpy", python_module=True)
            self.graph_destination = graph_destination

        if analysis_plugins is None:
            analysis_plugins = [Benchmark]
        elif Benchmark in analysis_plugins:
            pass
        else:
            analysis_plugins.append(Benchmark)
        return {
            "main_plugins": [self.available_plugins[plugin_name] for plugin_name in overhead_plugins] + [Success()],
            "analysis_plugins": analysis_plugins
        }

    def after_run(self, plugins, bugs, *args, **kwargs):
        """
        Generates the report for the collected data

        :param plugins: plugins used on the run
        :param bugs: bugs used on the run
        :param args: additional arguments
        :param kwargs: additional keyword arguments
        """
        entries = {}
        plugin_names = [plugin.__class__.__name__ for plugin in plugins]

        # generate the list of entries, using the most up to date ones
        with open(Benchmark.benchmark_log, "r") as _file_:
            for line in _file_.readlines():
                entry = [x.strip() for x in line.split(",")]
                if entry[0] in bugs and entry[1] in plugin_names:
                    plugin_name = entries.get(entry[0], {})
                    plugin_name[entry[1]] = entry[3]
                    entries[entry[0]] = plugin_name

        # generate a report
        report = {}
        for program in entries:
            for plugin in entries[program]:
                if plugin == Success.__name__:
                    continue

                entry = report.get(program, {})
                if program.startswith("apache"):
                    entry[plugin] = float(entries[program][Success.__name__]) / float(entries[program][plugin])
                else:
                    entry[plugin] = float(entries[program][plugin]) / float(entries[program][Success.__name__])

                report[program] = entry

        self.print_report(report)
        if self.graph_destination:
            self.generate_graph(report)

    @staticmethod
    def print_report(report):
        """
        Prints the report to stdout

        :param report: report to print
        """
        programs = set()
        plugins = set()
        for program in report:
            programs.add(program)
            for plugin in report[program]:
                plugins.add(plugin)

        output = "\t\t|"
        for plugin in plugins:
            output += "{:^8}|".format(plugin)

        output += "\n" + "-" * (17 + 9 * len(plugins)) + "\n"

        for program in programs:
            output += program + "\t|"
            for plugin in plugins:
                if report[program].get(plugin, None):
                    output += "{:>8}|".format(str(round(report[program][plugin], 2)))
                else:
                    output += "{:>8}|".format("X")
            output += "\n"

        print(output)

    def generate_graph(self, report):
        """
        Generates a graph from the given report

        :param report: report to use
        """
        if not matplotlib:
            raise MissingDependency("matplotlib", python_module=True)
        elif not numpy:
            raise MissingDependency("numpy", python_module=True)

        width = 0.8
        programs = [key for key in report.keys()]
        plugins = set([plugin for program in programs for plugin in report[program]])
        indices = numpy.arange(len(programs))
        highest_point = max([report[program][plugin] for program in programs for plugin in report[program]])
        lowest_point = min([report[program][plugin] for program in programs for plugin in report[program]])

        fig, ax = matplotlib.pyplot.subplots(figsize=(10, 5))

        graph_number = 0
        legends = []
        for plugin in plugins:
            color = "#%06x" % random.randint(0, 0xFFFFFF)
            entries = [report[program].get(plugin, 1) - 1 for program in report.keys()]
            values = ax.bar(indices + (graph_number * width / len(plugins)), entries, width / len(plugins), color=color)
            legends.append(matplotlib.patches.Patch(color=color, label=plugin))

            counter = 0
            for program in report.keys():
                if not report[program].get(plugin, None):
                    ax.text(
                        values[counter].get_x() + values[counter].get_width()/2, 0, "Not applicable",
                        rotation=90, size=20, color=color, ha="center", va="bottom"
                    )
                counter += 1

            graph_number += 1

        fig.legend(
            handles=legends,
            labels=[legend.get_label() for legend in legends],
            ncol=len(plugins), bbox_to_anchor=(0.99, .11), prop={'size': 17}
        )

        ax.axis([0, len(programs), math.floor(min(lowest_point + [0]) * 1.1), math.ceil(highest_point * 1.1)])
        ax.set_xticks(indices + (width/2))
        ax.set_xticklabels(programs, size=18, rotation=90)

        matplotlib.pyplot.tight_layout()
        fig.subplots_adjust(bottom=0.47)
        matplotlib.pyplot.savefig(self.graph_destination)
