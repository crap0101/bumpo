#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.

"""
This module contains the basic stuffs needed to build and use
various type of game objects.

"""

import gameutils

import pygame
import random
import collections
# for python < 2.7, create an alias for OrderedDict, a fake object
# which only have the 'item' method used by the Cell class.
if not hasattr(collections, 'OrderedDict'):
    class FakeOD(object):
        def __init__(self, attrs=None):
            if not attrs:
                self._items = {}
            else:
                try:
                    self._items = tuple((k, v) for k, v in attrs.items())
                except AttributeError:
                    self._items = tuple((k, v) for k, v in attrs)
        def items(self):
            return self._items
    collections.OrderedDict = FakeOD



class GenericGameObject (object):
    """
    A generic game object. Provide methods for drawing,
    moving, resizing, comparing game objects, etc.
    """
    def __init__ (self, surface=None, cmp_value=None):
        """
        Set *surface* as its own surface or create a new zero-sized surface;
        also set the *rect* attribute as the surface's rect.
        *cmp_value* is the value used to compare GenericGameObjects,
        e.g. obj1 == obj2 (if not provided fall to id(self)).
        """
        self._from_svg = False
        self._filepath = None
        self._drawed_surface = None # for *draw_on* and *erase* methods
        self.surface = surface if surface else pygame.Surface((0,0))
        self._original_surface = self.surface.copy()
        self.rect = self.surface.get_rect()
        self._surround_rect = gameutils.copy_rect(self.rect)
        self._surround_rect_delta = None
        self._surround_rect_perc = None
        self._cmp_value = cmp_value if cmp_value is not None else id(self)
        self.actions = collections.defaultdict(list)
        self.velocity = [5, 7]

    @property
    def from_svg (self):
        """True if the object has been created from a svg image."""
        return self._from_svg

    @property
    def area (self):
        """The object's rect area"""
        return self.rect.width * self.rect.height

    @property
    def size (self):
        """The object's rect size."""
        return self.rect.size
    @size.setter
    def size (self, size):
        """Resize the object at the given *size* (width, height)."""
        self.resize(*size)

    @property
    def compare_value (self):
        """The value used to compare this object."""
        return self._cmp_value
    @compare_value.setter
    def compare_value (self, cmp_value):
        """Set the value used to compare this object."""
        self._cmp_value = cmp_value

    def __eq__(self, other):
        return self._cmp_value == other

    def __ne__ (self, other):
        return self._cmp_value != other

    def clamp (self, rect):
        """
        Move the object's rect to be completely inside
        the *rect*. Return the new object's rect.
        """
        self.rect = self.rect.clamp(rect)
        return self.rect

    def draw_on (self, surface, background=None):
        """
        Draw the object on *surface*. If *background* is not None,
        it must be a surface intended to be drawed on *surface* _before_
        the object's surface (and at the same position).
        The portion of *surface* drawed will be saved for and repainted by
        the *erase* method if no other surface inteded to be drawed are
        passed to the latter method. Note that the portion of the original
        surface is saved _before_ blitting *background*.
        """
        self._drawed_surface = gameutils.get_portion(surface, self.rect)
        if background:
            surface.blit(background, self.rect, self.rect)
        return surface.blit(self.surface, self.rect)

    def erase (self, destination, surface=None, clip_area=None):
        """
        Erase the object's surface from *destination*, drawing *surface*
        in its rect's area. If no *surface* is passed, or not a True value,
        the surface generated from a previously call to the *draw_on* method
        is used instead, otherwise raise a TypeError. *clip_area* represents
        a smaller portion of the destination surface to draw.
        """
        surface = surface or self._drawed_surface
        if not surface:
            raise TypeError("Need a Surface to draw!")
        return destination.blit(surface, self.rect, clip_area)

    def fit (self, rect_or_surface):
        """Move and resize the object's rect to fit *rect_or_surface*.
        The aspect ratio of the original Rect is preserved, so the new
        rectangle may be smaller than the target in either width or height.
        """
        try:
            self.resize(*self.rect.fit(rect_or_surface.get_rect()).size)
        except AttributeError:
            self.resize(*self.rect.fit(rect_or_surface).size)

    def is_clicked (self, point=None):
        """Return True if  *point* is inside the object's rect.
        A point along the right or bottom edge is not considered to be
        inside the rectangle. If *point* is not provided use the point value
        got from pygame.mouse.get_pos().
        """
        return self.rect.collidepoint(point or pygame.mouse.get_pos())

    def move (self, x, y):
        """
        Move the object's rect by the given offset. *x* and *y* can be
        any integer value, positive or negative. Returns the moved rect.
        """
        self.rect = self.rect.move(x, y)
        return self.rect

    def move_at (self, position, anchor_at='center'):
        """
        Move the object's rect at *position*.
        *anchor_at* (default 'center') must be a string representing
        a valid rect attribute and is used to determine the new position.
        """
        setattr(self.rect, anchor_at, position)
        return self.rect

    def move_bouncing (self, bounce_rect, velocity=(None, None)):
        """
        Move the object's rect bouncing inside *bounce_rect*
        by *velocity* (a pair, default to self.velocity).
        """
        x, y = velocity if (None not in velocity) else self.velocity
        new_velocity = [x, y]
        if (self.rect.left + x <= bounce_rect.left or
            self.rect.right + x >= bounce_rect.right):
            new_velocity[0] = -x
        if (self.rect.bottom + y >= bounce_rect.bottom or
            self.rect.top + y <= bounce_rect.top):
            new_velocity[1] = -y
        self.move(x, y)
        self.clamp(bounce_rect)
        self.velocity = new_velocity
        return self.rect

    def move_random (self, in_rect, x=(None,None), y=(None,None)):
        """
        Move the object's rect inside *in_rect* by a random value.
        The optional args *x* and *y* must be a pair of integer
        (positive or negative) and are used as a range in which choose
        the random value for moving each coordinate e.g. x=(min, max).
        If a pair element is None it's value belong to the *in_rec*
        dimension (for max) or zero (for min). This pairs are silently sorted,
        so x=(8, 19) or x=(19, 8) are the same. Raise TypeError for invalid
        value of *x* and *y* or if *in_rect* is not a valid object.
        Return the moved rect.
        """
        try:
            min_x, max_x = sorted(x)
            min_y, max_y = sorted(y)
            w, h = in_rect.size
            max_x = w if max_x is None else max_x
            max_y = h if max_y is None else max_y
            self.move(random.randint(min_x or 0, max_x),
                         random.randint(min_y or 0, max_y))
        except (TypeError, ValueError), err:
            raise TypeError("%s: 'x' and 'y' args must be tuples of two "
                             "integer items (or None, eg: (None, 100))" % err)
        except AttributeError, err:
            raise TypeError(str(err))
        self.clamp(in_rect)
        return self.rect

    def resize (self, width, height):
        """
        Resize the object at the new (width, height) dimension.
        *width* and *height* must be two positive integer,
        otherwise TypeError will be raised.
        """
        if any(d < 0 for d in (width, height)):
            raise TypeError("width and height must be two positive integer")
        try:
            self.surface = pygame.transform.smoothscale(self.surface, (width, height))
        except ValueError:
            self.surface = pygame.transform.scale(self.surface, (width, height))
        self.rect.size = self.surface.get_rect().size

    def resize_from_dim(self, length, dim):
        """
        Scale the object in relation to *length*, relative to the
        dimension *dim* (width or height). *dim* must be a string ('w' or 'h')
        representing the first dimention upon which the resize is
        performed. The other dimension will be scaled accordingly.
        """
        rect = gameutils.scale_rect_at_length(self.rect, length, dim)
        self.resize(*rect.size)
        
    def resize_from_rect (self, rect):
        """Resize at the size of *rect*."""
        self.resize(*rect.size)

    def resize_by_perc (self, perc):
        """Resize the object by *perc*, e.g with perc=50 resize 50%."""
        rect = gameutils.resize_rect_by_perc(self.rect, perc)
        self.resize(*rect.size)

    def resize_perc_from (self, surface_or_rect, perc, dim='h'):
        """
        Resize the object scaling in relation to the dimension *dim*
        (width or height) of *surface_or_rect* resized by *perc*.
        Optional *dim* must be a string ('w' or 'h'), default to 'h'.
        """
        try:
            rect = surface_or_rect.get_rect()
        except AttributeError:
            rect = surface_or_rect
        perc_rect = gameutils.resize_rect_by_perc(rect, perc)
        length = getattr(perc_rect, dim)
        scaled_rect = gameutils.scale_rect_at_length(self.rect, length, dim)
        self.resize(*scaled_rect.size)

    def rotate (self, angle, anchor_at='center'):
        """
        Rotate the object's surface by *angle* amount. Could be a float value.
        Negative angle amounts will rotate clockwise. *anchor_at* is the rect
        attribute used for anchor the rotated rect (default to 'center').
        Use the attr self._original_surface for rotation to avoid the surface
        enlargement and (when many calls to rotate occurs) the consequently
        segfault or raising of pygame error.
        Any blit performed on the object surface will be lost (to avoid
        this use the method set_surface() without args).
        """
        self.surface = self._original_surface
        anchor_point = getattr(self.rect, anchor_at)
        self.surface = pygame.transform.rotate(self.surface, angle)
        #self.surface = pygame.transform.rotozoom(self.surface, angle, 1)
        self.rect = self.surface.get_rect()
        setattr(self.rect, anchor_at, anchor_point)

    def raise_actions (self, group='default'):
        """
        Execute the action(s) previously set.
        Optional *group* is a string, the name of the group which
        the action(s) to execute belongs (default to 'default' group).
        """
        for action in self.actions[group]:
            callable_, args, kwords = action
            callable_(*args, **kwords)

    def set_action (self, callable_, args=None, kwords=None, group='default'):
        """
        Set a new action.
        *callable_* is a callable object which will be executed by the
        raise_actions() method, the optional *args* must be a collection
        or args to pass to 'callable_' and the optional argument *kwords*
        a dict representing the callable's keywords arguments.
        *group* is the group which this action belongs to, if not provided
        this action fall in the 'default' group.
        """
        self.actions[group].append((callable_, args or [], kwords or {}))

    def del_action_group (self, group):
        """
        Delete the action(s) of the group *group* and return it.
        Return None if *group* is not present.
        """
        return self.actions.pop(group, None)

    def set_rect_attrs (self, dict_or_seq):
        """
        Set the object's rect attributes from *dict_or_seq*.
        *dict_or_seq* can be either a  mapping object (in this case it
        must provide an items() method) or any iterable of (key, value) pairs.
        """
        try:
            items = dict_or_seq.items()
        except AttributeError:
            items = dict_or_seq
        for attr, value in items:
            setattr(self.rect, attr, value)

    def set_surface (self, surface=None):
        """
        Set the object's surface with *surface*. If *surface* is not provided,
        use the actual surface (can be useful, for example, after a blit on
        the object surface to register these changes, updating the
        self._original_surface attribute.
        """
        if surface:
            self.surface = surface.copy()
            self.rect.size = self.surface.get_rect().size
        self._original_surface = self.surface.copy()

    @property
    def surround_rect (self):
        """
        surround_rect is a rect which can help in some situations,
        e.g. distributing many non-overlapping objects on a surface or
        placing the object with a certain amount of space from other objects.
        It's centered at the object's rect center and follows its movements
        and resizements. By default coincide with the object's rect.
        """
        if self._surround_rect_delta is not None:
            rect = gameutils.copy_rect(self.rect)
            rect.w += self._surround_rect_delta
            rect.h += self._surround_rect_delta
            rect.center = self.rect.center
            return rect
        elif self._surround_rect_perc is not None:
            return gameutils.resize_rect_by_perc(
                gameutils.copy_rect(self.rect), self._surround_rect_perc)
        else:
            self._surround_rect.center = self.rect.center
            return self._surround_rect

    @surround_rect.setter
    def surround_rect (self, rect):
        if not isinstance(rect, pygame.Rect):
            raise typeError("surround_rect must be a Rect object")
        self._surround_rect_delta = None
        self._surround_rect_perc = None
        self._surround_rect = gameutils.copy_rect(rect)

    def set_surround_rect (self, length=None, perc=None, rect=None):
        """
        Set the surround_rect of the object's rect.
        This is a dummy method which set some attribute used to update
        the surround when the object's rect change.
        The arguments are optional, but only one at a time must be present,
        raise TypeError otherwise.
        *length* must be an integer, the surround_rect will be created
        adding this value to the object's rect dimensions.
        *rect* must be a valid rect object, the new surround_rect.
        *perc* create a surround_rect scaling by this value the object's rect.
        """
        nargs = sum(1 for x in (length, perc, rect) if x is not None)
        if nargs == 0:
            return
        elif nargs > 1:
           raise TypeError("set_surround_rect takes only two arguments"
                           " (self, [length | perc | rect])")
        if rect:
            self.surround_rect = rect
        elif length is not None:
            self._surround_rect_delta = length
            self._surround_rect_perc = None
        elif perc is not None:
            self._surround_rect_perc = perc
            self._surround_rect_delta = None


