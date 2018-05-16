#!/usr/bin/python

# TODO - Test on gedit-3 for windows

from __future__ import print_function

import errno
import os
import shutil
import stat
import sys
from abc import ABCMeta
from os.path import abspath, dirname, exists, expanduser, expandvars, isdir, islink, lexists, join, normpath

here = dirname(abspath(__file__))


def has_admin():
    if os.name == 'nt':
        try:
            # only windows users with admin privileges can read the C:\windows\temp
            os.listdir(os.sep.join([os.environ.get('SystemRoot', 'C:\\windows'), 'temp']))
        except:
            return os.environ['USERNAME'], False
        else:
            return os.environ['USERNAME'], True
    else:
        if 'SUDO_USER' in os.environ and os.geteuid() == 0:
            return os.environ['SUDO_USER'], True
        else:
            return os.environ['USER'], False


def copytree(src, dst, symlinks=False, ignore=None):
    """
    copytree that works even if folder already exists
    """
    # http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
    if not exists(dst):
        os.makedirs(dst)
        shutil.copystat(src, dst)
    lst = os.listdir(src)
    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]
    for item in lst:
        s = join(src, item)
        d = join(dst, item)
        if symlinks and islink(s):
            if lexists(d):
                os.remove(d)
            os.symlink(os.readlink(s), d)
            if hasattr(os, 'lchmod'):
                st = os.lstat(s)
                mode = stat.S_IMODE(st.st_mode)
                os.lchmod(d, mode)
        elif isdir(s):
            copytree(s, d, ignore)
        else:
            shutil.copy2(s, d)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_dirs_nt(is_admin, app_name, app_plugin_name=None):
    """
    :param is_admin:         True if user has admin
    :param app_name:         app name, e.g. "gedit
    :param app_plugin_name:  plugin subdirectory directory e.g. gedit-3
    :return:  dest_dir, language_dir, plugin_dir
    """
    if app_plugin_name is None:
        app_plugin_name = app_name

    if is_admin:
        dest_dir = expandvars("%ProgramFiles%\\%s" % app_name)
        language_dir = expandvars("%ProgramFiles%\\%s\\share\\gtksourceview-3.0\\language-specs" % app_name)
        plugin_dir = expandvars("%ProgramFiles%\\%s\\lib\\%s\\plugins" % (app_name, app_plugin_name))
    else:
        dest_dir = expandvars("%UserProfile%//AppData//Roaming")
        language_dir = None
        plugin_dir = join(dest_dir, "%s//plugins" % app_name)

    return dest_dir, language_dir, plugin_dir


def get_dirs_unix(is_admin, app_name, **kwargs):
    """
    :param is_admin:         True if user has admin
    :param app_name:         app name, e.g. "gedit
    :return:  dest_dir, language_dir, plugin_dir
    """
    if is_admin:
        if isdir('/usr/lib64'):
            dest_dir = "/usr/lib64"
        else:
            dest_dir = "/usr/lib"
    else:
        dest_dir = expanduser("~/.local/share")

    language_dir = join(dest_dir, "gtksourceview-3.0/language-specs")
    plugin_dir = join(dest_dir, "%s/plugins" % app_name)

    return dest_dir, language_dir, plugin_dir


if os.name == 'nt':
    get_dirs = get_dirs_nt
else:
    get_dirs = get_dirs_unix


PLUGINS_DIR = '../plugins/'
PLUGIN_DIR = '%s/gedit/gedit3.12-plugin' % PLUGINS_DIR


class PeasPlugin:
    __metaclass__ = ABCMeta

    plugin_subdirectory = None
    lang_file = None

    def __init__(self):
        assert hasattr(self, 'name')
        assert hasattr(self, 'source_dirs')

    def install(self):
        print('install peas')
        username, is_admin = has_admin()
        dest_dir, language_dir, plugin_dir = \
            get_dirs(is_admin, self.app_name, self.plugin_subdirectory)

        if is_admin and not isdir(plugin_dir):
            print('%s not found' % self.name)
            sys.exit(1)
        else:
            if not is_admin:
                try:
                    os.makedirs(plugin_dir)
                except OSError:
                    pass

                if not isdir(plugin_dir):
                    print('Could not create destination directory: %s' % plugin_dir)
                    sys.exit(1)

        print('Install %s plugin to %s' % (self.name, dest_dir))

        def ignore(src, lst):
            # Have list of directories to ignore ^ somehow
            #
            # Root based on project-root
            #
            # Maybe create ignore func with each sourcedir
            src = os.path.abspath(src)

            print("ignore ? %s: %s" % (src, None))
            print(src == os.path.abspath(PLUGIN_DIR))
            print(src)
            print(PLUGINS_DIR)
            print()
            return lst

        for source_dir in self.source_dirs:
            source_dir = os.path.normpath(source_dir)
            print('copytree %s %s' % (source_dir, plugin_dir))
            copytree(source_dir, plugin_dir, ignore=ignore)

        if self.lang_file and language_dir:
            mkdir_p(language_dir)
            shutil.copyfile(self.lang_file, join(language_dir, "shoebot.lang"))
            os.system("update-mime-database %s/mime" % dest_dir)

        os.system("glib-compile-schemas %s/%s/plugins/shoebotit" % (dest_dir, self.app_name))


class GeditGioPlugin(PeasPlugin):
    name = 'Gedit-3.12'

    app_name = 'gedit'
    plugin_subdirectory = 'gedit-3'

    lang_file = '%s/shoebot.lang' % PLUGIN_DIR
    source_dirs = [
        PLUGINS_DIR,
        normpath(join(here, '../../plugin_shoebot')),
        PLUGIN_DIR,
    ]

    def __init__(self):
        PeasPlugin.__init__(
            self,
        )


# def main():
#     source_dirs = [here, normpath(join(here, '../../lib'))]
#     username, is_admin = has_admin()
#
#     dirs = get_dirs(is_admin, 'gedit', 'gedit-3')
#     kwargs = dict(
#         name="gedit-3.12",
#         source_dirs=source_dirs,
#         is_admin=is_admin,
#         **dirs
#     )
#
#     install_plugin(**kwargs)


def main2():
    plugin = GeditPluginGio()
    plugin.install()


if __name__ == '__main__':
    main2()
