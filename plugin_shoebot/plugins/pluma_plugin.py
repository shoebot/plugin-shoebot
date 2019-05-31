from gi.repository import GObject, Peas, PeasGtk, Pluma

from plugin_shoebot.plugins.peas_editor_shims import apply_shims
from .peas_plugin_base import ShoebotPluginHelper, ShoebotPreferences, ShoebotWindowHelperUIManager, WidgetPanelHelper


class PlumaShoebotPlugin(GObject.Object, Peas.Activatable, PeasGtk.Configurable):
    __gtype_name__ = "ShoebotPlugin"
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        window = self.object

    def do_activate(self):
        window = self.object
        apply_shims(window)

        panel_helper = WidgetPanelHelper(window)
        menu_helper = ShoebotWindowHelperUIManager(self, Pluma, window)
        self.menu = ShoebotPluginHelper(Pluma, window, panel_helper, menu_helper)
        self.menu.activate()

    def do_deactivate(self):
        window = self.object
        self.menu.deactivate()

    def do_update_state(self):
        window = self.object
        window.get_ui_manager().ensure_update()

    def do_create_configure_widget(self):
        widget = ShoebotPreferences()
        return widget