# IMAGE CLASSES

class Image (GenericGameObject):
    def __init__ (self, image_path, cmp_value=None):
        """
        Create a game object using the image file *image_path* as its surface.
        As an alternative *image_path* can be a pygame.Surface object, which
        is copied and become the object's surface.
        DANGER: using Scalable Vector Graphics (*.svg) format as *image_path*
        any resizing operation cause reloading the content from the
        original file; so any change to the object's surface (blit,
        subsurface, Cell's items were lost. Do resizing, fitting and
        similar operations *before* any surface modification or create
        another game object from the object's surface. To know if an object
        were build from a svg, check the *from_svg* attribute.
        """
        _from_svg = False
        if isinstance(image_path, pygame.Surface):
            surface = image_path.copy()
            image_path = None
        elif gameutils.is_svg(image_path):
            surface = gameutils.surface_from_svg(image_path)
            _from_svg = True
        else:
            surface = gameutils.surface_from_file(image_path)
        super(Image, self).__init__(surface, cmp_value)
        self._from_svg = _from_svg
        self._filepath = image_path

    def resize (self, width, height):
        """Resize the object at the new (width, height) dimension."""
        if self.from_svg:
            self.surface = gameutils.surface_from_svg(self._filepath, width, height)
        super(Image, self).resize(width, height)


