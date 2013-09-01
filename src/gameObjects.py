# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.

"""
This module contains the basic stuffs needed to build and use
various type of game objects.

"""


# std imports
from collections import OrderedDict
# local imports
from baseObjects import GameObject, Shape, Board
import gameUtils
from gameUtils import Table
from const import WIDTH, HEIGHT, CENTER
# external imports
import pygame


class GenericGameObject (GameObject):
    _reload_on_resize = True
    """
    A generic game object. Provide methods for drawing,
    moving, resizing, comparing game objects, etc.
    """
    def __init__ (self, obj=None, cmp_value=None, reload=None):
        """
        TODO: doc
        create a new game object for a BaseShape, pygame.Surface, file
        if reload == None use the class-level attribute.
        """
        if isinstance(obj, basestring):
            self._filepath = obj
            obj = gameUtils.surface_from_file(obj)
        else:
            self._filepath = None
        super(GenericGameObject, self).__init__(obj, cmp_value)
        self.convert()
        self._orig_shape = self.shape
        if reload is not None:
            self._reload_on_resize = bool(reload)

    @property
    def reload (self): 
        """
        Returns the boolean value used by other methods (resize, fit, etc.)
        for decide if reload the object's source image before doing their job.
        """
        return self._reload_on_resize
    @reload.setter
    def reload (self, value):
        """
        If set to a true value, resizing, fitting or any other operation
        which cause changing the object's dimensions will be performed
        possibly reloading the original shape image (Shape, GameObject
        or whatever) if information loss can happen.
        """
        if value and self._filepath:
            size = self.size
            self._shape = self._shape.__class__(
                gameUtils.surface_from_file(self._filepath))
            self.convert()
            self.resize(*size)
        self._reload_on_resize = bool(value)

    def fit (self, obj):
        """
        Move and resize this object to fit obj, which can be either a Shape
        or a GameObject. The aspect ratio of the object is preserved, so the
        new size may be smaller than the target in either width or height.
        """
        if self._reload_on_resize:
            if obj.w > self.w or obj.h > self.h:
                if self._filepath:
                    self._shape = self._shape.__class__(
                        gameUtils.surface_from_file(self._filepath))
                    self.convert()
                else:
                    self._shape = self._orig_shape.copy()
        super(GenericGameObject, self).fit(obj)

    def resize (self, width, height, anchor=CENTER):
        """
        Resize this object at (width, height) size.
        anchor (default CENTER) is the object's invariant point
        to be preserved after resizing.
        """ 
        fp = getattr(self, anchor)
        if self._reload_on_resize:
            if width > self.w or height > self.h:
                if self._filepath:
                    self._shape = self._shape.__class__(
                        gameUtils.surface_from_file(self._filepath))
                    self.convert()
                else:
                    self._shape = self._orig_shape.copy()
        super(GenericGameObject, self).resize(width, height)
        self.move_at(fp, anchor)

    def resize_perc_from (self, obj, perc, anchor=CENTER):
        """Resize this object at obj's perc size."""
        w, h = gameUtils.scale_perc(obj.w, obj.h, perc)
        self.resize(w, h, anchor)

    def scale_perc (self, perc, anchor=CENTER):
        """Scale this object by perc, e.g with perc=50, scale at 50%."""
        w, h = gameUtils.scale_perc(self.w, self.h, perc)
        self.resize(w, h, anchor)

    def scale_perc_from (self, obj, perc, dim=HEIGHT, anchor=CENTER):
        """Scale this object at the perc length of obj's
        dimension dim (default HEIGHT).
        """
        w, h = gameUtils.scale_perc_from(obj.w, obj.h, perc, dim)
        length = w if dim == WIDTH else h
        w, h = gameUtils.scale_from_dim(self.w, self.h, length, dim)
        self.resize(w, h, anchor)

    def scale_from_dim (self, length, dim=HEIGHT, anchor=CENTER):
        """Scale the object by the dim-relative length."""
        w, h = gameUtils.scale_from_dim(self.w, self.h, length, dim)
        self.resize(w, h, anchor)

    #XXX+TODO
    def _rotate (self, angle, anchor_at='center'):
        """
        Rotate the object's surface by *angle* amount. Could be a float value.
        Negative angle amounts will rotate clockwise. *anchor_at* is the rect
        attribute used for anchor the rotated rect (default to 'center').
        """
        raise NotImplementedError


