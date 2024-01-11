import logging

class SinaraPluginLoader():

    @staticmethod
    def get_infra_plugins():
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

