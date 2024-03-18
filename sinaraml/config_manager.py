from pathlib import Path
import os
import configparser
import json
import shutil

class SinaraGlobalConfigManager():
    def __init__(self, ensure_folders=False):
        self.config_folder = Path(os.path.expanduser("~")) / ".sinaraml"
        self.servers_folder = Path(self.config_folder) /  "servers"
        self.trash_bin_folder = Path(self.config_folder) / "trash_bin"
        self.trashed_servers_folder = Path(self.trash_bin_folder) / "servers"

        if ensure_folders:
            self.ensure_config_folder()

            self.ensure_trashed_servers_folder_folder()


    def ensure_config_folder(self):
        if not self.config_folder.exists():
            self.config_folder.mkdir(parents=True, exist_ok=True)

    def ensure_trashed_servers_folder_folder(self):
        if not self.trashed_servers_folder.exists():
            self.trashed_servers_folder.mkdir(parents=True, exist_ok=True)

    def get_trashed_servers(self):
        result = {}
        path = Path(self.trashed_servers_folder)
        for p in path.rglob(f"*"):
            if p.name == "server.json":
                result[p.parent.name] = str(p)
        return result


class SinaraServerConfigManager(SinaraGlobalConfigManager):

    def __init__(self, server_name, ensure_folders=True):
        super(SinaraServerConfigManager, self).__init__(ensure_folders)
        self.server_name = server_name
        self.server_folder = Path(self.config_folder) /  "servers" / server_name
        self.server_config = self.server_folder / "server.json"

        if ensure_folders:
            self.ensure_server_folder()

    def ensure_server_folder(self):
        if not self.server_folder.exists():
            self.server_folder.mkdir(parents=True, exist_ok=True)

    def server_config_exist(self):
        return self.server_config.exists()
    
    def save_server_config(self, config):
        with open(self.server_config, 'w') as cfg:
            json.dump(config, cfg)

    def load_server_config(self):
        with open(self.server_config, 'r') as cfg:
            return json.load(cfg)
        
    def trash_server(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        server_folder_trashed = Path(self.trashed_servers_folder) / f"{self.server_name}.{timestamp}"
        shutil.copytree(self.server_folder, server_folder_trashed, dirs_exist_ok=False)
        shutil.rmtree(self.server_folder)
        return Path(server_folder_trashed) / "server.json"