class TextImage (GenericGameObject):
    """Create game object for display text."""
    def __init__ (self, text, font_name, font_size,
                  text_color, bg_color=None, cmp_value=None):
        """
        Create a TextImage object: *text* is the text to be displayed;
        *font_name* can be either a filename or a font name, in the latter
        case the font must be present in the system, otherwise a random
        available font is used instead; *font_size* is the initial size of
        the font, may change when the object size change.
        *text_color* is the color used for blit the text, *bg_color* is the
        background color (default to None, means transparent).
        """
        self.font_name = font_name
        self.font_size = font_size
        self.text = str(text)
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = None
        self._build_font(font_name, font_size)
        super(TextImage, self).__init__(self._build_surface(), cmp_value)

    def _build_surface (self):
        """Build the object's surface."""
        # XXX: pygame BUG
        # Cfr. http://pygame.motherhamster.org/bugzilla/show_bug.cgi?id=49
        # fixed: http://hg.pygame.org/pygame/changeset/6cc8196e0181
        if self.bg_color is None:
            return self.font.render(self.text, True, self.text_color)
        return self.font.render(self.text, True, self.text_color, self.bg_color)
        
    def _build_font (self, name, size):
        """
        Build the font. Private method used in resizing and object
        instantiation; see the docstring of the __init__ method.
        """
        self.font_name = name
        self.font_size = size
        try:
            self.font = pygame.font.Font(self.font_name, self.font_size)
        except IOError:
            self.font = pygame.font.SysFont(self.font_name, self.font_size)
        except RuntimeError:
            self.font = pygame.font.SysFont(
                ','.join(pygame.font.get_fonts()), self.font_size)

    def resize (self, w, h):
        """
        Resize the object at the given width and height,
        rebuilding the font and the object's surface.
        """
        fw, fh = self.font.size(self.text)
        self.font_size = max((self.font_size * h / fh, self.font_size * w / fw))
        self._build_font(self.font_name, self.font_size)
        self.set_surface(self._build_surface())
        super(TextImage, self).resize(w, h)


