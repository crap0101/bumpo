
"""
Load plugins in bumpo.
Custom classes to be used instead of baseObjects's GameObject or Shape
must be derived from them (or subclasses of), or regiter themself
within the BaseGameObject or BaseShape abstract classes, respectively.

Each plugin module can have a module-level variable called "MODULE_PLUGINS"
as a sequence of plugin's object names (a class, a function or whatever)
which can be passed to the load_plugin function for get back the plugin object.

"""

import glob
import imp
import os


class LoadPluginError(Exception):
    pass

def _load_plugin (name, module):
    """Returns the plugin's object name (a class, function or whatever)
    from module.
    """
    mod = __import__(module, fromlist=[name])
    return getattr(mod, name)


def get_module (module, paths=None):
    """Returns the module found in paths.

    module => module name to get.
    paths  => a sequence of paths in which search the module.
              If omitted or None, search in sys.path.
    """
    file, path, descr = imp.find_module(module, paths)
    return imp.load_module(module, file, path, descr)


def load_plugin (name, module, paths=None):
    """Returns the plugin's object name (a class, function or whatever)
    from module in paths.
    Raise a LoadPluginError exception if something goes wrong.

    name   => plugin's object  name (a class, function or whatever)
    module => plugin's module
    paths  => a sequence of path in which search for the plugin. If omitted
              of None, default to sys.path.
    """
    file = None
    try:
        mod = get_module(module, paths)
        return getattr(mod, name)
    except Exception as err:
        raise LoadPluginError(err)
    finally:
        if file:
            file.close()


def find_plugin_modules (path=None):
    """Returns a list of plugin modules found in path.
    
    path => path to a directory containing plugin modules.
            If not provided or None, search in the default
            location.
    """
    if path is None:
        path = os.path.dirname(__file__)
    modules = [os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(os.path.join(path, '*.py'))]
    try:
        modules.remove('__init__')
    except ValueError:
        pass
    return tuple(modules)
