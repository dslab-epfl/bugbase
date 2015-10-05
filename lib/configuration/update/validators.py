#!/usr/bin/env python
# coding=utf-8

"""
Common answer validators, to prevent misconfiguration
"""


import os
import re


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


def validate_multiple_choice(answer: str, answer_list: list) -> (bool, str):
    """
    Checks if an answer is in the given list, or if a number corresponding to an index was given. Returns it
    :param answer: the answer to check
    :param answer_list: the list of answers available
    :return: True, answer if correct, False, None otherwise
    """
    if answer in answer_list:
        return True, answer
    else:
        try:
            return True, answer_list[int(answer)]
        except (ValueError, IndexError):
            return False, None


def validate_closed_question(answer: str) -> (bool, str):
    """
    A validator for closed questions
    :param answer: the given answer
    :return: True, answer if the answer is correct, False, None else
    """
    valid_answers = {
        "y": True,
        "yes": True,
        "1": True,
        "true": True,
        "n": False,
        "no": False,
        "0": False,
        "false": False
    }

    if answer.lower() in valid_answers:
        return True, valid_answers[answer.lower()]
    return False, None


def validate_string_question(answer: str) -> (bool, str):
    """
    Validates that the answer is indeed a non-empty string
    :param answer: the answer
    :return: True, answer if ok, False, None else
    """
    if answer:
        return True, answer
    return False, None


def validate_git_url(answer: str) -> (bool, str):
    """
    Validates that the answer starts with a protocol accepted by git or ""
    :param answer: the answer
    :return: True, answer if ok, False, None else
    """
    if answer == "":  # This is needed to allow the user to finish the sequence
        return True, answer
    elif answer.startswith("http://") or answer.startswith("https://"):
        return True, answer
    elif re.match(r"^.+:.+$", answer):  # for ssh git repositories
        return True, answer
    else:
        directory = os.path.expandvars(os.path.expanduser(answer))  # for local git repositories
        if os.path.isdir(directory) and os.path.isdir(os.path.join(directory, ".git")):
            return True, answer
        return False, None


def validate_add_remove_question(answer: str) -> (bool, str):
    """
    Validates an [Add/Remove] question

    :param answer: the answer
    :return: True, answer if ok, False, None else
    """
    valid_answers = {
        "": "",  # This is needed to allow user to finish the sequence
        "a": "a",
        "add": "a",
        "r": "r",
        "remove": "r"
    }
    if answer.lower() in valid_answers:
        return True, str(valid_answers[answer.lower()])
    return False, None
