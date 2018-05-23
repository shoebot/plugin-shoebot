import errno
import os
import shutil

from os.path import isdir
from distutils.dir_util import copy_tree


def recursive_copy(src, dest_dir):
    if isdir(src):
        copy_tree(src, dest_dir)
    else:
        shutil.copy2(src, dest_dir)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and isdir(path):
            pass
        else:
            raise
