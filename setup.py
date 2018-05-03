from __future__ import print_function

import glob
import os
import shutil
import sys

description = 'Integrate and control shoebot from editors or anything else',
here = os.path.dirname(os.path.abspath(__file__))

try:
    from setuptools import setup, Command, find_packages
except ImportError:
    sys.exit("Install setuptools before plugin-shoebot")


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
    },
)
