import sys


def get_editor_class():
    """
    :return:editor class such as gi.repository.Gedit
    """
    for editor in ['Gedit', 'Xed']:
        try:
            Editor = __import__('gi.repository.{}'.format(editor), fromlist=editor)
            return Editor
        except ImportError:
            pass
    else:
        sys.stderr.write('Unknown editor\n')


Editor = get_editor_class()
