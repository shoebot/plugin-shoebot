from gi.repository import Gtk


def apply_panel_shims(panel):
    if not hasattr(panel, "add_titled"):
        if hasattr(panel, "add_item"):
            arg = panel.add_item.get_arguments()[-1].get_name()
            if arg == 'icon_name':
                def add_titled(panel, item, name, display_name):
                    # In Xed, add_item takes an icon name
                    panel.add_item(item, display_name, Gtk.STOCK_EXECUTE)

                panel.add_titled = add_titled.__get__(panel)
            elif arg == 'image':
                def add_titled(panel, item, name, display_name):
                    # In Pluma, add_item the last parameter is image:Gtk.Image
                    empty_icon = Gtk.Image()
                    panel.add_item(item, display_name, empty_icon)

                panel.add_titled = add_titled.__get__(panel)
            else:
                print("Warning - no shim for add_titled")


# window shims
def shim_create_tab_from_location(window):
    if not hasattr(window, "create_tab_from_location"):
        if hasattr(window, "create_tab_from_uri"):
            # Pluma has the older create_tab_from_uri API
            def create_tab_from_location(window, location, encoding, line_pos, column_pos, create, jump_to):
                uri = location.get_uri()  # location is a GFile
                window.create_tab_from_uri(uri,
                                           encoding,
                                           0,
                                           False,  # Do not create a new file
                                           True)  # Switch to tab

            window.create_tab_from_location = create_tab_from_location.__get__(window)
    elif hasattr(window, "create_tab_from_location"):
        # Xed doesn't have the column_pos parameter
        f = window.create_tab_from_location
        window.__create_tab_from_location__ = f
        param_names = [arg.get_name() for arg in window.create_tab_from_location.get_arguments()]
        if 'column_pos' not in param_names:
            def create_tab_from_location(window, location, encoding, line_pos, column_pos, create, jump_to):
                f(location, encoding, line_pos, create, jump_to)
                if column_pos:
                    raise NotImplementedError('column_pos not implemented')

            window.create_tab_from_location = create_tab_from_location.__get__(window)


def apply_editor_shims(editor_class):
    if not hasattr(editor_class, "encoding_get_current"):
        # Shim for Xed -
        editor_class.encoding_get_current = (lambda self: None).__get__(editor_class)


def apply_shims(editor_class, window):
    panel = window.get_bottom_panel()
    apply_editor_shims(editor_class)
    apply_panel_shims(panel)

    shim_create_tab_from_location(window)
