#!/usr/bin/env python3

import argparse
import logging
import platform
import sys
from dataclasses import dataclass
from .org_manager import SinaraOrgManager


@dataclass
class Gitref:
    gitref: str

def check_any_cli_exists():
    if not SinaraOrgManager.check_last_update():
        args = Gitref(gitref = "https://github.com/4-DS/mlops_organization.git")
        SinaraOrgManager.install_from_git(args)
    
def init_cli(root_parser, subject_parser, platform=None):

    root_parser.subjects = []

    SinaraOrgManager.add_command_handlers(root_parser, subject_parser)

    org_name = 'personal'
    if platform and '_' in platform:
        org_name = platform.split('_')[0]
    elif not platform is None:
        org_name = platform
    org = SinaraOrgManager.load_organization(org_name)
    if org:
        org.add_command_handlers(root_parser, subject_parser)
    
def update_orgs():
    for org in SinaraOrgManager.get_orgs():
        from collections import namedtuple
        Args = namedtuple('Args', ['name', 'internal'])
        args = Args(name=org["name"], internal=True)
        SinaraOrgManager.update_org(args)


def setup_logging(use_vebose=False):
    logging.basicConfig(format="%(levelname)s: %(message)s")
    if use_vebose:
        logging.getLogger().setLevel(logging.DEBUG)

def platform_is_supported():
    platform_name = platform.system().lower()
    return platform_name == "linux" or platform_name == "darwin"

def main():

    exit_code = -1

    if not platform_is_supported():
        print(f'Your OS "{platform.system()}" is not supported. Check https://github.com/4-DS/sinara-tutorials/wiki/SinaraML-Known-issues#error-message-your-os-is-not-supported')
        return exit_code

    # add root parser and root subcommand parser (subject)
    parser = argparse.ArgumentParser(add_help=True, allow_abbrev=True)
    subject_subparser = parser.add_subparsers(title='subject', dest='subject', help=f"subject to use")
    parser.add_argument('-v', '--verbose', action='store_true', help="display verbose logs")
    parser.add_argument('-p', '--platform', action="store", help="choose SinaraML platform")
    #parser.add_argument('--version', action='version', version=f"SinaraML CLI {get_cli_version()}")

    sinara_platform = None
    for i in range(1, len(sys.argv)):
        a = sys.argv[i]
        if a.startswith('--platform'):
            sinara_platform = a.split('=')[1] if "=" in a else sys.argv[i+1]
            break
    
    if not sinara_platform:
        check_any_cli_exists()
    update_orgs()
    # each cli plugin adds and manages subcommand handlers (starting from subject handler) to root parser
    init_cli(parser, subject_subparser, platform=sinara_platform)
    

    # parse the command line and get all arguments
    args, unknown = parser.parse_known_args()
    root_args = parser.parse_args(unknown)

    # Setup logs format and verbosity level
    verbose = args.verbose | root_args.verbose
    setup_logging(verbose)
    args.platform = sinara_platform if not sinara_platform is None else 'personal'

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
            #from requests.exceptions import ConnectionError
            if e.__cause__.__class__.__name__ == "ConnectionError":
                logging.error("Docker daemon is not available, make sure docker is running and you have permissions to access it. Run CLI with sinara --verbose flag to see details")

            elif e.__class__.__name__ == "APIError":
                if e.is_client_error():
                    if e.status_code == 404:
                        logging.error(f"Docker image or container not found. Run CLI with sinara --verbose flag to see details")
                    elif e.status_code == 401 or e.status_code == 403:
                        logging.error(f"Make sure you have permissions to access requested resource. Run CLI with sinara --verbose flag to see details")                        
                    else:
                        logging.error("Docker client has failed, Run CLI with sinara --verbose flag to see details")
                else:
                    logging.error("Docker daemon failed, Run CLI with sinara --verbose flag to see details")

            elif e.__class__.__name__ == "DockerException":
                logging.error("Docker client has failed, Run CLI with sinara --verbose flag to see details")

            logging.error(e, exc_info=args.verbose)
                
    return exit_code

if __name__ == "__main__":
    sys.exit(main())