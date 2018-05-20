import os
from distutils.spawn import find_executable as which

from gi.repository import Gio, Gtk

from plugin_shoebot import PLUGIN_DIRECTORY
from plugin_shoebot.examples import find_example_dir
from plugin_shoebot.venv_chooser import VirtualEnvChooser


def load_gsettings():
    schema_id = "apps.shoebot.gedit"
    path = "/apps/shoebot/gedit/"

    schema_dir = '{}/install/plugin_data'.format(PLUGIN_DIRECTORY)
    schema_source = Gio.SettingsSchemaSource.new_from_directory(schema_dir,
                                                                Gio.SettingsSchemaSource.get_default(), False)
    schema = Gio.SettingsSchemaSource.lookup(schema_source, schema_id, False)
    if not schema:
        raise Exception("Cannot get GSettings  schema")
    settings = Gio.Settings.new_full(schema, None, path)
    return settings


def find_shoebot_exe(venv):
    """
    Find shoebot executable

    :param venv: venv param, may be a path or 'Default' or 'System'
    """
    if venv == 'Default':
        sbot = which('sbot')
    elif venv == 'System':
        # find system python
        env_venv = os.environ.get('VIRTUAL_ENV')
        if not env_venv:
            return which('sbot')

        # First sbot in path that is not in current venv
        for p in os.environ['PATH'].split(os.path.pathsep):
            sbot = '%s/sbot' % p
            if not p.startswith(env_venv) and os.path.isfile(sbot):
                return sbot
    else:
        sbot = os.path.join(venv, 'bin/sbot')
        if not os.path.isfile(sbot):
            print('Shoebot not found, reverting to System shoebot')
            sbot = which('sbot')
    return os.path.realpath(sbot)


class Preferences:
    def __init__(self):
        gsettings = load_gsettings()
        self.venv = gsettings.get_string('current-virtualenv')
        self.shoebot_executable = find_shoebot_exe(self.venv)

    @property
    def example_dir(self):
        directory = find_example_dir(self.python)
        return directory

    @property
    def python(self):
        return os.path.join(self.venv, 'bin', 'python')


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