class TextImage (GenericGameObject):
    """Create a game object for display text."""
    def __init__ (self, obj, fname, fsize, fgc, bgc=None, cmp_value=None):
        """
        Create a TextImage object: *obj* can be the string to be displayed
        or another TextImage object or anything with a text attribute which
        will be used as the text to display.
        *fname* can be either a filename or a font name, in the latter
        case the font must be present in the system, otherwise a random
        available font is used instead;
        *fsize* is the initial size of the font.
        *fgc* is the foreground color, used for blit the text.
        *bgc* is the background color (default to None, i.e. transparent).
        """
        if isinstance(obj, basestring):
            self._text = obj
        else:
            self._text = obj.text
        self._fname = fname
        self._fsize = fsize
        self._bgc = bgc
        self._fgc = fgc
        self._font = None  # the font returned by _build_font
        self._build_font(fname, fsize)
        super(TextImage, self).__init__(self._build_surface(), cmp_value)

    def _build_surface (self):
        """Builds and returns the object's surface."""
        # NOTE: pygame BUG
        # Cfr. http://pygame.motherhamster.org/bugzilla/show_bug.cgi?id=49
        # fixed: http://hg.pygame.org/pygame/changeset/6cc8196e0181
        if self._bgc is None:
            return self._font.render(
                self.text.decode('utf-8'), True, self._fgc)
        return self._font.render(
            self.text.decode('utf-8'), True, self._fgc, self._bgc)
        
    def _build_font (self, name, size):
        """Build the font."""
        self._fname = name
        self._fsize = size
        try:
            self._font = pygame.font.Font(self._fname, self._fsize)
        except IOError:
            self._font = pygame.font.SysFont(self._fname, self._fsize)
        except RuntimeError:
            self._font = pygame.font.SysFont(
                ','.join(pygame.font.get_fonts()), self._fsize)

    @property
    def bg (self):
        """Returns the background color."""
        return self._bgc
    @property
    def fg (self):
        """Returns the foreground color."""
        return self._fgc
    @property
    def fname (self):
        """Returns the font name."""
        return self._fname
    @property
    def fsize (self):
        """Returns the font size."""
        return self._fsize
    @property
    def text (self):
        """Returns the object's text as a string."""
        return self._text

    def resize (self, w, h, anchor=CENTER):
        """
        Resize the object at the given width and height,
        rebuilding the font and the object's surface.
        anchor (default CENTER) is the object's invariant point
        to be preserved after resizing.
        """ 
        fp = getattr(self, anchor)
        fw, fh = self._font.size(self.text)
        self._fsize = max((self._fsize * h / fh, self._fsize * w / fw))
        self._build_font(self._fname, self._fsize)
        self._surface = self._build_surface()
        self.move_at(fp, anchor)

    def set_text (self, text):
        """
        Set object's text to the string *text*, then rebuild font and surface.
        """
        self._text = text
        self._build_font(self._fname, self._fsize)
        self._surface = self._build_surface()

    def size_of (self, string):
        """Returns the size of string rendered using the object's font."""
        return self._font.size(string)


class Grid (object):
    def __init__ (self, rows, columns, size=(0,0)):
        """Make a Grid object.
        Provides some methods similar to other GameObject(s)
        for resizinig and moving.
        """
        self._table = Table(rows, columns)
        self._board = Board(size)
        self._shape = Shape(self._board.surfref)
        # default resize callback
        def rf (obj, cell, pos):
#            r, c = pos
            #obj.resize(*cell.size)
            obj.fit(cell)
