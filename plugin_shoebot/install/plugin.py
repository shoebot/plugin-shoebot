import sys

from os.path import abspath, dirname, expanduser, expandvars, isdir, join, normpath

from plugin_shoebot.install.user import has_admin
from .fileops import mkdir_p, recursive_copy

here = dirname(abspath(__file__))
project_dir = normpath(join(here, '../..'))

field_lookups = [
    '{platform}_{user_type}_{name}',
    '{platform}_{name}',
    '{user_type}_{name}',
    '{name}',
]


class PluginInstaller(object):
    """
    Plugin that can be installed into different directories depending
    on operating system and if the user is an admin or not.

    target_dirs:
        list of directories for the PluginInstaller to use.
        install_dir:  base directory

    directories can be specified directly, e.g.

    install_dir = '/opt/my-plugin'

    Or with modifiers, for platform and user_type in that order

    nt_install_dir = 'c:\\my-plugin'
    linux2_install_dir = '/opt/my-plugin'

    user_type:  can be 'admin' or 'user'

    nt_admin_install_dir = r'c:\Program Files\my-plugin'
    """
    vars = []
    after_copy = []
    target_dirs = ['install_dir']

    initial_context = dict(
        plugin_shoebot=join(project_dir, 'plugin_shoebot'),
        plugin_data=join(here, 'plugin_data')
    )

    @classmethod
    def _expand_dir(cls, value, **fmt_vars):
        if type(value) is list:
            for _value in value:
                _value = cls._expand_dir(_value, **fmt_vars)
                if isdir(_value):
                    return _value
            else:
                return None

        if value[0] == '~':
            value = expanduser(value)
        value = expandvars(value)
        value = value.format(**fmt_vars)
        return value

    @classmethod
    def resolve_vars(cls):
        return {name: getattr(cls, name) for name in cls.vars}

    @classmethod
    def resolve_dir(cls, is_admin, platform, target, **kwargs):
        user_type = 'admin' if is_admin else 'user'

        context_vars = dict(
            user_type=user_type,
            platform=platform,
            name=target,
        )

        for lookup in field_lookups:
            fmt_vars = cls.resolve_vars()
            fmt_vars.update(**kwargs)
            fmt_vars.update(**context_vars)
            field_name = lookup.format(**fmt_vars)
            value = getattr(cls, field_name, None)
            if value is not None:
                value = cls._expand_dir(value, **fmt_vars)
                return value

    @classmethod
    def resolve_dirs(cls):
        is_admin = has_admin()
        platform = sys.platform

        fmt_vars = cls.resolve_vars()

        result = {}
        result.update(cls.initial_context)
        for target in cls.target_dirs:
            target_dir = cls.resolve_dir(is_admin, platform, target, **fmt_vars)
            result[target] = target_dir
            fmt_vars[target] = target_dir

        return result

    def call_after_copy(self, directories):
        for f in self.after_copy:
            f(self, directories)

    def resolve_all(self):
        paths = self.resolve_dirs()
        paths.update(self.resolve_vars())
        return paths

    def src_dests(self, targets):
        for src, dest in self.copy:
            _src = src.format(**targets)
            _dest = dest.format(**targets)
            yield _src, _dest

    def copy_files(self):
        targets = self.resolve_all()
        for src, dest in self.src_dests(targets):
            mkdir_p(dest)
            recursive_copy(src, dest)

        self.call_after_copy(targets)

    def get_outputs(self):
        targets = self.resolve_all()
        for src, dest in self.src_dests(targets):
            yield dest
