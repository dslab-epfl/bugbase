#!/usr/bin/env python3
# coding=utf-8

"""
Helpers for trigger requiring client-server operations
"""


from abc import abstractmethod, ABCMeta
from http.client import BadStatusLine, IncompleteRead
import logging
import multiprocessing


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class BaseHelper(multiprocessing.Process, metaclass=ABCMeta):  # pylint: disable=no-member,too-few-public-methods
    """
    The minimum Helper when one is needed
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def run(self) -> None:
        """ The operation to run to trigger the bug """


class UrlFetcherHelper(BaseHelper):  # pylint: disable=too-few-public-methods
    """
    A Helper that fetches a http address in loop
    """
    def __init__(self, url: str, iterations: int=1, **kwargs) -> None:
        """
        Sets up the threading pool and assigns the values to be able to use them later
        :param url: the url to fetch
        :param iterations: how many time to fetch it
        :param kwargs: others arguments to pass. Will be added in formatting the url
        """
        super().__init__()
        self.url = url
        self.iterations = iterations
        self.kwargs = kwargs

    def run(self) -> None:
        """
        Fetches the url given by init a given number of time. Formats each url with the number of iteration as
         {iteration} and adds it the kwargs from init
        """
        import requests
        from requests import exceptions

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        error_counter = 0
        for i in range(self.iterations):
            try:
                requests.get(self.url.format(iteration=i, **self.kwargs))
            except (BadStatusLine, IncompleteRead, ConnectionResetError, requests.exceptions.ChunkedEncodingError,
                    exceptions.ConnectionError):
                error_counter += 1

                if error_counter > 20:
                    break
        return
