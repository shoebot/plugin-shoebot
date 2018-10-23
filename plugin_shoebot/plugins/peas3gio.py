"""
Plugin Gedit 3.12+ using gio based menus.
"""

import errno
import gi
import os
import sys

gi.require_version('Gtk', '3.0')

from gettext import gettext as _
from gi.repository import Gtk, Gio, GObject, Pango, PeasGtk

from .peas_base import Editor
from plugin_shoebot.gui.gtk3.actions_gio import _action_prefix, _action_data_name_text_value, GioActionHelperMixin
from plugin_shoebot.gui.gtk3.menu_gio import encode_relpath, example_menu_actions
from plugin_shoebot.gui.gtk3.preferences import ShoebotPreferences, preferences
from plugin_shoebot.shoebot_wrapper import RESPONSE_CODE_OK, RESPONSE_REVERTED, CMD_LOAD_BASE64, ShoebotProcess

MENU_ACTIONS = [
    ("run", _("Run in Shoebot")),
    ("var_window", _("Variable Window"), True),
    ("socket_server", _("Socket Server"), False),
    ("live_coding", _("Live Coding"), False),
    ("full_screen", _("Full screen"), False),
    ("verbose_output", _("Verbose output"), False),
]

WINDOW_ACCELS = [("run", "<Control>R")]

EXAMPLES = []


class ShoebotPlugin(GObject.Object, Editor.WindowActivatable, PeasGtk.Configurable, GioActionHelperMixin):
    __gtype_name__ = "ShoebotPlugin"
    window = GObject.property(type=Editor.Window)

    def __init__(self):
        GObject.Object.__init__(self)

        self.changed_handler_id = None
        self.idle_handler_id = None

        self.text = None
        self.live_text = None

        self.id_name = 'ShoebotPluginID'
        self.bot = None

    def do_activate(self):
        self.add_output_widgets()
        self.add_window_actions()

    def create_scrollable_textview(self, name):
        """
        Create a Gtk.TextView inside a Gtk.ScrolledWindow

        :return: container, text_view
        """
        text_view = Gtk.TextView()
        text_view.set_editable(False)

        font_desc = Pango.FontDescription("Monospace")
        text_view.modify_font(font_desc)
        text_view.set_name(name)

        buff = text_view.get_buffer()
        buff.create_tag('error', foreground='red')

        container = Gtk.ScrolledWindow()
        container.add(text_view)
        container.show_all()
        return container, text_view

    def add_output_widgets(self):
        self.output_container, self.text = self.create_scrollable_textview("shoebot-output")
        self.live_container, self.live_text = self.create_scrollable_textview("shoebot-live")
        self.panel = self.window.get_bottom_panel()

        self.panel.add_titled(self.output_container, 'Shoebot', 'Shoebot')
        self.panel.add_titled(self.live_container, 'Shoebot Live', 'Shoebot Live')

    def create_example_actions(self, examples):
        for rel_path in examples:
            action = Gio.SimpleAction.new(
                "open_example__%s" % encode_relpath(rel_path),
                None)

            action.connect("activate", self.on_open_example, rel_path)
            self.window.add_action(action)

    def add_window_actions(self):
        self.create_example_actions(EXAMPLES)
        self.create_actions(MENU_ACTIONS)

    def on_run(self, action, user_data):
        self.start_shoebot()

    def on_open_example(self, action, user_data, rel_path):
        example_dir = preferences.example_dir
        path = os.path.join(example_dir, rel_path)

        drive, directory = os.path.splitdrive(os.path.abspath(os.path.normpath(path)))
        uri = "file://%s%s" % (drive, directory)
        gio_file = Gio.file_new_for_uri(uri)
        self.window.create_tab_from_location(
            gio_file,
            None,  # encoding
            0,
            0,  # column
            False,  # Do not create an empty file
            True)  # Switch to the tab

    def start_shoebot(self):
        sbot_bin = preferences.shoebot_binary
        if not sbot_bin:
            textbuffer = self.text.get_buffer()
            textbuffer.set_text('Cannot find sbot in path.')
            while Gtk.events_pending():
                Gtk.main_iteration()
            return False

        if self.bot and self.bot.process.poll() == None:
            self.bot.send_command("quit")

        # get the text buffer
        doc = self.window.get_active_document()
        if not doc:
            return

        title = '%s - Shoebot on gedit' % doc.get_short_name_for_display()
        cwd = os.path.dirname(doc.get_uri_for_display()) or None

        start, end = doc.get_bounds()
        source = doc.get_text(start, end, False)
        if not source:
            return False

        textbuffer = self.text.get_buffer()
        textbuffer.set_text('running shoebot at %s\n' % sbot_bin)

        while Gtk.events_pending():
            Gtk.main_iteration()

        self.disconnect_change_handler(doc)
        self.changed_handler_id = doc.connect("changed", self.doc_changed)

        self.bot = ShoebotProcess(
            source,
            self.socket_server_enabled,
            self.var_window_enabled,
            self.full_screen_enabled,
            self.verbose_output_enabled,
            title,
            cwd=cwd,
            sbot=sbot_bin)
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
        if self.live_coding_enabled and self.bot:
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
                self.disconnect_change_handler()
                if e.errno == errno.EPIPE:
                    # EPIPE error
                    sys.write('FIXME: %s\n' % str(e))
                else:
                    # Something else bad happened
                    raise

    def update_shoebot(self):
        if self.bot:
            textbuffer = self.text.get_buffer()
            for stdout_line, stderr_line in self.bot.get_output():
                if stdout_line is not None:
                    textbuffer.insert(textbuffer.get_end_iter(), stdout_line)
                if stderr_line is not None:
                    # Use the 'error' tag so text is red
                    textbuffer.insert(textbuffer.get_end_iter(), stderr_line)
                    offset = textbuffer.get_char_count() - len(stderr_line)
                    start_iter = textbuffer.get_iter_at_offset(offset)
                    end_iter = textbuffer.get_end_iter()
                    textbuffer.apply_tag_by_name("error", start_iter, end_iter)
            self.text.scroll_to_iter(textbuffer.get_end_iter(), 0.0, True, 0.0, 0.0)

            textbuffer = self.live_text.get_buffer()
            for response in self.bot.get_command_responses():
                if response is None:
                    # sentinel value - clear the buffer
                    textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
                else:
                    cmd, status, info = response.cmd, response.status, response.info
                    if cmd == CMD_LOAD_BASE64:
                        if status == RESPONSE_CODE_OK:
                            textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
                            # TODO switch panels to 'Shoebot' if on 'Shoebot Live'
                        elif status == RESPONSE_REVERTED:
                            textbuffer.insert(textbuffer.get_end_iter(), '\n'.join(info).replace('\\n', '\n'))

            while Gtk.events_pending():
                Gtk.main_iteration()

        if self.bot:
            return self.bot.running
        else:
            return False

    def on_toggle_live_coding(self, action, user_data):
        panel = self.window.get_bottom_panel()
        if self.live_coding_enabled and self.bot:
            doc = self.window.get_active_document()
            source = self.get_source(doc)
            self.bot.live_source_load(source)

            panel.add_titled(self.live_container, 'Shoebot Live', 'Shoebot Live')
        else:
            panel.remove(self.live_container)

    def do_deactivate(self):
        self.panel.remove(self.live_container)
        self.panel.remove(self.output_container)

    def do_create_configure_widget(self):
        widget = ShoebotPreferences()
        return widget


