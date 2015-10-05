#!/usr/bin/env python3
# coding=utf-8

"""
Interface between the plugins and the framework. This is the only calls the framework is allowed to do to call plugins
"""

__author__ = "Benjamin Schubert, benjamin.schubert@epfl.ch"

import importlib

from lib import get_subclasses
from lib.parsers.configuration import get_global_conf
from lib.plugins import BasePlugin, MainPlugin, MetaPlugin


JANITORS = list()


def load_plugins() -> None:
    """
    Loads all enabled plugin modules
    """
    for plugin in get_global_conf().getlist("plugins", "enabled_plugins"):
        importlib.import_module("plugins.{}".format(plugin))


def configure(force: bool) -> None:
    """
    Calls all configure options for enabled plugins
    :param force: True in order to reinstall if it was already installed. If not installed, has no difference
    """
    for plugin in get_subclasses(BasePlugin):
        plugin().configure(force)


def register_for_install(**kwargs) -> None:
    """
    Allows each plugin to register to be called during the installation phases
    :param kwargs: keyword arguments to pass to the plugins
    """
    for plugin in get_subclasses(BasePlugin):
        plugin.register_for_install(**kwargs)


def create_executables(*args, **kwargs) -> None:
    """
    Allows each enabled plugin to create a special executable if needed
    :param args: arguments to pass to plugins
    :param kwargs: keyword arguments to pass to plugins
    """
    for plugin in get_subclasses(MainPlugin):
        plugin().create_executable(*args, **kwargs)


def post_install_run(analysis_plugins=None, **kwargs) -> None:
    """
    Calls analysis_plugins after the installation has succeeded
    :param analysis_plugins: the plugins to call
    :param kwargs: keyword arguments to pass to plugins
    """
    if analysis_plugins is not None:
        for plugin in analysis_plugins:
            plugin().post_install_run(**kwargs)


def post_install_clean(analysis_plugins=None, **kwargs) -> None:
    """
    Runs once the installation is complete. Should be used to remove every files created during installation and not
    useful anymore
    :param analysis_plugins:  the plugins to call
    :param kwargs: keyword arguments to pass to plugins
    """
    if analysis_plugins is not None:
        for plugin in analysis_plugins:
            plugin().post_install_clean(**kwargs)

    for janitor in JANITORS:
        janitor()


def register_for_trigger(**kwargs) -> None:
    """
    Allows each plugin to register to be called during the trigger phases
    :param kwargs: keyword arguments to pass to the plugins
    """
    for plugin in get_subclasses(BasePlugin):
        plugin.register_for_trigger(**kwargs)


def register_for_cleaning(function: callable) -> None:
    """
    Adds a function to be called once cleaning is done
    :param function: the function to call on cleaning
    """
    JANITORS.append(function)


def before_run(main_plugin: MetaPlugin, analysis_plugins=None, **kwargs) -> dict:
    """
    Function called before running, to prepare the plugins to run. Returns a dict constructed as below:
        dict = {
                "main_plugins": list of MainPlugins to run
                "analysis_plugins": list of analysis plugins to use
            }

    :param main_plugin: the MetaPlugin that runs and orchestrate everything
    :param analysis_plugins: the list of already enabled analysis_plugins
    :param kwargs: additional keyword arguments
    :return: a dictionary containing main_plugins and analysis_plugins
    """
    return main_plugin.before_run(analysis_plugins=analysis_plugins, **kwargs)


def after_run(main_plugin: MetaPlugin, analysis_plugins=None, **kwargs) -> int:
    """
    Function call after running, to combine results of the plugins that has run
    :param main_plugin: the MetaPlugin that orchestrates everything
    :param analysis_plugins: the list of analysis_plugins that are enabled
    :param kwargs: additional keyword arguments
    :return: int: 0|Else on success/failure
    """
    return main_plugin.after_run(analysis_plugins=analysis_plugins, **kwargs)


def pre_trigger_run(main_plugin: MainPlugin, analysis_plugins=None, **kwargs) -> None:
    """
    Calls the main plugins and every enabled analysis plugins before running the trigger
    :param main_plugin: the main plugin to run
    :param analysis_plugins: any analysis plugin to stack
    :param kwargs: keyword arguments passed to the plugins
    """
    main_plugin.pre_trigger_run(**kwargs)
    if analysis_plugins is not None:
        for plugin in analysis_plugins:
            plugin().pre_trigger_run(main_plugin=main_plugin, **kwargs)


def check_trigger_success(main_plugin: MainPlugin, **kwargs) -> int:
    """
    Calls the main plugin to check if the trigger was successful or not
    :param main_plugin: the plugin to use
    :param kwargs: keyword arguments to pass to the plugin
    :return: 0|1|None on success|failure|unexpected event
    """
    return main_plugin.check_trigger_success(**kwargs)


def post_trigger_run(main_plugin: MainPlugin, analysis_plugins=None, **kwargs) -> None:
    """
    Calls the main plugins and every enabled analysis plugins after running the trigger
    :param main_plugin: the main plugin to run
    :param analysis_plugins: any analysis plugin to stack
    :param kwargs: keyword arguments passed to the plugins
    """
    main_plugin.post_trigger_run(**kwargs)
    if analysis_plugins is not None:
        for plugin in analysis_plugins:
            plugin().post_trigger_run(main_plugin=main_plugin, **kwargs)


def post_trigger_clean(main_plugin: MainPlugin, analysis_plugins=None, **kwargs):
    """
    Calls the main plugins and every enabled analysis plugins if they need to clean files. Then calls all registered
    JANITORS functions
    :param main_plugin: the main plugin to run
    :param analysis_plugins: any analysis plugin to stack
    :param kwargs: keyword arguments passed to the plugins
    """
    main_plugin.post_trigger_clean(**kwargs)
    if analysis_plugins is not None:
        for plugin in analysis_plugins:
            plugin().post_trigger_clean(main_plugin=main_plugin, **kwargs)

    for janitor in JANITORS:
        janitor()
