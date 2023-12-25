#!/usr/bin/env python3

import argparse
import logging
from .server import SinaraServer
from .model import SinaraModel

def init_cli(root_parser):
    SinaraServer.add_command_handlers(root_parser)
    SinaraModel.add_command_handlers(root_parser)

def setup_logging(use_vebose=False):
    logging.basicConfig(format="%(levelname)s: %(message)s")
    if use_vebose:
        logging.getLogger().setLevel(logging.DEBUG)

def main():

    exit_code = -1

    # add root parser and root subcommand parser (subject)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subject', dest='subject', help=f"subject to use")
    parser.add_argument('-v', '--verbose', action='store_true', help="display verbose logs")

    # each cli plugin adds and manages subcommand handlers (starting from subject handler) to root parser
    init_cli(subparsers)

    # parse the command line and get all arguments
    args = parser.parse_args()

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
            logging.exception(e)
    
    return exit_code

if __name__ == "__main__":
    main()