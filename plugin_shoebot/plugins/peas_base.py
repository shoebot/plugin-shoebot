import sys

class EditorShims:
    pass

class XedShims(EditorShims):
    #class WindowActivatable:
    #    pass
    pass

def apply_shims(ShimKlass, Editor):
    ShimKlass = getattr(globals(), Editor.__name__, None)
    print("apply_shims: ", Editor, ShimKlass)


def get_shims(editor):
    return globals().get("{}Shims".format(editor))

def get_editor_class():
    """
    :return:editor class such as gi.repository.Gedit
    """
    for editor in ['Gedit', 'Xed', 'Pluma']:
        try:
            Editor = __import__('gi.repository.{}'.format(editor), fromlist=editor)
        except ImportError:
            continue
        ShimKlass = get_shims(editor)
        if ShimKlass is not None:
            apply_shims(ShimKlass, Editor)
        return Editor
    else:
        sys.stderr.write('Unknown editor\n')


Editor = get_editor_class()

if Editor is None:
    EDITOR_NAME = None
else:
    EDITOR_NAME = Editor.__class__.__name__.lower()
