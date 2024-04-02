import datetime
import glob
import json
import shutil
import subprocess
from pathlib import Path


class SinaraCliManager:
    subject = "cli"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    UPDATE_PERIOD = 24

    @staticmethod
    def add_command_handlers(root_parser, subject_parser):
        SinaraCliManager.subject_parser = subject_parser
        install_parser = subject_parser.add_parser(SinaraCliManager.subject, help='sinara install subject')
        install_subparsers = install_parser.add_subparsers(title='action', dest='action', help='Action to do with subject')

        SinaraCliManager.add_install_handler(install_subparsers)
        SinaraCliManager.add_update_handler(install_subparsers)


    @staticmethod
    def add_install_handler(root_parser):
        install_parser = root_parser.add_parser('install', help='containerize sinara bento service into a docker image')
        install_parser.add_argument('--gitref', help="git registry url of organization's cli")
        install_parser.set_defaults(func=SinaraCliManager.install_from_git)
    
    @staticmethod
    def add_update_handler(root_parser):
        update_parser = root_parser.add_parser('update', help='containerize sinara bento service into a docker image')
        update_parser.add_argument('--name', help="name of organization's cli")
        update_parser.set_defaults(func=SinaraCliManager.update_org)

    @staticmethod
    def get_orgs_dir(org_name = None):
        home_dir = str(Path.home())
        dir = Path(f'{home_dir}', '.sinara', 'orgs')
        if org_name:
            dir = Path(dir, org_name)
        return dir
    
    @staticmethod
    def check_last_update():
        result = {}
        home_dir = str(Path.home())
        dir = Path(f'{home_dir}', '.sinara', 'orgs', '*')
        for org_dir in glob.glob(str(dir)):
             #print(org_dir)
             with open(Path(org_dir, 'org_meta.json'), 'r') as f:
                org_meta = json.load(f)
                org_name = Path(org_dir).stem
                result[org_name] = org_meta["last_update"]
        return result

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
            print('git clone process ran too long')
            return
        
        with open(f'{install_dir}/mlops_organization.json') as f:
            org = json.load(f)
        print(org)
        new_org_dir = Path(install_dir.parent.absolute(), org["name"])
        #remove destination directory
        if new_org_dir.exists() and new_org_dir.is_dir():
            shutil.rmtree(new_org_dir)
        shutil.move(install_dir, new_org_dir)

        org_meta = {
            "last_update":  datetime.datetime.now(datetime.timezone.utc).strftime(SinaraCliManager.DATETIME_FORMAT)
        }

        with open(Path(new_org_dir, 'org_meta.json'), 'w') as f:
            json.dump(org_meta, f)


    @staticmethod
    def update_org(args):
        org_name = args.name
        org_dir = SinaraCliManager.get_orgs_dir(org_name)
        last_update  = SinaraCliManager.check_last_update()

        print(org_name)
        print(org_dir)
        print(last_update)
        last_update_datetime = datetime.datetime.strptime(last_update[org_name], SinaraCliManager.DATETIME_FORMAT).replace(tzinfo=None)
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        duration = now - last_update_datetime
        hours = divmod(duration.total_seconds(), 3600)[0]
        if hours > SinaraCliManager.UPDATE_PERIOD:
            command = ['git', '-C', str(org_dir), 'pull']
            try:
                subprocess.run(command, timeout=60)
            except subprocess.TimeoutExpired:
                print('git pull process ran too long')
