import errno

from gi.repository import Gtk, Gio, GObject, Pango, Peas, PeasGtk

from plugin_shoebot.gui.gtk3.menu_gaction import example_menu_xml
from plugin_shoebot.gui.gtk3.preferences import ShoebotPreferences, preferences
from plugin_shoebot.shoebot_wrapper import RESPONSE_CODE_OK, RESPONSE_REVERTED, CMD_LOAD_BASE64, ShoebotProcess

from gettext import gettext as _

import os

MENU_UI = """
<ui>
  <menubar name="MenuBar">
    <menu name="ShoebotMenu" action="Shoebot">
      <placeholder name="ShoebotOps_1">
        <menuitem name="Run in Shoebot" action="ShoebotRun"/>
            <separator/>
                 <menu name="ShoebotExampleMenu" action="ShoebotOpenExampleMenu">
                    {0}
                </menu>
        <separator/>
        <menuitem name="Enable Socket Server" action="ShoebotSocket"/>
        <menuitem name="Show Variables Window" action="ShoebotVarWindow"/>
        <menuitem name="Go Fullscreen" action="ShoebotFullscreen"/>
        <menuitem name="Live Code" action="ShoebotLive"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

OUTPUT_FONT = "Monospace"


class ScrollingOutputWidget(Gtk.ScrolledWindow):
    def __init__(self, name, font=OUTPUT_FONT):
        Gtk.ScrolledWindow.__init__(self)
        text = Gtk.TextView()
        text.set_editable(False)

        font_desc = Pango.FontDescription(font)
        text.modify_font(font_desc)
        text.set_name(name)

        buff = text.get_buffer()
        buff.create_tag('error', foreground='red')

        self.add(text)
        self.text = text

    def clear_text(self, text='', tag=None):
        buffer = self.text.get_buffer()
        offset = 0
        buffer.set_text(text)

        if tag:
            start_iter = buffer.get_iter_at_offset(offset)
            end_iter = buffer.get_end_iter()
            buffer.apply_tag_by_name(tag, start_iter, end_iter)

    def append_text(self, text, tag=None):
        buffer = self.text.get_buffer()
        offset = buffer.get_char_count()
        buffer.insert(buffer.get_end_iter(), text)

        if tag:
            start_iter = buffer.get_iter_at_offset(offset)
            end_iter = buffer.get_end_iter()
            buffer.apply_tag_by_name(tag, start_iter, end_iter)

    def scroll_to_end(self):
        buffer = self.text.get_buffer()
        self.text.scroll_to_iter(buffer.get_end_iter(), 0.0, True, 0.0, 0.0)


class ShoebotOutputWidget(ScrollingOutputWidget):
    pass


class WidgetPanelHelper(object):
    """
    PanelHelper for the old style panel (Gedit 3.10, Xed, Pluma)
    """

    def __init__(self, window):
        self.window = window
        self.shoebot_output = ShoebotOutputWidget('Shoebot Output')
        self.live_output = ScrollingOutputWidget('Shoebot Live')

        self.text = self.shoebot_output.text
        self.live_text = self.shoebot_output.text

    def add_output_widgets(self):
        panel = self.window.get_bottom_panel()
        panel.add_titled(self.shoebot_output, "shoebot-output", "Shoebot Output")
        panel.add_titled(self.live_output, "shoebot-live", "Shoebot Live")

    def remove_output_widgets(self):
        panel = self.window.get_bottom_panel()
        panel.remove_item(self.shoebot_output)
        panel.remove_item(self.live_output)


class ShoebotPluginHelperMixin(object):
    def __init__(self, editor_class, window, panel_helper):
        """
        :param editor_class: e.g. Xed, Pluma, Gedit
        :param window:
        """
        self.editor = editor_class
        self.panel_helper = panel_helper
        # self.panel_helper = WidgetPanelHelper(window)
        # self.menu_helper = UIManagerWindowHelper(self, editor_class, window)
        self.window = window

        self.changed_handler_id = None
        self.idle_handler_id = None

        self.id_name = 'ShoebotPluginID'

        self.use_socketserver = False
        self.show_varwindow = True
        self.use_fullscreen = False
        self.livecoding = False
        self.verbose_output = False  # TODO - no UI to change this currently

        self.started = False

        self.bot = None

    def activate(self):
        self.insert_menu()
        self.panel_helper.add_output_widgets()

    def deactivate(self):
        self.remove_menu()
        self.panel_helper.remove_output_widgets()
        self.window = None

    def update_ui(self):
        self.action_group.set_sensitive(self.window.get_active_document() is not None)
        # hack to make sure that views are connected
        # since activate() is not called on startup
        if not self.started and self.window.get_views():
            for view in self.window.get_views():
                self.connect_view(view)
            self.started = True

    def start_shoebot(self):
        print("start_shoebot", self)
        shoebot_binary = preferences.shoebot_binary
        if not shoebot_binary:
            self.panel_helper.shoebot_output.clear_text('sbot not found in path.')
            while Gtk.events_pending():
                Gtk.main_iteration()
            return False

        if self.bot and self.bot.process.poll() is not None:
            self.bot.send_command("quit")

        # get the text buffer
        doc = self.window.get_active_document()
        if not doc:
            return

        title = '%s - Shoebot' % doc.get_short_name_for_display()
        cwd = os.path.dirname(doc.get_uri_for_display()) or None

        start, end = doc.get_bounds()
        source = doc.get_text(start, end, False)
        if not source:
            return False

        self.panel_helper.shoebot_output.clear_text('running shoebot at %s\n' % shoebot_binary)

        while Gtk.events_pending():
            Gtk.main_iteration()

        self.disconnect_change_handler(doc)
        self.changed_handler_id = doc.connect("changed", self.doc_changed)

        self.bot = ShoebotProcess(source, self.use_socketserver, self.show_varwindow, self.use_fullscreen,
                                  self.verbose_output, title, cwd=cwd, sbot=shoebot_binary)
        self.idle_handler_id = GObject.idle_add(self.update_shoebot)

    def disconnect_change_handler(self, doc):
        if self.changed_handler_id is not None:
            doc.disconnect(self.changed_handler_id)
            self.changed_handler_id = None

    def get_source(self, doc):
        """
        Grab contents of 'doc' and return it

        :param doc: The active document
        :return:
        """
        start_iter = doc.get_start_iter()
        end_iter = doc.get_end_iter()
        source = doc.get_text(start_iter, end_iter, False)
        return source

    def doc_changed(self, *args):
        if self.livecoding and self.bot:
            doc = self.window.get_active_document()
            source = self.get_source(doc)

            try:
                self.bot.live_source_load(source)
            except Exception:
                self.bot = None
                self.disconnect_change_handler(doc)
                raise
            except IOError as e:
                self.bot = None
                self.disconnect_change_handler(doc)
                if e.errno == errno.EPIPE:
                    # EPIPE error
                    print('FIXME: %s' % str(e))
                else:
                    # Something else bad happened
                    raise

    def update_shoebot(self):
        if self.bot:
            shoebot_output = self.panel_helper.shoebot_output

            for stdout_line, stderr_line in self.bot.get_output():
                if stdout_line is not None:
                    shoebot_output.append_text(stdout_line)
                if stderr_line is not None:
                    # Use the 'error' tag so text is red
                    shoebot_output.append_text(stderr_line, tag="error")

            shoebot_output.scroll_to_end()

            live_output = self.panel_helper.live_output
            for response in self.bot.get_command_responses():
                if response is None:
                    # sentinel value - clear the buffer
                    live_output.clear_text()
                else:
                    cmd, status, info = response.cmd, response.status, response.info
                    if cmd == CMD_LOAD_BASE64:
                        if status == RESPONSE_CODE_OK:
                            live_output.clear_text('Reloaded successfully.')
                            # TODO switch panels to 'Shoebot' if on 'Shoebot Live'
                        elif status == RESPONSE_REVERTED:
                            error_message = '\n'.join(info).replace('\\n', '\n')
                            live_output.append_text(error_message)
                            live_output.scroll_to_end()

            while Gtk.events_pending():
                Gtk.main_iteration()

        return self.bot and self.bot.running


class ShoebotWindowHelperUIManager(ShoebotPluginHelperMixin):
    # Old style Gtk3 window (Pluma, Xed)
    def __init__(self, plugin_helper, editor_class, window, panel_helper):
        ShoebotPluginHelperMixin.__init__(self, editor_class, window, panel_helper)
        self.plugin_helper = plugin_helper
        self.editor_class = editor_class
        self.window = window
        self.example_bots = {}

    def insert_menu(self):
        examples_xml, example_actions, submenu_actions = example_menu_xml()

        ui_str = MENU_UI.format(examples_xml)

        manager = self.window.get_ui_manager()
        self.action_group = Gtk.ActionGroup("ShoebotPluginActions")
        self.action_group.add_actions([
            ("Shoebot", None, _("Shoe_bot"), None, _("Shoebot"), None),
            ("ShoebotRun", None, _("Run in Shoebot"), '<control>R', _("Run in Shoebot"), self.on_run),
            ('ShoebotOpenExampleMenu', None, _('E_xamples'), None, None, None)
        ])

        for action, label in example_actions:
            self.action_group.add_actions([(action, None, label, None, None, self.on_open_example)])

        for action, label in submenu_actions:
            self.action_group.add_actions([(action, None, label, None, None, None)])

        self.action_group.add_toggle_actions([
            ("ShoebotSocket", None, _("Enable Socket Server"), '<control><alt>S', _("Enable Socket Server"),
             self.toggle_socket_server, False),
            ("ShoebotVarWindow", None, _("Show Variables Window"), '<control><alt>V', _("Show Variables Window"),
             self.toggle_var_window, False),
            ("ShoebotFullscreen", None, _("Go Fullscreen"), '<control><alt>F', _("Go Fullscreen"),
             self.toggle_fullscreen, False),
            ("ShoebotLive", None, _("Live Code"), '<control><alt>C', _("Live Code"), self.toggle_livecoding, False),
        ])
        manager.insert_action_group(self.action_group)

        self.ui_id = manager.add_ui_from_string(ui_str)
        manager.ensure_update()

    def remove_menu(self):
        manager = self.window.get_ui_manager()
        manager.remove_action_group(self.action_group)
        for bot, ui_id in self.example_bots.items():
            manager.remove_ui(ui_id)
        manager.remove_ui(self.ui_id)

        # Make sure the manager updates
        manager.ensure_update()

    def on_open_example(self, action):
        example_dir = preferences.example_dir
        filename = os.path.join(example_dir, action.get_name()[len('ShoebotOpenExample'):].strip())

        drive, directory = os.path.splitdrive(os.path.abspath(os.path.normpath(filename)))
        uri = "file:///%s%s" % (drive, directory)
        gio_file = Gio.file_new_for_uri(uri)
        encoding = self.editor_class.encoding_get_current()
        self.window.create_tab_from_location(
            gio_file,
            encoding,
            0,
            0,  # column
            False,  # Do not create an empty file
            True)  # Switch to the tab

    def on_run(self, action):
        self.start_shoebot()
        # TODO - bit hacky, some re-org needed
        self.start_shoebot()

    def toggle_socket_server(self, action):
        self.use_socketserver = action.get_active()

    def toggle_var_window(self, action):
        self.show_varwindow = action.get_active()

    def toggle_fullscreen(self, action):
        self.use_fullscreen = action.get_active()

    def toggle_livecoding(self, action):
        self.livecoding = action.get_active()
        panel = self.window.get_bottom_panel()
        if self.livecoding and self.bot:
            doc = self.window.get_active_document()
            source = self.get_source(doc)
            self.bot.live_source_load(source)

            icon = Gtk.Image()
            panel.add_item(self.live_text, 'Shoebot Live', 'Shoebot Live', icon)
        else:
            panel.remove_item(self.live_text)
