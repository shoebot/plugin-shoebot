import errno
import os
import shutil

from os.path import isdir, islink, join, exists, lexists
from distutils.dir_util import copy_tree


# def copytree(src, dst, symlinks=False, ignore=None):
#     """
#     copytree that works even if folder already exists
#     """
#     # http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
#     if not exists(dst):
#         os.makedirs(dst)
#         shutil.copystat(src, dst)
#     lst = os.listdir(src)
#     if ignore:
#         excl = ignore(src, lst)
#         lst = [x for x in lst if x not in excl]
#     for item in lst:
#         s = join(src, item)
#         d = join(dst, item)
#         if symlinks and islink(s):
#             if lexists(d):
#                 os.remove(d)
#             os.symlink(os.readlink(s), d)
#             if hasattr(os, 'lchmod'):
#                 st = os.lstat(s)
#                 mode = stat.S_IMODE(st.st_mode)
#                 os.lchmod(d, mode)
#         elif isdir(s):
#             copytree(s, d, ignore)
#         else:
#             shutil.copy2(s, d)


def recursive_copy(src, dest_dir):
    print(src, dest_dir)
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
