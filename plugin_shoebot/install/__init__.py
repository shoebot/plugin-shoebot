plugins = {}


def register_plugin(name, plugin):
    plugins[name] = plugin


import libpeas
libpeas.register_plugins()
