#!/usr/bin/env python
# coding=utf-8

"""
Handles configuration updates for Bugbase
"""

from configparser import ExtendedInterpolation
import io
import logging
import os

from lib import constants
from lib.helper import Git
from lib.configuration.update.formatters import format_list_numbered, format_closed_question
from lib.configuration.update.validators import validate_multiple_choice, validate_closed_question,\
    validate_string_question, validate_git_url, validate_add_remove_question
from lib.parsers.configuration import get_global_conf, TypedConfigParser, reload_global_conf


__author__ = 'Benjamin Schubert, ben.c.schubert@gmail.com'


def ask_question(question: str, validate_answers, default: str, **kwargs) -> str:
    """
    Asks a question, validates the answer and returns the result
    :param question: the question to ask
    :param validate_answers: the function to validate the answers
    :param default: the default answer
    :param kwargs: keyword arguments to pass to the answer validator
    :return: the answer
    """
    valid_answer = False
    formatted_answer = None

    while not valid_answer:
        answer = input(question)
        valid_answer, formatted_answer = validate_answers(answer or default, **kwargs)

    return formatted_answer


def show_progress() -> str:
    """
    Asks user whether to show progress on long time running tasks or not

    :return: the answer
    """
    return str(ask_question(
        "Do you want to show progress on long time running tasks ? {}".format(
            format_closed_question(get_global_conf()["DEFAULT"]["show_progress"])),
        validate_answers=validate_closed_question,
        default=get_global_conf()["DEFAULT"]["show_progress"]
    ))


def choose_plugin_repositories(protocol) -> list:
    """
    Allows the user to add custom defined git repository containing plugins

    :return: list of plugins to enable
    """
    repositories = get_global_conf().getlist("plugins", "repositories")

    while True:
        answer = ask_question(
            "Do you want to add or remove plugin repositories ?\nEnabled Repositories :\n\t{}\n"
            "[Add/Remove]. Press enter to keep as is.".format("\n\t".join(format_list_numbered(repositories, ""))),
            validate_answers=validate_add_remove_question,
            default=""
        )

        if answer == "":
            break

        elif answer == "a":
            repo_to_add = ask_question(
                "What git repository do you want to add for plugins ? Hit enter to cancel.\n",
                validate_answers=validate_git_url,
                default=""
            )
            if repo_to_add is not "":
                repositories.append(repo_to_add)  # pylint: disable=no-member

        elif answer == "r":
            repo_to_delete = ask_question(
                "Which repository do you want to remove ? Hit enter to cancel.\n\t{}\n".format(
                    "\n\t".join(format_list_numbered(repositories, ""))
                ),
                validate_answers=validate_multiple_choice,
                default="",
                answer_list=repositories
            )

            repositories.remove(repo_to_delete)  # pylint: disable=no-member

    for repository in repositories:
        repository_name = repository.split("/")[-1].split(".")[0]
        logging.info("Pulling %(repository)s", dict(repository=repository_name))
        repository_directory = os.path.join(constants.PLUGINS_PATH, repository_name)

        git = Git(repository_directory, repository, protocol=protocol)
        git.update_to_commit("master")

    return repositories


def choose_wllvm() -> str:
    """
    Allows the user to choose whether to produce llvm bitcode or not
    :return whether to return wllvm or not
    """
    return str(ask_question(
        "Do you want to produce llvm bitcode from the binaries ? {}".format(
            format_closed_question(get_global_conf().getboolean("install", "llvm_bitcode"))),
        validate_answers=validate_closed_question,
        default=get_global_conf().get("install", "llvm_bitcode")
    ))