#            cell.move_at((c*cell.w, r*cell.h), 'topleft')
#            obj.move_at(cell.center)
        self._resize_func = rf

    def __eq__ (self, other):
        return self._table ==  other

    def __ne__ (self, other):
        return not (self == other)

    def __str__ (self):
        return "Grid object (%d, %d) at %d" % (
            self._table.n_rows, self.table.n_cols, id(self))

    def __iter__ (self):
        return iter(self._table)

    def __getitem__(self, item):
        return self._table[item]

    def __setitem__ (self, item, value):
        self._table[item] = value

    @property
    def dims (self):
        """Returns the grid (rows, cols) dimensions."""
        return self._table.n_rows, self._table.n_cols

    @property
    def empty (self):
        return self._table.empty

    @property
    def rect (self):
        """Returns a copy of the grid's rect."""
        return self._shape.rect

    @property
    def resize_func (self):
        """Returns the resize function actually used in the arrange method.
        The default function fits the object into the cell.
        """ 
        return self._resize_func
    @resize_func.setter
    def resize_func (self, func):
        """Sets the resize function to beused in the arrange method.
        Arguments passed to this function are:
          - the object to the resized
          - a Shape object, as the grid's cell
          - the (row, col) position of the object in the grid
        """ 
        self._resize_func = func

    @property
    def size (self):
        """Returns the grid's size."""
        return self._board.size

    @property
    def surface (self):
        return self._board.surface

    @property
    def surfref (self):
        return self._board.surfref

    @property
    def isfull (self):
        return self._table.isfull
    def iter_pos (self):
        return self._table.iter_pos()
    def items (self):
        return self._table.items()
    def values (self):
        return self._table.values()

    def add (self, objects, overwrite=False):
        """Add objects to this grid starting from the first empty position.
        If overwrite is True, replace the objects in the current position
        with the new ones.
        Returns an empty list if all object were added correctly to the grid,
        otherwise returns a list with the excluded objects.

        objects => a sequence of object to put in the grid.
        overwrite => flag read as a bool value.
        """

        lst = list(reversed(objects))
        if self.isfull:
            return lst

        for p, v in self.items():
            if (v == self.empty) or overwrite:
                try:
                    self._table[p] = lst.pop()
                except IndexError:
                    break
        return list(reversed(lst))

    def arrange (self, update=True):
        """Arrange the grid's objects.

        update => bool value, if True (default) redraw the objects on the grid.
        """
        w, h = self.size
        cols, rows = self._table.n_cols, self._table.n_rows
        cell = Shape()
        cell.resize(w/cols, h/rows)
        left, top = self._shape.topleft
        for r,c in self._table.iter_pos():
            cell.move_at((c*cell.w+left, r*cell.h+top), 'topleft')
            obj = self._table[r,c]
            if obj != self.empty:
                obj.move_at(cell.center)
        if update:
            self.update()

    def move (self, x ,y, update=False):
        self._shape.move(x, y)
        self.arrange(update)

    def move_at (self, point, anchor=CENTER, update=False):
        self._shape.move_at(point, anchor)
        self.arrange(update)

    def positions (self, item):
        """Return a list of grid positions which olds *item*."""
        return list(self._table.get(item))

    def rebuild (self, resize_func=None, update=True):
        """Rebuild the object.
        resize_func => function for manage object's resizing, see
                       the doc of the resize_func property for the signature.
                       If None use the default (or previously set) function.
        update => bool value, if True (default) redraw the objects on the grid.
        """
        if resize_func is None:
            resize_func = self._resize_func
        w, h = self.size
        cols, rows = self._table.n_cols, self._table.n_rows
        cell = Shape()
        cell.resize(w/cols, h/rows)
        for r,c in self._table.iter_pos():
            obj = self._table[r,c]
            if obj != self.empty:
                resize_func(obj, cell, (r,c))
        self.arrange(update)

    def resize (self, w, h, update=True):
        """Resize the grid and its cells to the new (w,h) size.
        Update the Grid contents if update is a True value.
        """
        self._board = Board((w,h))
        self._shape.resize(w,h)
        self.rebuild(update=update)

    def shuffle (self, update=True):
        """Shuffle the grid's cells.
        Update the Grid contents if update is a True value (default).
        """
        rects = []
        for obj in self._table.values():
            if obj != self.empty:
                rects.append(obj.rect)
        self._table.shuffle()
        for obj in self._table.values():
            if obj != self.empty:
                obj.move_at(rects.pop().center)
        if update:
            self.update()

    def update (self):
        """
        Update the grid's board.
        """
        w, h = self.size
        rows, cols = self.dims
        cell = Shape()
        cell.resize(w/cols, h/rows)
        for (r,c), obj in self._table.items():
            if obj != self.empty:
                self._board.draw(obj, (c*cell.w, r*cell.h))


