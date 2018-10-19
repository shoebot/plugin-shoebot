import os
import sys

from os.path import abspath, dirname, expanduser, expandvars, isfile, join, pathsep

DEFAULT = 'default'
SYSTEM = 'system'

PYTHON_BIN = os.path.basename(sys.executable)

PYTHON2 = 'python2'
PYTHON3 = 'python3'
CURRENT_PYTHON = os.path.basename(sys.executable)
ANY_PYTHON = [PYTHON2, PYTHON3]


PYTHON_BINS = [PYTHON2, PYTHON3]


def interpreter_environment(python):
    """
    :param python:  absolute path to python interpreter
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


def is_virtualenv(venv, interpreters=[CURRENT_PYTHON]):
    """
    :param venv: base directory of python environment
    """
    for interpreter in interpreters:
        if virtualenv_has_binary(venv, interpreter)[0]:
            return True
    return False


def is_interpreter(python_bin):
    return python_bin == PYTHON_BIN


def virtualenv_interpreter(venv, interpreters=ANY_PYTHON):#
    for interpreter in interpreters:
        has_interpreter, path = virtualenv_has_binary(venv, interpreter)
        if has_interpreter:
            return path
    return None


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
