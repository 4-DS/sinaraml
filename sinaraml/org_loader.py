import importlib.util
import logging
import os
import sys

class SinaraOrgLoader():

    @staticmethod
    def load_organization(filepath):
        mod_name = "command_handler"
        sys.path.append(os.path.dirname(filepath))

        spec = importlib.util.spec_from_file_location(mod_name, filepath)
        py_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_mod)
        print(dir(py_mod))
        #py_mod.SinaraServer()
        # if hasattr(py_mod, expected_class):
        #     class_inst = getattr(py_mod, expected_class)()
        #return class_inst

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

