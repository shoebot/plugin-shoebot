import os
import sys
from distutils.spawn import find_executable as which

import gi

from plugin_shoebot.venv import get_system_environment, get_current_environment, \
    virtualenv_has_binary, virtualenv_interpreter

gi.require_version('Gtk', '3.0')

from gi.repository import Gio, Gtk

from plugin_shoebot import PLUGIN_DIRECTORY
from plugin_shoebot.examples import find_example_dir
from plugin_shoebot.venv_chooser import VirtualEnvChooser

DEFAULT = 'default'
SYSTEM = 'system'


def load_gsettings():
    schema_id = "apps.shoebot"
    path = "/apps/shoebot/"

    schema_dir = '{}/install/plugin_data'.format(PLUGIN_DIRECTORY)
    try:
        os.makedirs(schema_dir)
    except OSError:
        pass
    if not os.path.exists('{}/gschemas.compiled'.format(schema_dir)):
        os.system('glib-compile-schemas {plugins_dir}'.format(plugins_dir=schema_dir))
    schema_source = Gio.SettingsSchemaSource.new_from_directory(schema_dir,
                                                                Gio.SettingsSchemaSource.get_default(), False)
    schema = Gio.SettingsSchemaSource.lookup(schema_source, schema_id, False)
    if not schema:
        raise Exception("Cannot get GSettings  schema")
    settings = Gio.Settings.new_full(schema, None, path)
    return settings


def find_shoebot_binary(venv):
    """
    Find shoebot executable

    :param venv: venv param, may be a path or 'Default' or 'System'
    """
    exists, path = virtualenv_has_binary(venv, 'sbot')
    if exists:
        return path
    else:
        sys.stderr.write('Shoebot not found in venv: %s\n' % venv)
        return None


class Preferences:
    def __init__(self):
        gsettings = load_gsettings()
        venv = gsettings.get_string('current-virtualenv')
        if venv == SYSTEM:
            venv = get_system_environment()
        elif venv == DEFAULT:
            venv = get_current_environment()

        self.venv = venv
        self.shoebot_binary = find_shoebot_binary(self.venv)

    @property
    def example_dir(self):
        directory = find_example_dir(virtualenv_interpreter(self.venv))
        return directory

    def __repr__(self):
        return '<ShoebotPreferences venv={venv} python={python}>'.format(venv=self.venv,
                                                                                       python=self.python)
        # return '<ShoebotPreferences python={python} example_dir={example_dir}>'.format(python=self.python,
        #                                                                                example_dir=self.example_dir)


preferences = Preferences()


def preferences_changed():
    global preferences
    preferences = Preferences()


def virtualenv_changed(venv):
    preferences_changed()


class ShoebotPreferences(Gtk.Box):
    """
    Currently allows the user to choose a virtualenv.
    """

    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=2)

        label = Gtk.Label("Python Environment")
        self.add(label)
        self.pack_start(label, True, True, 0)

        gsettings = load_gsettings()

        virtualenv_chooser = VirtualEnvChooser(gsettings=gsettings, on_virtualenv_chosen=virtualenv_changed)
        self.add(virtualenv_chooser)


if __name__ == '__main__':
    # Debug - create the configuration
    win = Gtk.Window()
    win.add(ShoebotPreferences())
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