# CELL AND GRID CLASSES

class Cell (Image):
    """
    A Cell Class. used to create object that may contains
    another game's object (only one at a time) to be used together.
    """
    def __init__ (self, image_path, item=None, cmp_value=None):
        self.item = item
        self._item_attrs = {'center':None}
        super(Cell, self).__init__(image_path, cmp_value)

    @property
    def uarea (self):
        """The area of the union of the object's area and its item."""
        return gameutils.rect_area(self.urect)

    @property
    def urect (self):
        """The union of the object's rect and its item's rect (if any)."""
        return self.rect.union(self.item.rect) if self.item else self.rect

    def add_item (self, item, attrs=None, draw=False):
        """
        Set the object's item. *item* Must be a GenericGameObjects or
        compatible object. *attrs* is a mapping or a sequence of
        (key, value) pairs of rect attrs by which *item* will be positioned,
        maybe in respect to the cell. Despite of its original type it is
        transformed in a collections.OrderedDict object.
        The attribute's value can be a number (or coordinate pair), a string,
        a callable which takes no arguments, or None.
        Using numbers or pairs (e.g. {'topleft':(2,3), 'width':33, ...} the
        *item* position is absolute.
        Using a string, e.g {'left':'top', ...} the key is used as the
        *item*'s rect attribute to set, and the value is used as the Cell's
        rect attribute's from which take the needed value.
        In the example above, the *item*'s rect 'left' attribute is set to
        the value of the Cell rect's attribute 'top'.
        Using {rect_attr:None, ...} the *item*'s rect attribute rect_attr
        is set to the value of the Cell's rect attribute rect_attr.
        Using a callable (such as a lambda) this object is called with no
        arguments and the return value is used as the attribute values.
        NOTE: moving the object when its item's attrs are relative position
        such as 'bottom' or 'left' and not fully qualified point in the plain
        can obviously cause the item's relative position to change.
        The return value must be a valid rect value for the corresponding
        attribute (i.e. despite None can be used in *attrs* as described
        above, a callable _must_ return a right value).
        If *attrs* is not given, *item* will be centered at the
        Cell's rect center.
        If *draw* is a true value, *item* will be draw immediately on the
        Cell's surface (default to False).
        This object can contain only one item at a time. Multiple calls of
        add_item cause the overwrite of the previously set item (if any).
        """
        self.item = item
        self.set_item_attrs(attrs or {'center':None})
        self.update_item()
        if draw:
            self.item.draw_on(self.surface)

    def draw_on(self, surface, background=None, draw_item=False):
        """
        Draw the object on *surface*. Same as the GenericGameObject's
        draw_on method, but also permit to blit the object's item if
        *draw_item* is set to a true value.
        Returns the object's recs.
        """
        rect = super(Cell, self).draw_on(surface, background)
        if draw_item:
            self.item.draw_on(self.surface)
        return rect

    def move (self, x, y):
        super(Cell, self).move(x, y)
        self.update_item()
        return self.rect

    def move_at (self, position, anchor_at='center'):
        super(Cell, self).move_at(position, anchor_at)
        self.update_item()
        return self.rect

    def move_bouncing (self, bounce_rect, velocity=(None, None), union=False):
        """
        Move the object inside *bounce_rect* by *velocity* (a tuple,
        default to self.velocity).
        if *union* is a true value (default to False), bounce using
        use the object's urect. Any way, the object's item position is
        updated after the bounce.
        """
        if union:
            orig_rect = gameutils.copy_rect(self.rect)
            u_topleft = self.urect.topleft
            self.rect = self.urect
        super(Cell, self).move_bouncing(bounce_rect, velocity)
        if union:
            new_topleft = gameutils.move_relative_to(
                orig_rect.topleft, u_topleft, self.rect.topleft)
            self.rect = gameutils.copy_rect(orig_rect)
            self.rect.topleft = new_topleft
            #self.rect.clamp_ip(bounce_rect)
        self.update_item()
        return self.rect

    def resize (self, w, h):
        super(Cell, self).resize(w, h)
        self.update_item()

    def set_item_attrs(self, attrs, update=True):
        """
        Set the item's attr from *attrs*.
        If *update* is True, update immediately the item.
        """
        self._item_attrs = collections.OrderedDict(attrs)
        if update:
            self.update_item()

    def update_item(self):
        """
        Update the object's item (if any) following the
        changes in the object.
        """
        if self.item:
            for attr, value in self._item_attrs.items():
                if value is None:
                    setattr(self.item.rect, attr, getattr(self.rect, attr))
                elif callable(value):
                    setattr(self.item.rect, attr, value())
                elif isinstance(value, str):
                    setattr(self.item.rect, attr, getattr(self.rect, value))
                else:
                    setattr(self.item.rect, attr, value)


