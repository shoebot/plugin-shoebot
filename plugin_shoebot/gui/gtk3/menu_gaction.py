"""
Gtk3 support for shoebot in editors and IDEs
"""

import os

from gi.repository import Gtk
from plugin_shoebot.examples import get_example_dir
from plugin_shoebot.utils import make_readable_filename

from .preferences import ShoebotPreferences

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


def examples_menu(root_dir=None, depth=0):
    """
    :return: xml for menu, [(bot_action, label), ...], [(menu_action, label), ...]
    """
    # pre 3.12 menus
    examples_dir = get_example_dir()
    if not examples_dir:
        return "", [], []

    root_dir = root_dir or examples_dir

    file_tmpl = '<menuitem name="{name}" action="{action}"/>'
    dir_tmpl = '<menu name="{name}" action="{action}">{menu}</menu>'

    file_actions = []
    submenu_actions = []

    xml = ""

    for fn in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, fn)
        rel_path = path[len(examples_dir):]
        if fn != '__pycache__' and os.path.isdir(path):
            action = 'ShoebotExampleMenu {0}'.format(rel_path)
            label = fn.capitalize()

            sm_xml, sm_file_actions, sm_menu_actions = examples_menu(os.path.join(root_dir, fn), depth + 1)

            submenu_actions.extend(sm_menu_actions)
            file_actions.extend(sm_file_actions)
            submenu_actions.append((action, label))
            xml += dir_tmpl.format(name=fn, action=action, menu=sm_xml)
        elif os.path.splitext(path)[1] in ['.bot', '.py'] and not fn.startswith('_'):
            action = 'ShoebotExampleOpen {0}'.format(rel_path)
            label = make_readable_filename(fn)

            xml += file_tmpl.format(name=fn, action=action)
            file_actions.append((action, label))

    return xml, file_actions, submenu_actions


def gedit3_menu(xml):
    """
    Build XML for GEDIT3 Menus.

    Pass in the xml returned by example_menu
    """
    # pre 3.12 menus
    return MENU_UI.format(xml)  # Splice in the examples menu


if __name__ == '__main__':
    # Debug - create the configuration
    win = Gtk.Window()
    win.add(ShoebotPreferences())
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
