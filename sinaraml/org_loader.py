import importlib.util
import logging
import os
import sys
from .cli_manager import SinaraCliManager

class SinaraOrgLoader():

    @staticmethod
    def load_organization(org_name = 'personal'):
        filepath = SinaraCliManager.get_orgs_dir(org_name)
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
    def get_organization_parts():
        plugins = []
        from pkgutil import iter_modules
        for p in iter_modules():
            try:
                if p.name.startswith('sinaraml_plugin'):
                    plugin_module = __import__(p.name)
                    plugin_module.get_supported_infras()
                    plugins.append(p.name)
            except Exception as e:
                logging.debug(e)
        return plugins
    
    @staticmethod
    def get_infras(plugin):
        plugin_module = __import__(plugin)
        return plugin_module.get_supported_infras()
        
    @staticmethod 
    def get_infra_plugin(plugin):
        plugin_module = __import__(plugin)
        return plugin_module

