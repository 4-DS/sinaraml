#!/usr/bin/env python3

import argparse
import logging
from .server import SinaraServer
from .model import SinaraModel

from .plugin_loader import SinaraPluginLoader

def init_cli(root_parser, subject_parser):
    overloaded_modules = []
    for infra_plugin in SinaraPluginLoader.get_infra_plugins():
        module = SinaraPluginLoader.get_infra_plugin(infra_plugin)
        for plugin_class in module.get_plugin_classes():
            print(plugin_class.__name__)
            for base in plugin_class.__bases__:
                print(base.__name__)
                overloaded_modules.append(base.__name__)
            plugin_class.add_command_handlers(subject_parser)

    if not 'SinaraServer' in overloaded_modules:
        SinaraServer.add_command_handlers(root_parser, subject_parser)
    if not 'SinaraModel' in overloaded_modules:
        SinaraModel.add_command_handlers(subject_parser)

def setup_logging(use_vebose=False):
    logging.basicConfig(format="%(levelname)s: %(message)s")
    if use_vebose:
        logging.getLogger().setLevel(logging.DEBUG)

def get_cli_version():
    try:
        from ._version import __version__
        return __version__
    except Exception as e:
        logging.info(e)
    return 'unknown'

def main():

    exit_code = -1

    # add root parser and root subcommand parser (subject)
    parser = argparse.ArgumentParser()
    subject_subparser = parser.add_subparsers(title='subject', dest='subject', help=f"subject to use")
    parser.add_argument('-v', '--verbose', action='store_true', help="display verbose logs")
    parser.add_argument('--version', action='version', version=f"SinaraML CLI {get_cli_version()}")

    # each cli plugin adds and manages subcommand handlers (starting from subject handler) to root parser
    init_cli(parser, subject_subparser)

    # parse the command line and get all arguments
    args = parser.parse_known_args()[0]

    # Setup logs format and verbosity level
    setup_logging(args.verbose)
    
    # display help if required arguments are missing
    if not args.subject:
        parser.print_help()
    elif not args.action:
        subparsers_actions = [
            action for action in parser._actions 
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                if args.subject == choice:
                    print(subparser.format_help())

    # call appropriate handler for the whole command line from a cli plugin if installed
    if hasattr(args, 'func'):
        try:
            args.func(args)
            exit_code = 0
        except Exception as e:
            if args.verbose:
                logging.exception(e)
            else:
                logging.error(e)
    
    return exit_code

if __name__ == "__main__":
    main()