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
        print("No create_tab_from_location - probably pluma")
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


def apply_shims(window):
    panel = window.get_bottom_panel()
    apply_panel_shims(panel)

    shim_create_tab_from_location(window)
