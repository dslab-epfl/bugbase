#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This scripts is a script to use to install dependencies of programs
"""

from abc import abstractmethod, ABCMeta
import logging
import platform
import subprocess

from lib.helper import launch_and_log_as_root
from lib.exceptions import DistributionNotSupportedException
from lib.installer.context_managers import FileLock


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class DependenciesInstaller(metaclass=ABCMeta):
    """
    A base installer for dependencies required by bugbase or its programs. One subclass per supported distribution
    should be made
    """
    def __init__(self, packages):
        self.packages = packages

    @staticmethod  # pragma nocover
    @abstractmethod
    def get_missing_packages(packages: list) -> list:
        """
        Checks for packages if they are already installed or not. Returns all packages to install.
        :param packages: the packages required
        :return: List of packages not installed
        """

    @staticmethod  # pragma nocover
    @abstractmethod
    def install(packages: list) -> None:
        """
        Install the given packages using the package manager of the host os
        :param packages: list of packages to install
        """

    @staticmethod  # pragma nocover
    @abstractmethod
    def update_sources() -> None:
        """
        Updates the sources of the distribution. This might help if we cannot download some packages, especially on
        apt-based distributions
        :raise subprocess.CalledProcessError
        """

    @staticmethod
    def factory(packages: list):
        """
        Factory to get the correct dependency installer for the distribution
        :param packages: the packages to install
        :return: subclass of DependenciesInstaller
        :raise DistributionNotSupportedException
        """
        distribution = platform.dist()[0]
        if distribution in ["Ubuntu", "debian"]:
            return AptBasedInstaller(packages)
        else:
            raise DistributionNotSupportedException(distribution)

    def run(self) -> None:
        """
        Gets the correct installer, and install the missing packages
        """
        missing = self.get_missing_packages(self.packages)

        if not len(missing):
            return

        with FileLock("/tmp/.bugbase_lock_deps"):
            try:
                self.install(missing)
            except subprocess.CalledProcessError:
                logging.warning(
                    "An error occurred while installing dependencies. Trying to update sources and reinstall"
                )
                try:
                    self.update_sources()
                    self.install(missing)
                except subprocess.CalledProcessError:
                    logging.fatal(
                        "An error occurred while installing packages. Please install manually :\n\t%(packages)s\n",
                        dict(packages="\n\t".join(missing))
                    )
                    raise


class AptBasedInstaller(DependenciesInstaller):
    """
    An installer for Apt-based distribution.
    Does not support Debian for now, as some packages are not in the repositories
    """
    @staticmethod
    def get_missing_packages(packages: list) -> list:
        """
        Checks the system for all packages not installed from the given list
        :param packages: the packages for which to search
        :return: all non installed packaged from the packages list
        """
        output = subprocess.check_output(["apt-cache", "policy"] + packages, stderr=subprocess.STDOUT)
        packages_info = output.decode("UTF-8")

        missing_dependencies = []

        for package in packages:
            index = packages_info.find(package)
            if packages_info[index:index+len(package) + 21].endswith("Installed: (none)"):
                missing_dependencies.append(package)

            if index == -1:
                logging.error("Could not find %(package)s in the repository", dict(package=package))

        return missing_dependencies

    @staticmethod
    def install(packages: list) -> None:
        """
        Installs the packages with an apt-enable system
        :param packages: the packages to install
        """
        logging.info("Will now install missing packages : %(packages)s", dict(packages=" ".join(packages)))
        cmd = ["apt-get", "install", "-y"] + packages
        launch_and_log_as_root(cmd)

    @staticmethod
    def update_sources() -> None:
        """
        Updates the repository sources, as on some OS, having it out of sync may lead to error on installation
        :raise subprocess.CalledProcessError if process fails
        """
        logging.info("Updating apt repositories")
        launch_and_log_as_root(["apt-get", "update"])
