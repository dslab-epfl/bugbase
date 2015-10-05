#!/usr/bin/env python3
# coding=utf-8

"""
A module containing installers from various sources
"""

from abc import ABCMeta, abstractmethod
from configparser import SectionProxy
from contextlib import suppress
import logging
import os
import re
import shutil
import tarfile

import requests

from lib import constants, helper
from lib.installer.context_managers import FileLock
from lib.installer.dependency_installer import DependenciesInstaller
from lib.parsers.configuration import get_global_conf, get_compiler_conf


__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"


class Installer:
    """
    This class is an automated installer for programs. See conf/install.conf to know how to format the data to make this
    work
    """
    __metaclass__ = ABCMeta

    def __init__(self, conf: SectionProxy, force_installation: bool) -> None:
        """
        :param conf: the configuration options
        :param force_installation: if the program is installed, will override it
        """
        self.conf = conf
        self.program_path = os.path.join(constants.PROGRAMS_SOURCE_PATH, self.conf["name"])
        self.install_dir = self.conf.getdir("install_directory")
        self.additional_sources_path = os.path.join(self.program_path, "src")
        self.patches_path = os.path.join(self.program_path, "patches")
        self.force_installation = force_installation
        self.env = self.prepare_env()

    @property
    @abstractmethod
    def working_dir(self) -> str:
        """
        The absolute path to the directory where to compile the program
        """

    @property
    @abstractmethod
    def sources_dir(self) -> str:
        """
        The absolute path to where the sources are stored
        """

    @abstractmethod
    def download_sources(self) -> bool:
        """
        Should download the sources needed for the program to be installed

        :return: True if something was downloaded/updated, False otherwise
        """

    @abstractmethod
    def prepare_sources(self) -> None:
        """
        Should prepare the sources and place them in self.working_dir
        """

    @staticmethod
    def factory(conf: SectionProxy, force_installation: bool):
        """
        Parses the configuration and returns the correct Installer
        :param conf: the configuration of the program to install
        :param force_installation: if reinstalling is enabled or not
        :return: an Installer instance
        """
        if "git_repo" in conf:
            return GitInstaller(conf, force_installation)
        elif "svn_repo" in conf:
            return SVNInstaller(conf, force_installation)
        elif conf.get("system_package", False):
            return DependenciesInstaller.factory([conf.get("name")])
        elif conf.getboolean("license", False):
            return LicensedSourceInstaller(conf, force_installation)
        elif conf.get("url", None):
            return DownloadableSourceInstaller(conf, force_installation)
        elif conf.get("source", None):
            return SourceInstaller(conf, force_installation)
        else:
            raise RuntimeError("There was an error while configuring the Installer to use")

    def prepare_env(self) -> dict:
        """
        Sets up the environment depending on the compiler chosen
        :return: the environment to use
        """
        env = os.environ.copy()
        env["PREFIX"] = self.install_dir

        # if we are configuring utilities, stop here, we already have set everything necessary
        if self.conf.getboolean("utility"):
            return env

        compiler_full_name = get_global_conf().get("install", "compiler")
        compiler_package, compiler_name = compiler_full_name.split(".")
        compiler_conf = get_compiler_conf(compiler_package, compiler_name)

        for env_name, env_value in compiler_conf.items("env"):
            if env_name.upper() == "PATH":
                env[env_name.upper()] = "{}:{}".format(env_value, env["PATH"])
            else:
                env[env_name.upper()] = env_value

        env["CFLAGS"] = env.get("CFLAGS", "") + " -g "
        env["CXXFLAGS"] = env.get("CXXFLAGS", "") + " -g "

        if get_global_conf().getboolean("install", "llvm_bitcode"):
            env["PATH"] = "{}:{}".format(
                os.path.join(get_global_conf().getdir("utilities", "install_directory"), "wllvm"),
                env["PATH"]
            )

            env["LLVM_COMPILER"] = "clang"
            env["CC"] = "wllvm"
            env["CXX"] = "wllvm++"
        return env

    def patch(self, patches: list, directory: str, reverse: bool=False, patches_path=None) -> None:
        """
        Applies different patches to the sources or the installed files
        :param patches: list of patches to apply
        :param directory: the top directory where to apply these patches
        :param reverse: if the patch is to be reversed
        :param patches_path: the path where to find the patches. If not set, will use data/program_name/patches
        """
        if not patches:
            return

        for _patch in patches:
            logging.verbose("Applying {}patch {}".format("Reverse " if reverse else "", _patch))
            cmd = ["patch", "-p1", "-i", os.path.join(patches_path or self.patches_path, _patch)]
            if reverse:
                cmd.insert(2, "-R")

            helper.launch_and_log(cmd, cwd=directory, error_msg="A patch failed to apply")

    def configure(self) -> None:
        """
        Configures the sources
        """
        if self.conf["configure"] == "configure":
            cmd = [
                os.path.join(self.sources_dir, "configure"),
                "--prefix={}".format(self.install_dir)
            ]
        elif self.conf["configure"] == "cmake":
            cmd = [
                "cmake",
                self.sources_dir
            ]
        else:
            logging.verbose("{} does not need configuration".format(self.conf["display_name"]))
            return

        cmd += self.conf.getlist("configure_args", [])
        logging.info("Configuring %(name)s", dict(name=self.conf["display_name"]))

        self.env["WLLVM_CONFIGURE_ONLY"] = "1"
        helper.launch_and_log(cmd, cwd=self.working_dir, env=self.env, error_msg="Configuration failed")
        del self.env["WLLVM_CONFIGURE_ONLY"]

    def make(self) -> None:
        """
        runs 'make'
        """
        logging.info("Compiling %(name)s", dict(name=self.conf["display_name"]))
        cmd = ["make"] + get_global_conf().getlist("install", "make_args")
        if self.conf.getlist("make_args", None):
            cmd += self.conf.getlist("make_args")
        helper.launch_and_log(cmd, cwd=self.working_dir, env=self.env, error_msg="Compilation failed")

    def install(self) -> None:
        """
        Runs 'make install'
        """
        logging.info("Installing %(name)s", dict(name=self.conf["display_name"]))
        if self.conf.get("install", None) == "copy":
            shutil.copytree(self.sources_dir, self.install_dir)

        else:
            helper.launch_and_log(
                ["make", "install"], cwd=self.working_dir, env=self.env, error_msg="Installation failed"
            )

    def extract_bitcode(self) -> None:
        """
        Extracts and copies the bitcode file to the bin directory
        """
        logging.info("Copying bitcode file")
        source = os.path.join(self.working_dir, self.conf["bitcode_file"].lstrip("/"))
        cmd = "{}/wllvm/extract-bc {}".format(get_global_conf().getdir("utilities", "install_directory"), source)

        helper.launch_and_log(cmd.split(" "), env=self.env, error_msg="Bitcode extraction failed")

        shutil.copy(source + ".bc", self.install_dir + "/bin/")

    def copy_files(self, _files: list) -> None:
        """
        Copy files to add at the end (configuration files, and so on)
        :param _files: the files to copy
        """
        if not _files:
            return

        logging.verbose("Copying required files")
        for _file in _files:
            name, destination = _file.split("=>")
            shutil.copy2(os.path.join(self.additional_sources_path, name), os.path.join(self.install_dir, destination))
            logging.verbose("Copying " + name + " to " + os.path.join(self.install_dir, destination))

    def run(self) -> None:
        """
        The main program, handles everything
        """
        with suppress(FileNotFoundError):
            shutil.rmtree(self.working_dir)

        with FileLock(os.path.join("/tmp/", "." + self.conf.get("name") + ".build")):
            if not self.download_sources():
                self.force_installation = True

        if os.path.exists(self.install_dir):
            if not self.force_installation:
                logging.warning(
                    "The install directory is not empty. %(name)s will not be installed", dict(name=self.conf["name"])
                )
                return 1
            else:
                logging.verbose(
                    "%(name)s was already installed, removing it before continuing", dict(name=self.conf["name"])
                )
                shutil.rmtree(self.install_dir)

        logging.info("Treating " + self.conf["display_name"])
        self.prepare_sources()

        self.patch(self.conf.getlist("patches_pre_config", []), self.working_dir)

        self.configure()

        self.patch(self.conf.getlist("patches_post_config", []), self.working_dir)

        self.copy_files(self.conf.getlist("copy_post_config", []))

        if self.conf.getboolean("make", True):
            self.make()

        self.install()

        if get_global_conf().getboolean("install", "llvm_bitcode") and ("bitcode_file" in self.conf.keys()):
            self.extract_bitcode()

        self.patch(self.conf.getlist("patches_post_install", []), self.install_dir)

        self.copy_files(self.conf.getlist("copy_post_install", []))

        if os.path.exists(os.path.join(self.patches_path, self.conf["display_name"] + ".patch")):
            self.patch([self.conf["display_name"] + ".patch"], self.working_dir, True)

        logging.info("finished installing %(name)s", dict(name=self.conf["display_name"]))


