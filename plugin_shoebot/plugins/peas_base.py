import sys


def get_editor_class():
    """
    :return:editor class such as gi.repository.Gedit
    """
    for editor in ['Gedit', 'Xed', 'Pluma']:
        try:
            Editor = __import__('gi.repository.{}'.format(editor), fromlist=editor)
            return Editor
        except ImportError:
            pass
    else:
        sys.stderr.write('Unknown editor\n')


Editor = get_editor_class()

if Editor is None:
    EDITOR_NAME = None
else:
    EDITOR_NAME = Editor.__class__.__name__.lower()