def choose_compiler() -> str:
    """
    Allows the user to choose his compiler
    :return: the compiler to use
    """
    compilers = []

    for package in os.listdir(constants.PLUGINS_PATH):
        if os.path.isdir(os.path.join(constants.PLUGINS_PATH, package)):
            compilers_dir = os.path.join(constants.PLUGINS_PATH, package, "compilers")
            if os.path.exists(compilers_dir):
                compilers.extend([
                    "{}.{}".format(package, compiler.split(".")[0])
                    for compiler in os.listdir(compilers_dir)
                ])

    return ask_question(
        "Which compiler do you want to use ?\n\t{}\n".format("\n\t".join(
            format_list_numbered(compilers, get_global_conf().get("install", "compiler")))),
        validate_answers=validate_multiple_choice,
        default=get_global_conf().get("install", "compiler"),
        answer_list=compilers
    )


def choose_module_handling() -> str:
    """
    Choose whether or not to install required python modules automatically or not
    :return whether to handle python modules or not
    """
    return str(ask_question(
        "Do you want the script to automatically install required python modules ? {}".format(
            format_closed_question(get_global_conf().getboolean("install", "module_handling"))),
        validate_answers=validate_closed_question,
        default=get_global_conf().get("install", "module_handling")
    ))


def choose_git_protocol() -> str:
    """
    Choose which protocol to use with git
    :return the protocol to use with git
    """
    return ask_question(
        "WHat protocol do you want to use for git ? \n\t{}\n".format("\n\t".join(
            format_list_numbered(["https", "ssh"], get_global_conf().get("install", "git_protocol")))),
        validate_answers=validate_multiple_choice,
        default=get_global_conf().get("install", "git_protocol"),
        answer_list=["https", "ssh"]
    )