class GitInstaller(Installer):
    """
    This class is an automated installer for programs under git. See install_conf.py to know how to format the data to
    make this work
    """
    @property
    def working_dir(self) -> str:
        """
        The working directory to use
        """
        return os.path.join(get_global_conf().getdir("install", "build_directory"), self.conf["name"])

    @property
    def sources_dir(self) -> str:
        """
        Where the sources are stored
        """
        return os.path.expanduser(
            os.path.join(get_global_conf().get("install", "source_directory"), self.conf["name"]))

    def download_sources(self) -> bool:
        """ clones the git repository or updates it if it is already there """
        git = helper.Git(self.sources_dir, self.conf["git_repo"])
        output = git.update()

        if "Already up-to-date" in output or "not currently on a branch" in output:
            # if we are not on a branch, we are on a separate commit, we have nothing to update
            return 1

        output = git.update_to_commit(self.conf.get("commit", "master"))

        if "Your branch is up-to-date" in output:
            return 1

    def prepare_sources(self):
        """
        clones the git repo or updates it if it is already there
        """
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)


class SVNInstaller(GitInstaller):
    """
    This class is an automated installer for programs under svn. See install_conf.py to know how to format the data to
    make this work
    """
    def prepare_sources(self):
        """
        Clones the subversion repository or updates it if it is already there
        """
        svn = helper.Svn(self.sources_dir, self.conf["svn_repo"])
        svn.update()
        if self.conf.get("commit", None):
            svn.update_to_commit(self.conf.get("commit"))

        for source in self.conf.getlist("additional_sources", []):
            info = self.conf.getlist(source)
            _svn = helper.Svn(os.path.join(self.sources_dir, info[1], source), info[0])
            _svn.update()

        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)