class ShoebotPluginMenu(GObject.Object, Editor.AppActivatable):
    app = GObject.property(type=Editor.App)

    def __init__(self):
        GObject.Object.__init__(self)
        self.shoebot_menu = None
        self.tools_menu_ext = None

    def build_menu(self, menu_name=_("Shoebot")):
        menu = Gio.Menu.new()
        base = Gio.MenuItem.new_submenu(menu_name, menu)

        examples_item, examples = example_menu_actions(_("E_xamples"))

        if examples and not EXAMPLES:
            # if examples is None, examples were not found.
            EXAMPLES.extend(examples)
            menu.append_item(examples_item)

        for action in MENU_ACTIONS:
            name, text, value = _action_data_name_text_value(*action)
            action_name = "win.{}_{}".format(_action_prefix(value), name)
            menu.append(text, action_name)

        return base

    def do_activate(self):
        for name, accel in WINDOW_ACCELS:
            self.app.set_accels_for_action("win.on_%s" % name, (accel, None))

        shoebot_menu = self.build_menu()
        self.shoebot_menu = shoebot_menu
        self.tools_menu_ext = self.extend_menu("tools-section")
        self.tools_menu_ext.append_menu_item(shoebot_menu)

    def do_deactivate(self):
        for name, accel in WINDOW_ACCELS:
            self.app.set_accels_for_action("win.on_%s" % name, ())
        self.tools_menu_ext = None
        self.shoebot_menu = None
