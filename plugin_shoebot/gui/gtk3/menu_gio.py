import base64
import os

from gi.repository import Gio
from plugin_shoebot.gui.gtk3.preferences import preferences
from plugin_shoebot.utils import make_readable_filename


def encode_relpath(rel_path):
    # 3.12+ menus
    b64_path = base64.b64encode(rel_path.encode('UTF-8')).decode("UTF-8")
    return b64_path


def example_menu_actions(text, root_dir=None, depth=0):
    """
    Traverse examples directory and get relative filenames
    and relative filenames

    :return: base_item, [rel_paths...]
    """
    # GMenu (Gedit 3.12+ menus)
    examples_dir = preferences.example_dir
    if not examples_dir:
        return None, []

    root_dir = root_dir or examples_dir

    file_actions = []

    menu = Gio.Menu.new()
    base_item = Gio.MenuItem.new_submenu(text, menu)

    for fn in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, fn)
        rel_path = path[len(examples_dir):]
        if os.path.isdir(path):
            label = fn.capitalize()

            item, sm_file_actions = example_menu_actions(label, os.path.join(root_dir, fn))
            menu.append_item(item)

            file_actions.extend(sm_file_actions)
        elif os.path.splitext(path)[1] in ['.bot', '.py'] and not fn.startswith('_'):
            label = make_readable_filename(fn)

            # the only way I could work out to attach the data to the menu item is in the name :/
            action_name = "win.open_example__%s" % encode_relpath(rel_path)

            menu.append(label, action_name)
            file_actions.append(rel_path)

    return base_item, file_actions