''' #XXX+TODO: ?
class DispatchObj (object):
    """A container for game objects, which dispatch messagges one at a time
    to the currently active object.
    """
    def __init__ (self, objects):
        self._objects = list(objects)
        self._idx = 0
        self._active = self._objects[0]
        self._to_all = []

    def _multicall (self, methods):
        def _inner (*a, **k):
            r = []
            for m in methods:
                r.append(m(*a, **k))
            return r
        return _inner

    def __getattr__ (self, attr):
        if attr in ('_objects', 'objects', '_active', 'active', '_idx', '_to_all'):
            return super(DispatchObj, self).__getattr__(attr)
        elif attr in self._to_all:
            return self._multicall([getattr(o, attr) for o in self._objects])
        return getattr(self._active, attr)

    def __setattr__ (self, attr, val):
        if attr in ('_objects', 'objects', '_active', 'active', '_idx', '_to_all'):
            return super(DispatchObj, self).__setattr__(attr, val)
        return setattr(self._active, attr, val)

    @property
    def active (self):
        """Returns the currently active object."""
        return self._active

    @property
    def objects (self):
        """Returns the hold objects."""
        return tuple(self._objects)
    @objects.setter
    def objects (self, objects):
        """Set a new  group of objects to hold.
        The active objects of this new group become the
        object at index of the previously active object.
        If out of range, set as active the first object
        in the group.
        See the set_active to change the active object directly.
        """
        self._objects = list(objects)
        self._idx -= 1
        self.next()

    def add (self, obj):
        """Add obj the the objects list."""
        self._objects.append(obj)

    def next (self):
        try:
            self.set_active(self._idx + 1)
        except ValueError:
            self.set_active(0)

    def set_active (self, index=None, obj=None):
        """Set the active object.
        index is the index of the object to activate in the object list.
        Instead of an index, an object can be passed as the obj param,
        which is the object to activate.
        If the index parameter is provided (as keyword or positional), the
        obj argument - if any - will be ignored.

        If the index is out of range or the object can't be found raise
        a ValueError exception.

        NOTE+XXX+TODO: default value of obj is None, so a None objects
        can't be searched ad set by itself, instead the index argument
        must be used.
        """
        if index is not None:
            try:
                self._active = self._objects[index]
                self._idx = index
            except IndexError as err:
                raise ValueError(err)
        elif obj is not None:
            idx = self._objects.index(obj)
            self._active = self._objects[idx]
            self._idx = idx

    def set_send_to_all (self, method='', action='add'):
        """Sets which methods must be sent to all the object.
        
        method => method name. If empty or a false value, reset
        the blablabla, otherwise execute action.
        action => must be one of 'add', 'replace', 'delete'.
                  'add' (default) adds method to the list of send-to-all
                  methods, 'replace' add this method and throw the others,
                  'delete'... delete all the methods.                  
        """
        if not method:
            self._to_all = []
        elif action == 'add':
            self._to_all.append(method)
        elif action == 'replace':
            self._to_all = [method]
        elif action == 'delete':
            try:
                self._to_all.remove(method)
            except ValueError:
                pass

    def send_to_all (self, method_name, args=(), kwargs={}):
        """Send a message to all the stored objects.
        method_name is the object's method to call, with args and kwargs
        as parameter.
        """
        for obj in self._objects:
            getattr(obj, method_name)(*args, **kwargs)
'''
