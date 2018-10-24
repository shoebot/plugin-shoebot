from gi.repository import Gio, GLib


def action_prefix(value):
    if value in [True, False]:
        return 'toggle'
    else:
        return 'on'


def action_data_name_text_value(name, text, value=None):
    return name, text, value


def action_data_name_value(name, _text, value=None):
    return name, value


class GioActionHelperMixin:
    def create_actions(self, actions_data):
        """
        Create many menu options by calling create_action
        for each item in the passed in list.

        See create_action
        """
        for action_data in actions_data:
            name, value = action_data_name_value(*action_data)
            self.create_action(name, value)

    def create_action(self, name, value=None):
        """
        Create standard or toggleable menu options and hook
        them up to actions on implementing class.

        :param name: action name
        :param text: Not used
        :param value: None|True|False
             if None then a standard menu action will be created and linked
             to a handler function named on_{name}

             If a boolean is passed then a toggle action will be created
             and on_toggle_{name} will be called after toggling the option.
        :return:
        """
        if value is None:
            self.create_standard_action(name)
        elif value in [True, False]:
            self.create_toggle_action(name, value)
        else:
            raise ValueError('Unknown Action: {}'.format(str(action_data)))

    def create_standard_action(self, name):
        action_name = "on_%s" % name
        action = Gio.SimpleAction.new(name=action_name)
        action.connect("activate", getattr(self, action_name))
        self.window.add_action(action)
        return action

    def create_toggle_action(self, name, value=False):
        """
        Create Gio Simple Action and hook it up to a function
        that toggles a boolean.

        See create_toggle_handler for info on the handler.

        :param name: name, e.g. toggle_livecoding
        :param value:  initial value
        :return: the created action
        """
        action_name = "toggle_%s" % name
        action = Gio.SimpleAction.new_stateful(
            action_name,
            None,
            GLib.Variant.new_boolean(value))
        handler = self.create_toggle_handler(name, value)
        action.connect("activate", handler)
        self.window.add_action(action)
        return action

    def create_toggle_handler(self, name, value=False):
        """
        Create a handler that:
            toggles the GLib action
            sets a variable names like {name}_enabled
            calls a function named like on_toggle_{name}

        :param name: variable prefix, full name will be {name}_enabled
        :param value: initial value
        """
        def default_toggle_handler(action, user_data):
            enabled = not action.get_state().get_boolean()
            action.set_state(GLib.Variant.new_boolean(enabled))
            setattr(self, "{}_enabled".format(name), enabled)

            handler = getattr(self, "on_toggle_{name}".format(name=name), None)
            if handler:
                handler(action, user_data)

        setattr(self, "{}_enabled".format(name), value)
        default_toggle_handler.__name__ = "call_toggle_{}".format(name)
        return default_toggle_handler
