import json
import shutil
import subprocess
from pathlib import Path


class SinaraCliManager:
    subject = "cli"


    def add_command_handlers(root_parser, subject_parser):
        SinaraCliManager.subject_parser = subject_parser
        install_parser = subject_parser.add_parser(SinaraCliManager.subject, help='sinara install subject')
        install_subparsers = install_parser.add_subparsers(title='action', dest='action', help='Action to do with subject')

        SinaraCliManager.add_install_handler(install_subparsers)


    @staticmethod
    def add_install_handler(root_parser):
        model_containerize_parser = root_parser.add_parser('install', help='containerize sinara bento service into a docker image')
        model_containerize_parser.add_argument('--gitref', help="git registry url of organization's cli")
        model_containerize_parser.set_defaults(func=SinaraCliManager.install_from_git)

    @staticmethod
    def get_orgs_dir(org_name = None):
        home_dir = str(Path.home())
        dir = Path(f'{home_dir}', '.sinara', 'orgs')
        if org_name:
            dir = Path(dir, org_name)
        return dir

    @staticmethod
    def install_from_git(args):
        gitref = args.gitref
        
        install_dir = SinaraCliManager.get_orgs_dir()
        install_dir.mkdir(parents=True, exist_ok=True)
        install_dir = Path(install_dir, 'mlops_organization')
        if install_dir.exists() and install_dir.is_dir():
            shutil.rmtree(install_dir)
        
        print(install_dir)
        command = ['git', 'clone', gitref, str(install_dir)]
        print(command)
        try:
            subprocess.run(command, timeout=60)
        except subprocess.TimeoutExpired:
            print('git process ran too long')
            return
        
        with open(f'{install_dir}/mlops_organization.json') as f:
            org = json.load(f)
        print(org)
        new_org_dir = Path(install_dir.parent.absolute(), org["name"])
        shutil.move(install_dir, new_org_dir)

