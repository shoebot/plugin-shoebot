from gi.repository import GObject, Peas, PeasGtk, Pluma

from plugin_shoebot.plugins.peas_editor_shims import apply_shims
from .peas_plugin_base import ShoebotPreferences, ShoebotWindowHelperUIManager, WidgetPanelHelper


class PlumaShoebotPlugin(GObject.Object, Peas.Activatable, PeasGtk.Configurable):
    __gtype_name__ = "ShoebotPlugin"
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        window = self.object

    def do_activate(self):
        window = self.object
        apply_shims(Pluma, window)

        panel_helper = WidgetPanelHelper(window)

        self.menu_helper = ShoebotWindowHelperUIManager(self, Pluma, window, panel_helper)
        self.menu_helper.activate()

    def do_deactivate(self):
        window = self.object
        self.menu_helper.deactivate()

    def do_update_state(self):
        window = self.object
        window.get_ui_manager().ensure_update()

    def do_create_configure_widget(self):
        widget = ShoebotPreferences()
        return widget
