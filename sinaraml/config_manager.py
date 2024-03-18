from multiprocessing.util import ForkAwareThreadLock
from pathlib import Path
import os
import configparser
import json
import shutil
import sys

class SinaraConfigManager():

    def __init__(self, server_name):
        self.server_name = server_name
        self.config_folder = Path(os.path.expanduser("~")) / ".sinaraml"
        self.server_folder = Path(self.config_folder) /  "servers" / server_name
        self.server_config = self.server_folder / "server.json"
        self.trash_bin_folder = Path(self.config_folder) / "trash_bin"
        self.removed_servers_folder = Path(self.trash_bin_folder) / "servers"
        self.ensure_config_folder()
        self.ensure_server_folder()
        self.ensure_removed_servers_folder_folder()

    def ensure_config_folder(self):
        if not self.config_folder.exists():
            self.config_folder.mkdir(parents=True, exist_ok=True)

    def ensure_server_folder(self):
        if not self.server_folder.exists():
            self.server_folder.mkdir(parents=True, exist_ok=True)

    def ensure_removed_servers_folder_folder(self):
        if not self.removed_servers_folder.exists():
            self.removed_servers_folder.mkdir(parents=True, exist_ok=True)

    def server_config_exist(self):
        return self.server_config.exists()
    
    def save_server_config(self, config):
        with open(self.server_config, 'w') as cfg:
            print(config)
            json.dump(config, cfg)

    def load_server_config(self):
        with open(self.server_config, 'r') as cfg:
            return json.load(cfg)
        
    def trash_server(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        server_folder_trashed = Path(self.removed_servers_folder) / f"{self.server_name}.{timestamp}"
        shutil.copytree(self.server_folder, server_folder_trashed, dirs_exist_ok=False)
        shutil.rmtree(self.server_folder)
        return Path(server_folder_trashed) / "server.json"