class Grid(GenericGameObject):
    def __init__ (self, fill_with=None, fill_dict_args=None):
        """
        *fill_with* is the object which will be used for all of the Grid's cell
        *fill_dict_arg* are the arguments used for instantiante the latter.
        Example:
        >>> g = gameObjects.Grid(gameObjects.Image, [pygame.Surface((0,0)), 2])
        >>> g
        <ImparaParole.baseObjects.gameObjects.Grid object at 0x150c690>
        """
        super(Grid, self).__init__()
        self._row = 0
        self._col = 0
        self._grid = {}
        self.fill_object = fill_with
        self.fill_object_args = fill_dict_args or dict()

    def __contains__ (self, item):
        return item in self._grid.values()

    def __getitem__(self, item):
        return self._grid[item]

    def __setitem__ (self, item, value):
        self._grid[item] = value

    def __iter__(self):
        return iter(self._grid[pos] for pos in self.iter_pos())

    def __len__ (self):
        return len(self._grid)

    def __str__ (self):
        fill = self.fill_object.__class__.__name__ if self.fill_object else '?'
        return "Grid object (%s, %d, %d)" % (fill, self._row, self._col)

    @property
    def columns (self):
        """The columns of the grid, as a list of lists."""
        cols = []
        for col in range(self._col):
            cols.append(list(self[row, col] for row in range(self._row)))
        return cols

    @property
    def rows (self):
        """The rows of the grid, as a list of lists."""
        rows = []
        for row in range(self._row):
            rows.append(list(self[row, col] for col in range(self._col)))
        return rows

    def build (self, rows, columns, cell_size):
        """Build a *rows* X *columns* grid, with cells of size *cell_size*."""
        self._grid = {}
        self._row = rows
        self._col = columns
        if not self.fill_object:
            for pos in self.iter_pos():
                self[pos] = None
            return
        _topleft = self.rect.topleft
        for pos in self.iter_pos():
            obj = self.fill_object(**self.fill_object_args)
            obj.resize(*cell_size)
            self[pos] = obj
        self.update()

    def draw_on (self, surface, background=None):
        """
        Draw the grid on *surface*, and return a sequence of its
        cells rects (to be used, for example, with pygame.display.update).
        """
        return list(cell.draw_on(surface) for cell in self)

    def iter_pos(self):
        """Yields the coordinates (row, column) of each cell in the table."""
        for row in range(self._row):
            for col in range(self._col):
                yield row, col

    def items (self):
        """Yields pairs of ((row, col), value) for each cell in the table."""
        for pos in self.iter_pos():
            yield pos, self[pos]

    def values (self):
        """Yields the value of each cell in the table."""
        for _, value in self.items():
            yield value

    def move (self, x, y):
        """Move the grid by (*x*, *y*)."""
        super(Grid, self).move(x, y)
        self.update()
        return self.rect

    def move_at (self, position, anchor_at='center'):
        """
        Move the object's rect at *position*.
        *anchor_at* (default to 'center') must be a string representing
        a valid rect attribute and is used to determine the new position.
        All the grid's objects are moved consequently.
        Returns the grid's rect.
        """
        super(Grid, self).move_at(position, anchor_at)
        self.update()
        return self.rect
                
    def resize (self, w, h):
        """Resize the grid and its cells to the new (*w*, *h*) size."""
        self.rect.size = (w, h)
        cell_size = (w / self._col, h / self._row)
        for cell in self:
            cell.resize(*cell_size)
        self.update()

    def shuffle (self):
        """Shuffle the grid's cells."""
        cells = list(x for x in self)
        random.shuffle(cells)
        for pos in self.iter_pos():
            self[pos] = cells.pop()
        assert not cells
        self.update()

    def update (self):
        """
        Update the grid's objects position.
        """
        _topleft = self.rect.topleft
        for row in self.rows:
            for cell in row:
                cell.rect.topleft = _topleft
                _topleft = cell.rect.topright
                self.rect.union_ip(cell.rect)
            _topleft = row[0].rect.bottomleft