class SourceInstaller(Installer):
    """
    This class is an installer for program for which we have the sources bundled in bugbase
    """
    @property
    def source_name(self) -> str:
        """ the name of the source """
        return self.conf["source"]

    @property
    def source_storage_path(self) -> str:
        """ where the source is stored """
        return os.path.join(self.additional_sources_path, self.source_name)

    @property
    def working_dir(self) -> str:
        """
        The working directory to use
        """
        return os.path.join(self.extract_dir, self.source_name.replace(".tar.gz", "").replace(".tar.bz2", ""))

    @property
    def sources_dir(self) -> str:
        """
        The directory where the sources are stored
        """
        return self.working_dir

    @property
    def extract_dir(self) -> str:
        """
        The absolute path to the directory where to extract the files
        """
        return os.path.join(get_global_conf().getdir("install", "build_directory"), self.conf["name"])

    def prepare_sources(self) -> None:
        """
        Extracts the file from self.src_path+self.conf["src_name"] to self.extract_dir
        """
        logging.verbose("unpacking file in " + self.extract_dir)
        tar = tarfile.open(self.source_storage_path)
        tar.extractall(self.extract_dir)
        tar.close()

    def download_sources(self) -> bool:
        return True


class DownloadableSourceInstaller(SourceInstaller):
    """
    SourceInstaller that downloads data through http beforehand
    """
    @property
    def source_name(self) -> str:
        """ the name of the source """
        return self.conf["url"].split("/")[-1]

    @property
    def source_storage_path(self) -> str:
        """ where the source is stored """
        return os.path.join(get_global_conf().get("install", "source_directory"), self.conf["name"], self.source_name)

    def download_sources(self) -> bool:
        if os.path.exists(self.source_storage_path):
            return True

        logging.verbose("Downloading %(file)s", dict(file=self.conf["url"]))
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

        response = requests.get(self.conf["url"], stream=True)
        if response.status_code != requests.codes.ok:
            raise response.raise_for_status()

        os.makedirs(os.path.dirname(self.source_storage_path), exist_ok=True)
        with open(self.source_storage_path, "wb") as _file_:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # this is to filter out keepalive chunks
                    _file_.write(chunk)


class LicensedSourceInstaller(SourceInstaller):
    """
    This installer handles cases when a license has to be accepted before the sources are downloaded
    """
    def prepare_sources(self) -> None:
        source_directory = os.path.join(
            get_global_conf().getdir("install", "source_directory"),
            "sources",
            self.conf.get("name")
        )
        os.makedirs(source_directory, exist_ok=True)
        archive_found = [_file_ for _file_ in os.listdir(source_directory) if re.match(self.conf.get("source"), _file_)]

        if not len(archive_found):
            print("You need to accept a license agreement before downloading {}.".format(self.conf.get("name")))
            print(
                "Please go to {} then put the downloaded file in {}/".format(self.conf.get("url"), source_directory)
            )
            input("Please press enter when done")

            archive_found = [
                _file_
                for _file_ in os.listdir(source_directory)
                if re.match(self.conf.get("source"), _file_)
            ]

            if not len(archive_found):
                print("Could not find the archive, please ensures that the name matches", self.conf.get("source"))
                return self.prepare_sources()

        tar = tarfile.open(os.path.join(source_directory, archive_found[0]))
        tar.extractall(self.extract_dir)
        tar.close()
        self.conf["source"] = archive_found[0]
