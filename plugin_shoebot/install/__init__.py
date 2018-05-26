import sys

plugins = {}


def register_plugin(name, plugin):
    plugins[name] = plugin


def parse_plugin_names(names_str):
    """
    :param names_str: space separated string of plugin names
    :return: set of plugins
    :raise: sys.exit if namea are invalid
    """
    available_plugins = set(plugins.keys())
    if names_str is None:
        plugin_names = available_plugins
    else:
        plugin_names = set(names_str.split())
        if 'all' in plugin_names:
            plugin_names = set(plugins.keys())
        if not plugin_names.issubset(available_plugins):
            valid_plugins = ' '.join(available_plugins)
            invalid_plugins = ' '.join(plugin_names.difference(available_plugins))
            sys.stderr.write(
                'Invalid plugins specified: "%s", valid plugins: "%s"\n' % (invalid_plugins, valid_plugins))
            sys.exit(1)
    return plugin_names


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
