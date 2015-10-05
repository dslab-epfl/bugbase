#!/usr/bin/env python
# coding=utf-8
# pylint: disable=missing-docstring

"""
Tests for question formatter
"""


from lib import constants

from lib.configuration.update import validate_multiple_choice, validate_closed_question, validate_string_question, \
    validate_git_url, validate_add_remove_question

from tests.unit_tests import UnitTest


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


class AnswerValidatorMCQTest(UnitTest):
    def test_mcq_invalid_answer(self):
        answer = validate_multiple_choice("n", ["a", "b", "c"])
        self.assertEqual(answer, (False, None))

    def test_mcq_valid_answer(self):
        answer = validate_multiple_choice("y", ["x", "y", "z"])
        self.assertEqual(answer, (True, "y"))

    def test_mcq_numeric_answer(self):
        answer = validate_multiple_choice("1", ["a", "b", "c"])
        self.assertEqual(answer, (True, "b"))


class AnswerValidatorClosedTest(UnitTest):
    def helper(self, answers: list):
        for answer in [(answers[0], True), (answers[1], False)]:
            self.assertEqual(validate_closed_question(str(answer[0])), (True, answer[1]))

    def test_numeric_answer(self):
        self.helper([1, 0])

    def test_boolean_answer(self):
        self.helper(["true", "false"])

    def test_short_answer(self):
        self.helper(["y", "n"])

    def test_long_answer(self):
        self.helper(["yes", "no"])

    def test_upper_case(self):
        self.helper(["YES", "NO"])

    def test_non_existing(self):
        self.assertEqual(validate_closed_question("goat"), (False, None))


class StringValidatorTest(UnitTest):
    def test_empty_string(self):
        self.assertEqual(validate_string_question(""), (False, None))

    def test_other_string(self):
        self.assertEqual(validate_string_question("non empty"), (True, "non empty"))


class GitUrlTest(UnitTest):
    def test_empty_url(self):
        """ This is needed to allow the user to finish the sequence """
        self.assertEqual(validate_git_url(""), (True, ""))

    def test_http_url(self):
        url = "http://goaty.org"
        self.assertEqual(validate_git_url(url), (True, url))

    def test_https_url(self):
        url = "https://secret-goatsy.org"
        self.assertEqual(validate_git_url(url), (True, url))

    def test_ssh_url(self):
        url = "user@git.com:goat"
        self.assertEqual(validate_git_url(url), (True, url))

    def test_local_git(self):
        url = constants.ROOT_PATH
        self.assertEqual(validate_git_url(url), (True, url))

    def test_invalid_ssh_url(self):
        url = "git@git.com/goatsy"
        self.assertEqual(validate_git_url(url), (False, None))


class AddRemoveValidatorTest(UnitTest):
    def helper(self, answers: list):
        for answer in [(answers[0], "a"), (answers[1], "r")]:
            self.assertEqual(validate_add_remove_question(answer[0]), (True, answer[1]))

    def test_empty_answer(self):
        """ This is needed to finish the sequence """
        self.assertEqual(validate_add_remove_question(""), (True, ""))

    def test_abbreviation(self):
        self.helper(["a", "r"])

    def test_full(self):
        self.helper(["add", "remove"])

    def test_uppercase(self):
        self.helper(["ADD", "REMOVE"])

    def test_invalid(self):
        self.assertEqual(validate_add_remove_question("b"), (False, None))
