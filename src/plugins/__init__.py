# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010-2024  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.

"""
Load plugins in bumpo.
Custom classes to be used instead of baseObjects's GameObject or Shape
must be derived from them (or subclasses of).

Each plugin module can have a module-level variable called "MODULE_PLUGINS"
as a sequence of plugin's object names (a class, a function or whatever)
which can be passed to the load_plugin function for get back the plugin object. # XX+TODO: review this

"""

try:
    import importlib
    HAVE_IMPORTLIB = 1
except ImportError:
    import imp
    HAVE_IMPORTLIB = 0
import glob
import os
import sys


class LoadPluginError(Exception):
    pass

def _load_plugin (name, module):
    """Returns the plugin's object name (a class, function or whatever)
    from module.
    """
    mod = __import__(module, fromlist=[name])
    return getattr(mod, name)


def get_module (module, paths=None):
    """Returns the module found in paths or None.

    module => module name to get.
    paths  => a sequence of paths in which search the module.
              If omitted or None, search in sys.path.
    """
    # importlib mess... o.O
    if HAVE_IMPORTLIB:
        for path in list(paths or sys.path):
            for p in find_plugins(path):
                spec = importlib.util.spec_from_file_location(module, p)
                if spec is not None:
                    mod = importlib.util.module_from_spec(spec)
                    if mod is not None:
                        sys.modules[module] = mod
                        spec.loader.exec_module(mod)
                        return mod
    else:
        file, path, descr = imp.find_module(module, paths)
        return imp.load_module(module, file, path, descr)


def find_plugins (path=None):
    import fnmatch
    if path is None:
        path = os.path.dirname(__file__)
    modules = [p for p in glob.glob(os.path.join(path, '*.py'))
               if not fnmatch.fnmatch(p, '*/__init__.py')]
    return tuple(modules)


def find_plugin_modules (path=None):
    """Returns a list of plugin modules found in path.

    path => path to a directory containing plugin modules.
            If not provided or None, search in the default
            location.
    """
    if path is None:
        path = os.path.dirname(__file__)
    modules = [os.path.splitext(os.path.basename(f))[0]
               for f in find_plugins(path)]
    return tuple(modules)


def load_plugin (name, module, paths=None):
    """Returns the plugin's object name (a class, function or whatever)
    from module in paths.
    Raise a LoadPluginError exception if something goes wrong.

    name   => plugin's object  name (a class, function or whatever)
    module => plugin's module
    paths  => a sequence of path in which search for the plugin. If omitted
              of None, default to sys.path.
    """
    try:
        mod = get_module(module, paths)
        return getattr(mod, name)
    except Exception as err:
        raise LoadPluginError(err)