class MemoryGrid (Grid):
    """Specific Grid class for Memory game."""
    def __init__ (self, nrows, ncolumns, cell_size):
        super(MemoryGrid, self).__init__()
        self.build(nrows, ncolumns, cell_size)
        self.cover = None

    def draw_on_covered (self, surface, cells=None):
        """
        Draw the grid's cover surface on *surface*.
        If *¢ells* is provided, must be a container filled with games objects
        or compatible ones; in this case blit them on *surface* instead of the
        grid's cells. Returns a list of the blitted rects.
        """
        rects = []
        for cell in (cells or self):
            rects.append(surface.blit(self.cover.surface, cell.rect))
        return rects

    def set_cover (self, image_or_surface):
        """
        Set the grid's cells cover to *image_or_surface*, a path to the target
        image or a pygame.Surface object. If the grid is already filled with
        game objects, the cover will be resized at the size of the first cell.
        """
        self.cover = Image(image_or_surface)
        if self[0,0]:
            self.cover.resize(*self[0,0].rect.size)


class GridCell (Image):
    """
    Specialized Image class which create objects intended to be used
    as MemoryGrid's cell objects.
    """
    def __init__ (self, image_path=None, cmp_value=None):
        super(GridCell, self).__init__(image_path, cmp_value)
        self._covered = True

    @property
    def covered (self):
        """True if the cell is covered (default)"""
        return self._covered

    def toggle (self):
        """Toggle the cell's covered state."""
        self._covered ^= True


class MovingTextButton(TextImage):
    """
    TextImage derived Class with some methods for simplify object's movements.
    """
    def __init__(self, *args, **kword):
        super(MovingTextButton, self).__init__(*args, **kword)
        self.start_attr = 'center'
        self.start_position = self.rect.center

    def goto_start(self):
        """
        Set the object's rect center at the value of its
        *start_position* attribute.
        """
        setattr(self.rect, self.start_attr, self.start_position)

    def update_start_position (self, rect_attr='center'):
        """
        Set the object's *start_position* attribute to the
        object's rect attribute *rect_attr* (default to 'center').
        """
        self.start_attr = rect_attr
        self.start_position = getattr(self.rect, rect_attr)

