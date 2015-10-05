#!/usr/bin/env python3
# coding=utf-8

"""
Helper functions to handle repetitive tasks
"""

import datetime
import logging
import os
import subprocess

from lib.parsers.configuration import get_global_conf


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class Git:
    """
    A class for managing git commands from python
    """
    def __init__(self, destination_folder, upstream, protocol=None, **kwargs):
        self.destination_folder = destination_folder
        self.upstream = upstream
        self.kwargs = kwargs
        self.protocol = protocol or get_global_conf().get("install", "git_protocol")

        if self.protocol.startswith("http") and self.upstream.startswith("git@github.com"):
            self.upstream = self.upstream.replace("git@github.com:", "https://github.com/")
        elif self.protocol == "ssh" and self.upstream.startswith("https://github.com/"):
            self.upstream = self.upstream.replace("https://github.com/", "git@github.com:")

        if not os.path.exists(os.path.join(destination_folder, ".git")):
            self.init()

    def init(self) -> None:
        """
        creates the folder and initiates the repository, as `git init`

        :raise subprocess.CalledProcessError on error git initiation
        """
        os.makedirs(self.destination_folder)

        launch_and_log(["git", "init"], cwd=self.destination_folder)
        launch_and_log(["git", "remote", "add", "origin", self.upstream], cwd=self.destination_folder)

    def update(self) -> str:
        """
        Updates the git repository

        :raise subprocess.CalledProcessError on error
        :return the output of git update
        """
        try:
            output = launch_and_log(["git", "pull"], cwd=self.destination_folder, **self.kwargs)
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            if exc.returncode == 128:
                logging.warning("Pulling git repo failed, retrying once")
                return launch_and_log(["git", "pull"], **self.kwargs)

        return output

    def update_to_commit(self, commit: str) -> str:
        """
        Changes the repository head to the given commit. Commit can also be a branch

        :param commit: the branch or commit to which to update HEAD
        :raise subprocess.CalledProcessError if the new head does not exist
        :return output of git checkout
        """
        self.update()
        try:
            output = launch_and_log(["git", "checkout", commit], cwd=self.destination_folder)
        except subprocess.CalledProcessError:
            logging.warning("Could not checkout to commit %(commit)s.", dict(commit=commit))
            raise

        else:
            return output


class Svn:
    """
    A class for managing subversion commands from python
    """
    def __init__(self, destination_folder, upstream):
        self.destination_folder = destination_folder
        self.upstream = upstream

        if not os.path.exists(os.path.join(destination_folder, ".svn")):
            self.init()

    def init(self) -> None:
        """ Creates the directory and checks the repository out """
        os.makedirs(os.path.dirname(self.destination_folder), exist_ok=True)

        launch_and_log(
            ["svn", "co", self.upstream, os.path.basename(self.destination_folder)],
            cwd=os.path.dirname(self.destination_folder)
        )

    def update(self) -> None:
        """
        updates the repository to the latest revision

        :raise subprocess.CalledProcessError on error
        """
        launch_and_log(["svn", "up"], cwd=self.destination_folder)

    def update_to_commit(self, commit: str) -> None:
        """
        Changes the repository head to the given commit

        :param commit: the commit to which to update HEAD
        :raise subprocess.CalledProcessError if the new head does not exist
        """
        self.update()
        try:
            launch_and_log(["svn", "update", "-r", commit], cwd=self.destination_folder)
        except subprocess.CalledProcessError:
            logging.warning("Could not checkout to commit %(commit)s", dict(commit=commit))
            raise


def launch_and_log(cmd: list, cwd: str=os.getcwd(), env: dict=os.environ.copy(), error_msg: str=None, **kwargs) -> str:
    """
    Launches a process and logs its output, before raising any error it might have encountered

    :param cmd: the command to launch
    :param cwd: the directory in which the process takes place. Defaults to the current working directory
    :param env: environment variables to use when running the program
    :param error_msg: an error message to add to the error in case of error
    :param kwargs: additional arguments to pass to check_output
    :raise subprocess.CalledProcessError on error
    :return output of given program
    """
    output = None

    try:
        if kwargs.get("shell", False):
            logging.debug(" ".join(cmd))
        else:
            logging.debug(cmd)  # With shell=True, given input is a string

        output = subprocess.check_output(cmd, cwd=cwd, env=env, stderr=subprocess.STDOUT, **kwargs)

    except subprocess.CalledProcessError as exc:
        output = exc.output
        exc.error_msg = error_msg
        raise exc
    else:
        return output.decode()

    finally:
        for line in output.decode().split("\n"):
            logging.debug(line)


def launch_and_log_as_root(cmd, **kwargs) -> None:
    """
    Updates the process to be able de run as root and launches it using launch_and_log

    :param cmd: the command to launch
    :param kwargs: other arguments to send to launch_and_log. See launch_and_log for more information
    :raise subprocess.CalledProcessError on error
    """
    if not subprocess.call(["which", "sudo"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL):
        root_cmd = "sudo"
    else:
        root_cmd = "su"

    # noinspection PyTypeChecker
    launch_and_log(" ".join([root_cmd, "sh", "-c", "\'" + " ".join(cmd) + "\'"]), shell=True, **kwargs)


def show_progress(done: int, total: int, section: str="install") -> None:
    """
    Shows the current status of the run if progress in enabled

    :param done: number of tasks already done
    :param total: total number of tasks to do
    """
    if get_global_conf().getboolean(section, "show_progress"):
        time = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        print("[\x1b[30;1m{time}\x1b[0m] [{done}/{total}]".format(
            time=time, done=done, total=total), end="\r")


def find_source_files(start_directory: str) -> list:
    """
    Finds all C/C++ files in the given directory

    :param start_directory: the directory to walk for C/C++ files
    :return: all C/C++ files found
    """
    return [
        os.path.join(dir_path, _file_)
        for dir_path, _, _files_ in os.walk(start_directory)
        for _file_ in _files_
        if _file_.endswith(".c") or _file_.endswith(".cpp")
    ]
