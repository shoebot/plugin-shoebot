from __future__ import print_function

import glob
import os
import shutil
import sys

from setuptools.command.easy_install import easy_install
from plugin_shoebot.install import get_plugin_outputs, install_plugins, parse_plugin_names

description = 'Integrate and control shoebot from editors or anything else',
here = os.path.dirname(os.path.abspath(__file__))

try:
    from setuptools import setup, Command, find_packages, Distribution
    from setuptools.command.install import install
    from distutils.command.clean import clean
except ImportError:
    sys.exit("Install setuptools before plugin-shoebot")


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


class EasyInstallWithPTH(easy_install):
    """ Installs shoebot plugins."""
    description = "Installs plugin-shoebot"
    user_options = install.user_options + [
        ('plugins=', None, 'Install gedit plugin.'),
    ]

    def initialize_options(self):
        self.plugins = None
        install.initialize_options(self)

    def get_outputs(self):
        return get_plugin_outputs()

    def finalize_options(self):
        self.plugins = parse_plugin_names(self.plugins)
        install.finalize_options(self)

    def run(self):
        install_plugins(self.plugins)
        return install.run(self)


class InstallCommand(install):
    """ Installs shoebot plugins."""
    description = "Installs plugin-shoebot"
    user_options = install.user_options + [
        ('plugins=', None, 'Install gedit plugin.'),
    ]

    def initialize_options(self):
        self.plugins = None
        install.initialize_options(self)

    def get_outputs(self):
        return get_plugin_outputs()

    def finalize_options(self):
        self.plugins = parse_plugin_names(self.plugins)
        install.finalize_options(self)

    def run(self):
        install_plugins(self.plugins)
        return install.run(self)


class CleanCommand(clean):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split()

    user_options = clean.user_options

    def initialize_options(self):
        return clean.initialize_options(self)

    def finalize_options(self):
        return clean.finalize_options(self)

    def run(self):
        global here
        clean.run(self)

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
    version='0.1.6',
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
