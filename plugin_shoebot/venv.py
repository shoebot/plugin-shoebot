import os
import sys

from os.path import abspath, dirname, expanduser, expandvars, isfile, join, normpath, pathsep, relpath

PYTHON_BIN = os.path.basename(sys.executable)


def interpreter_environment(python):
    """
    :param python:  absolute path to python executable
    :return:  path to environment for python
    """
    return dirname(dirname(python))


def get_system_environment():
    """
    :return:  Path to system pythons environment
    """
    env_venv = os.environ.get('VIRTUAL_ENV')
    if not env_venv:
        return interpreter_environment(sys.executable)

    # First python in path that is not in current venv
    for p in os.environ['PATH'].split(pathsep):
        python = '%s/%s' % (p, PYTHON_BIN)
        if not p.startswith(env_venv) and isfile(python):
            return interpreter_environment(sys.executable)

    return interpreter_environment(sys.executable)


def get_current_environment():
    """
    :return:  Python environment with first python in the PATH
    """
    return interpreter_environment(sys.executable)


def is_virtualenv(directory):
    """
    :param directory: base directory of python environment
    """
    path = os.path.join(directory, PYTHON_BIN)
    return os.path.isfile(path)


def virtualenv_interpreter(venv):
    return virtualenv_binary(venv, PYTHON_BIN)


def virtualenv_binary(venv, binary):
    return os.path.join(venv, 'bin', binary)


def virtualenv_has_binary(venv, binary):
    """
    :param script: script to look for in bin folder
    """
    path = virtualenv_binary(venv, binary)
    return os.path.isfile(path), path


def virtualenvwrapper_envs(filter=None):
    """
    :return: python environments in ~/.virtualenvs

    :param filter: if this returns False the venv will be ignored

    >>> virtualenvwrapper_envs(filter=virtualenv_has_script('pip'))
    """
    vw_home = abspath(expanduser(expandvars('~/.virtualenvs')))
    venvs = []
    for directory in os.listdir(vw_home):
        venv = join(vw_home, directory)
        if is_virtualenv(venv):
            if filter and not filter(venv):
                continue
            venvs.append(venv)
    return sorted(venvs)
