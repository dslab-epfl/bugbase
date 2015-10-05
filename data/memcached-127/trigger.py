#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script triggers a bug in memcached (#127).
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


from contextlib import suppress
import os
import memcache

from lib.trigger import TriggerWithHelper, BaseHelper


class Helper(BaseHelper):
    """
    Memcached specific helper, using python's memcache library and connecting to the server, then iterating a certain
    number of time before returning the result
    """
    class MemcachedManager:
        """
        ContextManager for opening a client at entrance and disconnecting it at exit
        """
        def __init__(self, url):
            self.url = url
            self.client = None

        def __enter__(self):
            self.client = memcache.Client([self.url])
            return self.client

        # noinspection PyUnusedLocal
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.client.disconnect_all()

    def __init__(self, key, iterations, results):
        super().__init__()
        self.url = "127.0.0.1:11211"
        self.key = key
        self.results = results
        self.iterations = iterations

        with self.MemcachedManager(self.url) as client:
            client.set(key, 0)

    def run(self):
        """
        Runs self.iterations times an increment then reports the result and exits
        """
        with self.MemcachedManager(self.url) as client:
            for i in range(self.iterations):
                with suppress(ValueError):
                    client.incr(self.key)
            self.results.put(client.get(self.key))


class Trigger(TriggerWithHelper):
    """
    The trigger implementation for memcached
    """
    def __init__(self):
        super().__init__()
        self.__named_helper_args__ = {"iterations": 200}
        self.benchmark.pre_benchmark_run = self.pre_benchmark_run

    @property
    def program(self) -> str:
        """
        The program name : memcached-127
        """
        return "memcached-127"

    @property
    def start_cmd(self) -> str:
        """
        The start command has to append -u root if the program is run as root
        """
        command = "{} -t 2".format(self.conf.get_executable())
        if os.getuid() == 0:
            command += " -u root"

        return command

    @property
    def stop_cmd(self) -> str:
        """
        Sends kill signal to memcached
        """
        return "pkill memcached"

    @property
    def delay(self) -> int:
        """
        The delay to wait until memcached is up
        """
        return 2

    @property
    def helper_commands(self) -> list:
        """
        Commands to pass to the helpers to trigger the bug
        """
        return ["test"] * 2

    @property
    def helper(self) -> Helper:
        """
        Gets the memcached specific helper
        """
        return Helper

    @property
    def named_helper_args(self) -> dict:
        """
        redefines the helper args, which is the number of iterations to run
        """
        return self.__named_helper_args__

    def check_success(self, results: list, **kwargs) -> int:
        """
        Checks that all helpers have a results, which means no one failed, and checks that at least one helper had the
        expected number. Due to concurrency, all helpers may not have the last number
        :param results: the list of threads results
        :param kwargs: additional keyword arguments
        :return: 0|1|None on success|failure|unexpected result
        """
        if None in results:
            return 1
        if self.named_helper_args["iterations"] * 2 not in results:
            return None

        return 0

    def pre_benchmark_run(self):
        """
        Updates the number of iteration to last about 10 seconds instead of 1 for more precise benchmarking
        """
        self.__named_helper_args__["iterations"] = 200000
