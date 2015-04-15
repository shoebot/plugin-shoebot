from urllib import pathname2url

from gettext import gettext as _
from shoebotit import ide_utils, gtk2_utils

import gedit
import gobject
import gtk
import pango
import os


def which(program):
    # gedit2 doesn't come with distutils.spawn, at least the
    # version I tested on windows
    #
    # http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/377028#377028
    #
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    def ext_candidates(fpath):
        yield fpath
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            yield fpath + ext

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            for candidate in ext_candidates(exe_file):
                if is_exe(candidate):
                    return candidate

    return None


if not which('sbot'):
    print('Shoebot executable not found.')


class ShoebotWindowHelper:
    def __init__(self, plugin, window):
        self.example_bots = {}

        self.window = window
        self.changed_handler_id = None
        panel = window.get_bottom_panel()
        self.output_widget = gtk2_utils.get_child_by_name(panel, 'shoebot-output')

        self.plugin = plugin
        self.insert_menu()

        self.id_name = 'ShoebotPluginID'

        self.use_socketserver = False
        self.show_varwindow = True
        self.use_fullscreen = False
        self.livecoding = False

        self.started = False

        for view in self.window.get_views():
            self.connect_view(view)
        
        self.bot = None

    def deactivate(self):
        self.remove_menu()
        self.window = None
        self.plugin = None
        self.action_group = None

    def insert_menu(self):
        examples_xml, example_actions, submenu_actions = gtk2_utils.examples_menu()
        ui_str = gtk2_utils.gedit2_menu(examples_xml)

        manager = self.window.get_ui_manager()
        self.action_group = gtk.ActionGroup("ShoebotPluginActions")
        self.action_group.add_actions([
            ("Shoebot", None, _("Shoe_bot"), None, _("Shoebot"), None),
            ("ShoebotRun", None, _("Run in Shoebot"), '<control>R', _("Run in Shoebot"), self.on_run_activate),
            ('ShoebotOpenExampleMenu', None, _('E_xamples'), None, None, None),
            ])

        for action, label in example_actions:
            self.action_group.add_actions([(action, None, (label), None, None, self.on_open_example)])

        for action, label in submenu_actions:
            self.action_group.add_actions([(action, None, (label), None, None, None)])

        self.action_group.add_toggle_actions([
            ("ShoebotSocket", None, _("Enable Socket Server"), '<control><alt>S', _("Enable Socket Server"), self.toggle_socket_server, False),
            ("ShoebotVarWindow", None, _("Show Variables Window"), '<control><alt>V', _("Show Variables Window"), self.toggle_var_window, False),
            ("ShoebotFullscreen", None, _("Go Fullscreen"), '<control><alt>F', _("Go Fullscreen"), self.toggle_fullscreen, False),
            ("ShoebotLive", None, _("Live Code"), '<control><alt>C', _("Live Code"), self.toggle_livecoding, False),
            ])
        manager.insert_action_group(self.action_group, -1)

        self.ui_id = manager.add_ui_from_string(ui_str)
        manager.ensure_update()

    def on_open_example(self, action):
        example_dir = ide_utils.get_example_dir()
        filename = os.path.join(example_dir, action.get_name()[len('ShoebotOpenExample'):].strip())

        uri = "file:///" + pathname2url(filename)
        self.window.create_tab_from_uri(uri,
                gedit.encoding_get_current(), 
                0, 
                False,  # Do not create a new file
                True)   # Switch to tab

    def remove_menu(self):
        manager = self.window.get_ui_manager()
        manager.remove_action_group(self.action_group)
        for bot, ui_id in self.example_bots.items():
            manager.remove_ui(ui_id)
        manager.remove_ui(self.ui_id)

        # Make sure the manager updates
        manager.ensure_update()

    def update_ui(self):
        self.action_group.set_sensitive(self.window.get_active_document() != None)
        # hack to make sure that views are connected
        # since activate() is not called on startup
        if not self.started and self.window.get_views():
            for view in self.window.get_views():
                self.connect_view(view)
            self.started = True

    def on_run_activate(self, action):
        self.start_shoebot()

    def start_shoebot(self):
        #sbot_bin=gtk2_utils.sbot_executable()
        if os.name == 'nt': ### TODO - use same mechanism as gtk3
            sbot_bin = which('sbot.cmd')
        else:
            sbot_bin = which('sbot')

        if not sbot_bin:
            textbuffer = self.output_widget.get_buffer()
            textbuffer.set_text('Cannot find sbot in path.')
            while gtk.events_pending():
               gtk.main_iteration(block=False)
            return False

        if self.bot and self.bot.process.poll() == None:
            print('Sending quit.')
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

        textbuffer = self.output_widget.get_buffer()
        textbuffer.set_text('')

        while gtk.events_pending():
           gtk.main_iteration()

        self.disconnect_change_handler(doc)
        self.changed_handler_id = doc.connect("changed", self.doc_changed)

        self.bot = ide_utils.ShoebotProcess(source, self.use_socketserver, self.show_varwindow, self.use_fullscreen, title, cwd=cwd, sbot=sbot_bin)
        self.idle_handler_id = gobject.idle_add(self.update_shoebot)

    def disconnect_change_handler(self, doc):
        if self.changed_handler_id is not None:
            doc.disconnect(self.changed_handler_id)
            self.changed_hander_id = None

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
                self.disconnect_change_handler()
                if e.errno == errno.EPIPE:
                    # EPIPE error
                    print('FIXME: %s' % str(e))
                else:
                    # Something else bad happened
                    raise

    def update_shoebot(self):
        if self.bot:
            textbuffer = self.output_widget.get_buffer()
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
            self.output_widget.scroll_to_iter(textbuffer.get_end_iter(), 0.0, True, 0.0, 0.0)
            while gtk.events_pending():
                gtk.main_iteration()

        if self.bot:
            return self.bot.running
        else:
            return False
    
    def toggle_socket_server(self, action):
        self.use_socketserver = action.get_active()

    def toggle_var_window(self, action):
        self.show_varwindow = action.get_active()

    def toggle_fullscreen(self, action):
        self.use_fullscreen = action.get_active()

    def toggle_livecoding(self, action):
        self.livecoding = action.get_active()
        if self.livecoding and self.bot:
            doc = self.window.get_active_document()
            source = self.get_source(doc)
            self.bot.live_source_load(source)

    def connect_view(self, view):
        # taken from gedit-plugins-python-openuricontextmenu
        pass


class ShoebotPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.instances = {}
        self.tempfiles = []

    def _create_view(self):
        """ Create the gtk.TextView used for shell output """
        view = gtk.TextView()
        view.set_editable(False)

        fontdesc = pango.FontDescription("Monospace")
        view.modify_font(fontdesc)
        view.set_name('shoebot-output')

        buff = view.get_buffer()
        buff.create_tag('error', foreground='red')
        return view

    def activate(self, window):
        self.text = self._create_view()
        self.panel = window.get_bottom_panel()

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.add(self.text)
        scrolled_window.show_all()
        
        self.panel.add_item(scrolled_window, 'Shoebot', image)   
        self.output_widget = scrolled_window

        self.instances[window] = ShoebotWindowHelper(self, window)

    def deactivate(self, window):
        self.panel.remove_item(self.text)
        self.instances[window].deactivate()
        del self.instances[window]
        for tfilename in self.tempfiles:
            os.remove(tfilename)

        self.panel.remove_item(self.output_widget)

    def update_state(self, window):
        self.instances[window].update_ui()