def choose_coredump_pattern() -> str:
    """
    Choose the coredump pattern
    :return the coredump pattern to use
    """
    return ask_question(
        "What coredump pattern do you want ? Default is {}\n".format(
            get_global_conf().get("trigger", "core_dump_pattern")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("trigger", "core_dump_pattern")
    )


def choose_coredump_filter() -> str:
    """
    Choose whether to change the coredump filter and which one to use if so
    :return the coredump filter to use
    """
    return ask_question(
        "What coredump filter do you want ? Default is {}\n".format(
            get_global_conf().get("trigger", "core_dump_filter")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("trigger", "core_dump_filter")
    )


def choose_coredump_location() -> str:
    """
    Choose whether to change the coredump location and which one to use if so
    :return the coredump location to use
    """
    return ask_question(
        "What coredump location do you want ? Default is {}\n".format(
            get_global_conf().get("trigger", "core_dump_location")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("trigger", "core_dump_location")
    )


def choose_build_dir() -> str:
    """
    Choose in which build directory
    :return the build directory to use
    """
    return ask_question(
        "Where do you want to set the build directory ? Default is {}\n".format(
            get_global_conf().get("install", "build_directory")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("install", "build_directory")
    )


def choose_install_dir() -> str:
    """
    Choose in which directory to install programs and utilities
    :return the install director to use
    """
    return ask_question(
        "Where do you want to install programs ? Default is {}\n".format(
            get_global_conf().get("install", "install_directory")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("install", "install_directory")
    )


def choose_source_storage_dir() -> str:
    """
    Choose in which directory to store downloaded sources
    :return the source directory to use
    """
    return ask_question(
        "Where do you want to download sources ? Default is {}\n".format(
            get_global_conf().get("install", "source_directory")),
        validate_answers=validate_string_question,
        default=get_global_conf().get("install", "source_directory")
    )


def choose_make_arguments() -> list:
    """
    Choose which make arguments to add
    :return list of make arguments to send
    """
    return ask_question(
        "What arguments do you want to give to make ? Default is {}\n".format(
            get_global_conf().get("install", "make_args")),
        validate_answers=validate_string_question,
        default=" ".join(get_global_conf().getlist("install", "make_args"))
    ).split(" ")


def choose_plugins_to_enable() -> list:
    """
    Seeks all findable plugins and asks which ones to enable

    :return list of plugins to enable
    """
    plugins_to_enable = list()

    for package in os.listdir(constants.PLUGINS_PATH):
        package_full_path = os.path.join(constants.PLUGINS_PATH, package)
        if not os.path.isdir(package_full_path):
            continue

        for _file_ in os.listdir(package_full_path):
            if _file_.endswith(".py") and _file_ != "__init__.py":
                plugin = "{}.{}".format(package, os.path.splitext(_file_)[0])
                plugin_is_enabled = True if plugin in get_global_conf().get("plugins", "enabled_plugins") else False
                answer = ask_question(
                    "Would you like to enable the {} plugin ? {}".format(
                        plugin, format_closed_question(plugin_is_enabled)
                    ),
                    validate_answers=validate_closed_question,
                    default="y" if plugin_is_enabled else "n"
                )
                if answer:
                    plugins_to_enable.append(plugin)

    return plugins_to_enable


def update_conf(new_conf: TypedConfigParser) -> None:
    """
    Checks the custom conf for anything to update and updates it accordingly
    :param new_conf: the new configuration to create
    """
    old_conf = get_global_conf()
    changed_conf = TypedConfigParser(interpolation=ExtendedInterpolation())

    for section in new_conf.sections():
        differences = set(new_conf.items(section)) ^ set(old_conf.items(section))
        modifications = differences & set(new_conf.items(section))
        if modifications:
            if section not in changed_conf.sections():
                changed_conf.add_section(section)

            for option, value in modifications:
                if TypedConfigParser.LIST_SEPARATOR in value:
                    old_value = set(old_conf.getlist(section, option))
                    new_value = set(new_conf.getlist(section, option))
                    if not old_value ^ new_value:
                        continue

                changed_conf.set(section, option, value)

    # cleanup empty added sections, not to save a new custom conf for nothing
    for section in changed_conf.sections():
        if len(changed_conf.items(section)) == 0:
            changed_conf.remove_section(section)

    if len(changed_conf.sections()):
        custom_conf = TypedConfigParser(interpolation=ExtendedInterpolation())
        custom_conf.read(os.path.join(constants.CONF_PATH, "custom.conf"))

        custom_conf.read_dict(changed_conf)

        try:
            with open(os.path.join(constants.CONF_PATH, "custom.conf"), "w") as config:
                custom_conf.write(config)
        except PermissionError:
            values_to_add = io.StringIO()
            changed_conf.write(values_to_add)
            logging.error(
                "Could not update the config file : Permission Denied.\nPlease add to conf/custom.conf :\n\n%(entry)s",
                dict(entry=values_to_add.getvalue())
            )
            return 1


def update() -> None:
    """
    Asks multiple questions to user to update the configuration then update the custom.conf file
    """
    new_config = TypedConfigParser(interpolation=ExtendedInterpolation())
    new_config.read(os.path.join(constants.CONF_PATH, "default.conf"))
    new_config.read(os.path.join(constants.CONF_PATH, "custom.conf"))

    new_config.set("DEFAULT", "show_progress", show_progress())
    new_config.set("install", "llvm_bitcode", choose_wllvm())
    new_config.set("install", "module_handling", choose_module_handling())
    new_config.set("install", "git_protocol", choose_git_protocol())
    new_config.set("trigger", "core_dump_pattern", choose_coredump_pattern())
    new_config.set("trigger", "core_dump_filter", choose_coredump_filter())
    new_config.set("trigger", "core_dump_location", choose_coredump_location())
    new_config.set("install", "build_directory", choose_build_dir())
    new_config.set("install", "install_directory", choose_install_dir())
    new_config.set("install", "source_directory", choose_source_storage_dir())
    new_config.set("install", "make_args", TypedConfigParser.LIST_SEPARATOR.join(choose_make_arguments()))
    new_config.set("plugins", "repositories", TypedConfigParser.LIST_SEPARATOR.join(choose_plugin_repositories(
        new_config.get("install", "git_protocol")
    )))
    new_config.set("install", "compiler", choose_compiler())
    new_config.set("plugins", "enabled_plugins", TypedConfigParser.LIST_SEPARATOR.join(choose_plugins_to_enable()))

    if not update_conf(new_config):
        reload_global_conf()
    else:
        return 1
