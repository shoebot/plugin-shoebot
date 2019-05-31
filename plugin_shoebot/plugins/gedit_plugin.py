from gi.repository import GObject, Gedit, PeasGtk

from plugin_shoebot.gui.gtk3.preferences import ShoebotPreferences
from plugin_shoebot.plugins.peas3gio import AppMenuHelper, ShoebotWindowHelperGio
from plugin_shoebot.plugins.peas_editor_shims import apply_shims


class ShoebotPlugin(GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):
    __gtype_name__ = "ShoebotPlugin"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.tools_menu_ext = None

    def do_activate(self):
        window = self.window
        apply_shims(Gedit, window)
        self.window_helper = ShoebotWindowHelperGio(self.window, 'gedit ')
        self.window_helper.do_activate()
        # panel_helper = GtkStackPanelHelper(window)

    def do_deactivate(self):
        pass

    def do_create_configure_widget(self):
        widget = ShoebotPreferences()
        return widget


class ShoebotPluginMenu(GObject.Object, Gedit.AppActivatable):
    app = GObject.property(type=Gedit.App)

    # __gtype__ = 'ShoebotPluginMenu'

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.menu_helper = AppMenuHelper(self, Gedit, self.app)
        self.menu_helper.activate()

    def do_deactivate(self):
        self.menu_helper.deactivate()
