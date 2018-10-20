import os

from plugin_shoebot.install import register_plugin
from plugin_shoebot.install.plugin import PluginInstaller


class PeasPluginBase(PluginInstaller):
    vars = PluginInstaller.vars + [
        'app', 'app_major_version', 'user_config_dir'
    ]
    target_dirs = PluginInstaller.target_dirs + [
        'plugins_dir', 'language_dir'
    ]

    darwin_install_dir = '~/.local/share'

    linux2_admin_install_dir = ['/usr/lib64', '/usr/lib']
    linux2_user_install_dir = '~/.local/share'

    linux2_plugins_dir = "{install_dir}/{app}/plugins/"

    nt_admin_install_dir = r"%ProgramFiles%\{app}"
    nt_admin_plugins_dir = r"%ProgramFiles%\{app}\lib\{app_major_version}\plugins"

    nt_user_install_dir = "%UserProfile%\AppData\Roaming"
    nt_user_plugins_dir = "{install_dir}/{app}/plugins"


    language_dir = "{install_dir}/gtksourceview-3.0/language-specs"

    after_copy = [
        lambda self, directories: os.system("glib-compile-schemas {plugins_dir}plugin_shoebot/install/plugin_data\n".format(**directories))
    ]


class Peas3PluginBase(PeasPluginBase):
    user_config_dir = '~/.local/share'

    copy = [
        ('{plugin_shoebot}', '{plugins_dir}/plugin_shoebot'),
        ('{plugin_data}/shoebot-{app_major_version}.plugin', '{plugins_dir}'),
        ('{plugin_data}/shoebot-{app_major_version}.lang', '{language_dir}'),
    ]


class PlumaPlugin(PeasPluginBase):
    user_config_dir = '~/.config'
    app = 'pluma'
    app_major_version = 'pluma-1'

    copy = [
        ('{plugin_shoebot}', '{plugins_dir}/plugin_shoebot'),
        ('{plugin_data}/shoebot-{app_major_version}.pluma-plugin', '{plugins_dir}'),
        ('{plugin_data}/shoebot-{app_major_version}.lang', '{language_dir}'),
    ]

class GioGeditPlugin(Peas3PluginBase):
    """
    gedit-3.12+ has GIO based menus
    """
    app = 'gedit'
    app_major_version = 'gedit-3'


class GioXedPlugin(Peas3PluginBase):
    """
    gedit-3.12+ has GIO based menus
    """
    app = 'xed'
    app_major_version = 'xed-1'


def register_plugins():
    register_plugin('gedit', GioGeditPlugin)
    register_plugin('xed', GioXedPlugin)
    register_plugin('pluma', PlumaPlugin)
