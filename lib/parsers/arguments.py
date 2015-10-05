#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
These are simple useful argument parsers that may be of use for scripts in bugbase
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


# noinspection PyProtectedMember
from argparse import ArgumentParser, _SubParsersAction, Namespace
import collections
from gettext import gettext as _
import itertools
import logging


class SmartArgumentParser(ArgumentParser):
    """
    An ArgumentParser that is able to parse any argument non-matched by the _SubParserAction it has.
    """
    def parse_args(self, args: list=None, namespace: Namespace=None) -> Namespace:
        """
        Parses the arguments and returns them.

        :param args: arguments list to parse
        :param namespace: the namespace in which to add the arguments
        :raise ArgumentError if an argument was not matched
        :return the parsed arguments
        """
        args, argv = self.parse_known_args(args, namespace)

        if not argv:
            return args

        # save old actions, before rerunning the parser without the _SubParsersActions
        _old_actions = self._actions.copy()
        self._actions = [action for action in _old_actions if not isinstance(action, _SubParsersAction)]

        # parse the remaining command line
        args2, argv2 = self.parse_known_args(argv, None)

        self._actions = _old_actions.copy()

        if argv2:
            msg = _('unrecognized arguments: %s')
            self.error(msg % ' '.join(argv2))

        for key, value in vars(args2).items():
            if isinstance(value, collections.Iterable):
                setattr(args, key, [value for value in itertools.chain(getattr(args, key), value)])

        return args


def get_verbosity_parser() -> ArgumentParser:
    """
    Simple mutually exclusive logging level argument parser
    :return: argparse.ArgumentParser instance containing multiple logging levels
    """
    verbosity_parser = ArgumentParser(add_help=False)

    __logging_args__ = verbosity_parser.add_mutually_exclusive_group()
    __logging_args__.set_defaults(logging_level=logging.INFO)

    __logging_args__.add_argument(
        "-v", "--verbose", help="show really all information, this might be too much",
        action="store_const", const=logging.VERBOSE, dest="logging_level")

    __logging_args__.add_argument(
        "-d", "--debug", help="show all progress information",
        action="store_const", const=logging.DEBUG, dest="logging_level")

    __logging_args__.add_argument(
        "-q", "--quiet", help="show only critical information",
        action="store_const", const=logging.ERROR, dest="logging_level")

    return verbosity_parser
