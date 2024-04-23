import datetime
import glob
import json
import shutil
import subprocess
import importlib
import os
import sys
from pathlib import Path


class SinaraOrgManager:
    SUBJECT = "org"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    UPDATE_PERIOD = 24

    @staticmethod
    def load_organization(org_name = 'personal'):
        filepath = SinaraOrgManager.get_orgs_dir(org_name)
        if not os.path.isdir(filepath):
            return
        filepath = os.path.abspath(filepath)
        mod_name = os.path.basename(filepath)
        mod_dir = os.path.dirname(filepath)
    
        if not mod_dir in sys.path:
            sys.path.append(mod_dir)
            
        py_mod = importlib.import_module(mod_name)
        
        return py_mod.CommandHandler()

    @staticmethod
    def add_command_handlers(root_parser, subject_parser):
        SinaraOrgManager.subject_parser = subject_parser
        org_parser = subject_parser.add_parser(SinaraOrgManager.SUBJECT, help='sinara org <arguments> or -h for help on command')
        org_subparsers = org_parser.add_subparsers(title='action', dest='action', help='Action to do with subject')
        root_parser.subjects.append(SinaraOrgManager.SUBJECT)

        # test two subjects with same name
        # if SinaraOrgManager.SUBJECT not in root_parser.subjects:
        #     org_parser = subject_parser.add_parser(SinaraOrgManager.SUBJECT, help='sinara org <arguments> or -h for help on command')
        #     org_subparsers = org_parser.add_subparsers(title='action', dest='action', help='Action to do with subject')

        SinaraOrgManager.add_install_handler(org_subparsers)
        SinaraOrgManager.add_update_handler(org_subparsers)
        SinaraOrgManager.add_list_handler(org_subparsers)

    @staticmethod
    def add_install_handler(root_parser):
        install_parser = root_parser.add_parser('install', help='install organization cli')
        install_parser.add_argument('--gitref', help="git registry url of organization's cli")
        install_parser.set_defaults(func=SinaraOrgManager.install_from_git)
    
    @staticmethod
    def add_update_handler(root_parser):
        update_parser = root_parser.add_parser('update', help='update organization cli')
        update_parser.add_argument('--name', help="name of organization's cli")
        update_parser.set_defaults(func=SinaraOrgManager.update_org)

    @staticmethod
    def add_list_handler(root_parser):
        list_parser = root_parser.add_parser('list', help='list all installed organization cli and platforms')
        list_parser.set_defaults(func=SinaraOrgManager.list_platforms)

    @staticmethod
    def get_orgs_dir(org_name = None):
        home_dir = str(Path.home())
        dir = Path(f'{home_dir}', '.sinaraml', 'orgs')
        if org_name:
            dir = Path(dir, org_name)
        return dir

    @staticmethod
    def get_orgs():
        result = []
        for org_path in SinaraOrgManager.get_orgs_dir().glob('*'):
            with open(Path(org_path, 'mlops_organization.json')) as f:
                org = json.load(f)
                result.append(org)
        return result
    
    @staticmethod
    def check_last_update():
        result = {}
        home_dir = str(Path.home())
        dir = Path(f'{home_dir}', '.sinaraml', 'orgs', '*')
        for org_dir in glob.glob(str(dir)):
             #print(org_dir)
             org_meta_path = Path(org_dir, 'org_meta.json')
             if not org_meta_path.exists():
                with open(org_meta_path, 'w') as f:
                    json.dump({}, f)

             with open(org_meta_path, 'r') as f:
                org_meta = json.load(f)
                org_name = Path(org_dir).stem
                if "last_update" in org_meta.keys():
                    result[org_name] = org_meta["last_update"]
                else:
                    result[org_name] = None
        return result

    @staticmethod
    def install_from_git(args):
        gitref = args.gitref
        
        install_dir = SinaraOrgManager.get_orgs_dir()
        install_dir.mkdir(parents=True, exist_ok=True)
        install_dir = Path(install_dir, 'mlops_organization')
        if install_dir.exists() and install_dir.is_dir():
            shutil.rmtree(install_dir)
        
        command = f'git clone {gitref} {str(install_dir)}'
        print(command)
        try:
            subprocess.run(command, timeout=60, shell=True)
        except subprocess.TimeoutExpired:
            print('git clone process ran too long')
            return
        
        with open(f'{install_dir}/mlops_organization.json') as f:
            org = json.load(f)
        #print(org)
        new_org_dir = Path(install_dir.parent.absolute(), org["name"])
        #remove destination directory
        if new_org_dir.exists() and new_org_dir.is_dir():
            shutil.rmtree(new_org_dir)
        shutil.move(install_dir, new_org_dir)

        SinaraOrgManager._install_org_requirements(new_org_dir)

        org_meta = {
            "last_update":  datetime.datetime.now(datetime.timezone.utc).strftime(SinaraOrgManager.DATETIME_FORMAT)
        }

        with open(Path(new_org_dir, 'org_meta.json'), 'w') as f:
            json.dump(org_meta, f)


    @staticmethod
    def update_org(args):
        org_name = args.name
        if not org_name:
            # update all organizations
            for org in SinaraOrgManager.get_orgs():
                from collections import namedtuple
                Args = namedtuple('Args', ['name'])
                args = Args(name=org["name"])
                SinaraOrgManager.update_org(args)
            return
            
        org_dir = SinaraOrgManager.get_orgs_dir(org_name)
        last_update  = SinaraOrgManager.check_last_update()

        #print(org_name)
        #print(org_dir)
        #print(last_update)
        last_update_datetime = datetime.datetime.strptime(last_update[org_name], SinaraOrgManager.DATETIME_FORMAT).replace(tzinfo=None)
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        duration = now - last_update_datetime
        hours = divmod(duration.total_seconds(), 3600)[0]
        if hours > SinaraOrgManager.UPDATE_PERIOD and hasattr(args, 'internal') and args.internal == True\
            or not hasattr(args, 'internal'):
            command = f'git -C {str(org_dir)} pull'
            try:
                print(f"Updating organization '{org_name}'")
                subprocess.run(command, shell=True, timeout=60)
                SinaraOrgManager._install_org_requirements(org_dir)

                org_meta_path = Path(org_dir, 'org_meta.json')
                with open(org_meta_path, 'r') as f:
                    org_meta = json.load(f)
                    org_meta["last_update"] = datetime.datetime.now(datetime.timezone.utc).strftime(SinaraOrgManager.DATETIME_FORMAT)
                with open(Path(org_dir, 'org_meta.json'), 'w') as f:
                   json.dump(org_meta, f)

            except subprocess.TimeoutExpired:
                print('org update process ran too long')
                return
    
    @staticmethod
    def _install_org_requirements(org_dir):
        requirements_path = Path(org_dir, 'requirements.txt')
        pip_install_cmd = f'pip install -r {requirements_path}'
        subprocess.run(pip_install_cmd, shell=True, timeout=300)

    @staticmethod
    def list_platforms(args):
        org_dir = SinaraOrgManager.get_orgs_dir()

        for dir in glob.glob(str(Path(org_dir, '*'))):
            with open(f'{dir}/mlops_organization.json') as f:
                org = json.load(f)
                print(f'Organization: {org["name"]}')
                if "cli_bodies" in org.keys():
                    for body in org["cli_bodies"]:
                        platforms = "|".join(body["platform_names"])
                        print(f'{org["name"]}_{body["boundary_name"]}_[{platforms}]')