from __future__ import print_function

import glob
import os
import shutil
import sys

from plugin_shoebot.install import plugins

description = 'Integrate and control shoebot from editors or anything else',
here = os.path.dirname(os.path.abspath(__file__))

try:
    from setuptools import setup, Command, find_packages
    from setuptools.command.install import install
except ImportError:
    sys.exit("Install setuptools before plugin-shoebot")


class InstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    description = "Installs plugin-shoebot"

    available_plugins = set(plugins)

    user_options = install.user_options + [
        ('plugins=', None, 'Install gedit plugin.'),
    ]

    def initialize_options(self):
        self.plugins = None
        install.initialize_options(self)

    def get_outputs(self):
        outputs = []
        from plugin_shoebot.install import plugins
        for name, plugin_klass in plugins.items():
            plugin = plugin_klass()
            outputs.extend(plugin.get_outputs())
        return outputs

    def finalize_options(self):
        if self.plugins is None:
            self.plugins = InstallCommand.available_plugins
        else:
            self.plugins = set(self.plugins.split())
            if 'all' in self.plugins:
                self.plugins.pop('all')
                self.plugins.update(InstallCommand.available_plugins)
            if not self.plugins.issubset(InstallCommand.available_plugins):
                valid_plugins = ' '.join(InstallCommand.available_plugins)
                invalid_plugins = ' '.join(self.plugins.difference(InstallCommand.available_plugins))
                sys.stderr.write('Invalid plugins specified: "%s", valid plugins: "%s"\n' % (invalid_plugins, valid_plugins))
                sys.exit(1)
        for plugin in self. plugins:
            pass
        install.finalize_options(self)

    def run(self):
        from plugin_shoebot.install import plugins
        for name, plugin_klass in plugins.items():
            plugin = plugin_klass()
            plugin.copy_files()


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)

setup(
    name='plugin_shoebot',
    version='0.1.0',
    url='https://github.com/shoebot/plugin-shoebot.git',
    author='Stuart Axon',
    author_email='stu.axon@gmail.com',
    description=description,
    packages=find_packages(),
    cmdclass={
        'clean': CleanCommand,
        'install': InstallCommand
    },
)
