plugins = {}


def register_plugin(name, plugin):
    plugins[name] = plugin


def install_plugins(plugin_names=None):
    if plugin_names is None:
        plugin_names = set(plugins.keys())
    for name, plugin_klass in plugins.items():
        if name in plugin_names:
            plugin = plugin_klass()
            plugin.copy_files()


def get_plugin_outputs():
    outputs = []
    for name, plugin_klass in plugins.items():
        plugin = plugin_klass()
        outputs.extend(plugin.get_outputs())
    return outputs


def remove_plugins():
    raise NotImplemented()


def read_plugins():
    from . import libpeas
    libpeas.register_plugins()


read_plugins()
