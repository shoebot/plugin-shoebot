from gi.repository import GObject, Xed, PeasGtk

from plugin_shoebot.plugins.peas_editor_shims import apply_shims
from .peas_plugin_base import ShoebotPreferences, WidgetPanelHelper, ShoebotWindowHelperUIManager


class XedShoebotPlugin(GObject.Object, Xed.WindowActivatable, PeasGtk.Configurable):
    __gtype_name__ = "ShoebotPlugin"
    window = GObject.property(type=Xed.Window)

    def do_activate(self):
        window = self.window
        apply_shims(Xed, window)

        panel_helper = WidgetPanelHelper(window)
        self.menu_helper = ShoebotWindowHelperUIManager(self, Xed, window, panel_helper)
        self.menu_helper.activate()

    def do_deactivate(self):
        self.menu_helper.deactivate()

    def do_update_state(self):
        window = self.window
        window.get_ui_manager().ensure_update()

    def do_create_configure_widget(self):
        widget = ShoebotPreferences()
        return widget
