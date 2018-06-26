import itertools
import os

from gi.repository import GLib, Gtk

from plugin_shoebot.gui.gtk3.preferences import DEFAULT
from plugin_shoebot.venv import virtualenvwrapper_envs, virtualenv_has_binary, is_virtualenv


class VirtualEnvChooser(Gtk.Box):
    """
    Allow the user to choose a virtualenv.

    :param gsetting: save settings to this prefix
    """

    def __init__(self, gsettings=None, on_virtualenv_chosen=None):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        self.gsettings = gsettings
        self.on_virtualenv_chosen = on_virtualenv_chosen
        if gsettings:
            current_virtualenv = self.gsettings.get_string('current-virtualenv')
            self.user_envs = sorted(gsettings.get_value('virtualenvs'))
        else:
            current_virtualenv = None
            self.user_envs = []

        virtualenv_store = Gtk.ListStore(str, str)
        virtualenv_combo = Gtk.ComboBox.new_with_model(virtualenv_store)

        sys_envs = [[SYSTEM, 'System'], [DEFAULT, 'Default']]

        all_envs = itertools.chain(
            sys_envs,
            [[os.path.basename(venv), venv] for venv in virtualenvwrapper_envs(filter=lambda: virtualenv_has_binary(venv, 'sbot'))],
            [[os.path.basename(venv), venv] for venv in self.user_envs]
        )

        for i, (name, venv) in enumerate(all_envs):
            virtualenv_store.append([os.path.basename(venv), venv])

            if gsettings and venv == current_virtualenv:
                virtualenv_combo.set_active(i)

        virtualenv_combo.connect("changed", self.on_virtualenv_combo_changed)
        virtualenv_combo.set_entry_text_column(1)
        renderer_text = Gtk.CellRendererText()
        virtualenv_combo.pack_start(renderer_text, True)
        virtualenv_combo.add_attribute(renderer_text, "text", 0)

        self.virtualenv_combo = virtualenv_combo
        self.virtualenv_store = virtualenv_store

        self.pack_start(virtualenv_combo, False, False, True)

        add_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_ADD))
        add_button.connect("clicked", self.on_add_virtualenv)
        self.pack_start(add_button, True, True, 0)

        remove_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REMOVE))
        remove_button.connect("clicked", self.on_remove_virtualenv)
        remove_button.set_sensitive(current_virtualenv in self.user_envs)

        self.pack_start(remove_button, True, True, 0)
        self.remove_button = remove_button

    def on_virtualenv_combo_changed(self, combo):
        # TODO - Name these
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            name, venv = model[tree_iter][:2]
            if self.gsettings:
                self.gsettings.set_string('current-virtualenv', venv)
                if self.on_virtualenv_chosen is not None:
                    self.on_virtualenv_chosen(venv)

            self.remove_button.set_sensitive(venv in self.user_envs)
        else:
            entry = combo.get_child()
            print("Entered: %s" % entry.get_text())

    def on_remove_virtualenv(self, widget):
        index = self.virtualenv_combo.get_active()
        item = self.virtualenv_store[index]
        venv = item[1]

        self.virtualenv_combo.set_active(0)

        # Use gtk iterator to delete item
        _iter = self.virtualenv_store.get_iter(index)
        self.virtualenv_store.remove(_iter)

        if venv in self.user_envs:
            self.user_envs.remove(venv)
            self.gsettings.set_value('virtualenvs', GLib.Variant('as', self.user_envs))

    def on_add_virtualenv(self, widget):
        # TODO - complete this and remove print statements
        dialog = Gtk.FileChooserDialog("Please choose a virtualenv", widget.get_toplevel(),
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Select clicked")
            print("Folder selected: " + dialog.get_filename())
            folder = dialog.get_filename()
            if is_virtualenv(folder):
                self.add_virtualenv(folder)
                dialog.destroy()
            else:
                print('Not a venv')
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")
            dialog.destroy()

    def add_virtualenv(self, venv):
        self.virtualenv_store.append([os.path.basename(venv), venv])
        self.user_envs.append(venv)
        self.gsettings.set_value('virtualenvs', GLib.Variant('as', self.user_envs))
        self.virtualenv_combo.set_active(len(self.virtualenv_store) - 1)
