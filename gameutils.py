# -*- coding: utf-8 -*-
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


"""This module contains some function/class utilities related to the games."""


import pygame
import logging
import math
import random
import operator
import itertools as it
from StringIO import StringIO

try:
    import gtk
    from gtk import gdk
    HAVE_GTK = True
except ImportError, err:
    logging.warning('missing gtk module: %s' % str(err))
    HAVE_GTK = False
    import mimetypes
    mimetypes.init()


class FakeSound (object):
    """
    A class for creating sound object that (partially) mimic
    the behaviour of pygame.mixer.Sound object.
    """
    def __init__ (self, path_or_fileobj, channel=None):
        self.target = path_or_fileobj
        self.channel = channel
    def get_length (self):
        """Return the length of the FakeSound (in seconds)."""
        return pygame.mixer.Sound(self.target).get_length()
    def play (self, channel=0):
        """Begin sound playback, return a Channel object."""
        pygame.mixer.music.load(self.target)
        pygame.mixer.music.play()
        self.channel = pygame.mixer.Channel(channel)
        return self.channel
    def stop (self):
        """Stop sound playback, return None."""
        pygame.mixer.music.stop()
        if self.channel:
            self.channel.stop()
            self.channel = None


def finddiv (n):
    if n < 1:
        return 0,0
    for x in range(1, n):
        for y in range(1, n):
            if y > x:
                break
            if x*y >= n:
                return x,y
    return n,1


# EVENTS

def dont_block (event_to_push=None):
    """
    Convenience function to avoid app's freeze-like behaviour when
    the event queue is empty and pygame.event.get is used in the program's
    main loop. Call this function assure the presence of an event to be
    processed; it work checking the event queue and, if empty, push in
    *event_to_push* (or pygame.USEREVENT if None).
    """
    if event_to_push is None:
        event_to_push = pygame.USEREVENT
    event = pygame.event.poll()
    if event.type == pygame.NOEVENT:
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))
    else:
        pygame.event.post(event)



# GENERAL

def get_attrs_from (attrs, object, raise_error=True):
    """
    Return a new dict build with (key, value) pairs of the attributes
    *attrs* of *object*.
    *attrs* can be any objects that support iteration (tuple, list, dict).
    If *raise_error* is a true value (the default), raise an AttributeError
    if *object* has not any of the attributes in *attrs*; otherwise, ignore
    that attribute.
    """
    object_attrs = {}
    for attr in attrs:
        try:
            object_attrs[attr] = getattr(object, attr)
        except AttributeError:
            if raise_error:
                raise
    return object_attrs


# RECTS

def copy_rect (rect):
    """
    Return a new pygame.Rect object, a copy of *rect*.
    This is a workaround to mimic the copy method, for Pygame < 1.9.0.
    """
    return pygame.Rect(rect)


def rect_area (rect):
    """Return the area of *rect*."""
    return rect.width * rect.height


def scale_rect (rect, factor):
    """Return a new rect scaled by *factor* in relation to *rect*."""
    return pygame.Rect(0, 0, rect.w*factor, rect.h*factor) 


def scale_rect_at_length (rect, length, dim):
    """
    Return a new rect scaled in relation to *length*, relative to the
    dimension *dim* (width or height). *dim* must be a string ('w' or 'h')
    representing the first dimention upon which the resize is
    performed. The other dimension will be scaled accordingly.
    For example, with *rect* of size (10, 20), length=5 and dim='w',
    the new rect's size will be (5, 10).
    """
    fst, snd = rect.size if dim == 'w' else rect.size[::-1]
    _fst = length
    _snd = snd * _fst / fst
    return pygame.Rect((0, 0), (_fst, _snd) if dim == 'w' else (_snd, _fst))


def resize_rect_by_perc (rect, perc, anchor_at='center'):
    """
    Return a new rect resized by *perc*
    *anchor_at* (a string, must be a pygame.Rect attribute) sets
    the new's rect position from the given *rect* (default to 'center').
    """
    new_rect = pygame.Rect(rect.topleft, (rect.w*perc/100, rect.h*perc/100))
    setattr(new_rect, anchor_at, getattr(rect, anchor_at))
    return new_rect


def resize_rect_by_perc_ip (rect, perc, anchor_at='center'):
    """Like *resize_rect_by_perc* but operates in place."""
    new_rect = resize_rect_by_perc(rect, perc, anchor_at)
    rect.size = new_rect.size
    setattr(rect, anchor_at, getattr(new_rect, anchor_at))


def rects_collide_at (rects, index):
    """
    Returns a list of indices for any rect in *rect* which
    collide with the rect at *index* (apart the rect at *index*).
    """
    rects = rects[:]
    target_rect = rects.pop(index)
    return [i + (i >= index) for i in target_rect.collidelistall(rects)]


def distribute_rects (rects, in_rect, pad=0):
    """
    Distribute *rects* inside the rect *in_rect*,
    spacing them by *pad* (default 0).
    """
    w, h = in_rect.size
    lastRect = pygame.Rect(map(sum, zip(in_rect.topleft, (pad,pad))), (pad,pad))
    newRowStartPoint = (in_rect.left+pad, rects[0].h+pad)
    for pos, rect in enumerate(rects):
        if lastRect.right + rect.width + pad > w:
            if (newRowStartPoint[0] + rect.height + pad > h
                or newRowStartPoint[1] + rect.width + pad > w):
                return rects, pos
            rect.topleft = newRowStartPoint
            lastRect = rect
        elif lastRect.top + rect.height + pad > h:
            return rects, pos
        else:
            rect.topleft = map(sum, zip(lastRect.topright, (pad, 0)))
            lastRect = rect
        if rect.bottom > newRowStartPoint[1]:
            newRowStartPoint = (newRowStartPoint[0], rect.bottom + pad)
    return rects, pos+1


def cmp_rects_area (rect1, rect2):
    """
    Compare the area of the two rects *rect1* and *rect2*.
    Return value:
      -1  if rect1 < rect2,
       0  if the areas are equals
       1  if rect1 > rect2.
    """
    area1, area2 = map(rect_area, (rect1, rect2))
    return -1 if area1 < area2 else (0 if area1 == area2 else 1)


def cmp_rects_attr (rect1, rect2, attr):
    """
    Compare the *attr* attribute of *rect1* and *rect2*.
    Like the __cmp__ object's method returns
      -1  if rect1.attr < rect2.attr,
       0  if the rect's attr are equals
       1  if rect1.attr > rect2.attr.
    """
    attr1, attr2 = map(lambda r: getattr(r, attr), (rect1, rect2))
    return -1 if attr1 < attr2 else (0 if attr1 == attr2 else 1)


def cmp_rects_attrs (rect1, rect2, attrs, delta=0):
    """
    Compare all the attributes in *attrs* of *rect1* and *rect2*.
    *delta* (must be an integer >= 0, default to 0) is used to set the
    limit of acceptable number of differences between the rects.
    A *delta* value of 0 means that all attributes must compare equals.
    Like the __cmp__ object's method returns
      -1  if the first rect evaluate < than the second,
       0  if the first rect evaluate == as the second,
       1  if the first rect evaluate > than the second.
    """
    if delta < 0:
        raise ValueError("*delta* must be an integer >= 0")
    res = sum(cmp_rects_attr(rect1, rect2, attr) for attr in attrs)
    ares = abs(res)
    if res < 0:
        if ares > delta:
            return -1
        return 0
    elif res == 0:
        return 0
    elif ares < delta:
        return 0
    return 1


def move_relative_to(pos, rel, new):
    """
    Arguments are pairs of (x, y) coordinates.
    Returns a new pair of coordinates which is the new positon
    for *pos* referring *rel* as if *rel* is moved at *new*.
    """
    x, y = pos
    rx, ry = rel
    nx, ny = new
    xx, yy = abs(rx - x), abs(ry - y)
    _x = nx + xx if x > rx else nx - xx
    _y = ny + yy if y > ry else ny - yy
    return _x, _y


def position_relative_to (position, relative, other):
    """
    Arguments are pairs of (x, y) coordinates.
    *position* is the actual position,
    *relative* are the coordinates *position* make reference to
    *other* is the point in the plane in which referring *relative*.
    Return a pair of coordinates (x, y) as the new position.
    Example:
    >>> position_relative_to((22,22), (2,2), (4,4))
    (44, 44)
    """
    rw, rh = map(lambda d: d if d > 0 else 1, relative)
    pw, ph = position
    ow, oh = other
    w = pw * ow / rw
    h = ph * oh / rh
    return w, h


def rect_relative_to (rect, relative, other):
    """
    Similar to *position_relative_to* but operates on rects.
    *rect* is the actual rect
    *relative* is the rect *rect* make reference to
    *other* is a rect referring *relative_rect*, in which the
    new rect must be build.
    Return a new rect, resized and moved accordingly."""
    t, l = position_relative_to(rect.topleft, relative.size, other.size)
    b, r = position_relative_to(rect.bottomright, relative.size, other.size)
    return pygame.Rect(t, l, b-t, r-l)



# SURFACES & COLORS


def average_color (surface):
    """Return the average color of *surface*."""
    alpha = surface.get_at((0,0)).a
    r, g, b, _ = pygame.transform.average_color(surface)
    return pygame.Color(r, g, b, alpha)


def edistance (color1, color2):
    """Returns the Euclidean distance between *color1* and *color2*."""
    return math.sqrt(sum(
            map(lambda pair: math.pow(operator.sub(*pair), 2),
                zip(color1, color2))))


def get_portion (surface, rect):
    """
    Return, as a new surface, the portion of *surface*
    contained by *rect*.
    """
    portion = pygame.Surface((rect.w, rect.h))
    portion.blit(surface, (0,0), rect)
    return portion


def grayscale (surface):
    """Returns a new 'black & white' surface from *surface*."""
    surf = surface.copy()
    grayscale_ip(surf)
    return surf


def grayscale_ip (surface):
    """Transform *surface* to grayscale *in place*."""
    for w in range(surface.get_width()):
        for h in range(surface.get_height()):
            r, g, b, a = surface.get_at((w,h))
            y = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
            surface.set_at((w,h), (y, y, y, a))


def laplacian (surface):
    """Returns a new surface appling the laplacian algorithm to *surface*."""
    return pygame.transform.laplacian(surface)


def surface_area (surface):
    """Return the area of *surface*."""
    w, h = surface.get_size()
    return w * h


def surface_resize (surface, width, height):
    """
    Returns a new surface resized at *width* and *height*.
    *width* and *height* must be >= 0, otherwise raise TypeError.
    """
    if any(d < 0 for d in (width, height)):
        raise TypeError("width and height must be two positive integer")
    try:
        return pygame.transform.smoothscale(surface, (width, height))
    except ValueError:
        return pygame.transform.scale(surface, (width, height))



# OBJECTS UTILITY

def gobj_collide_at (objects, index, attr='rect'):
    """
    Check if the object at index *index* collide with any
    other object in the *objects* sequence. The optional argument
    *attr* is the object's attribute by which compare the object's
    collisions (must be a rect object, default to 'rect').
    Returns a list of all the indices of objects that collide
    with the target object. If no intersecting objects are found,
    an empty list is returned. 
    """
    return rects_collide_at(list(getattr(o, attr) for o in objects), index)


# Images handling

def is_svg (filepath):
    """Return True if *filepath* is a svg file, False otherwise."""
    if HAVE_GTK:
        ext = 'svg'
        return (filepath.lower().endswith(ext)
                or gtk.gdk.pixbuf_get_file_info(filepath)[0]['name'].lower() == ext)
    else:
        ext = '.svg'
        img_type, enc = mimetypes.guess_type(filepath)
        if img_type is None:
            return False
        return ext in map(str.lower, mimetypes.guess_all_extensions(img_type))


class ImgBuffer (object):
    """
    Help class for create objects used as callback which
    store data generated from some gtk.gdk.pixbuf* functions.
    """
    def __init__(self):
        self.data = []
    def __call__(self, data, **kw):
        self.data.append(data)
    def get_data(self):
        return ''.join(self.data)


def surface_from_svg (filepath, w=None, h=None):
    """
    Return a pygame.Surface object from a svg file.
    *filepath* is the file to read from,
    Optional *w* and *h* are the image width and height
    for the new image (default None, use the informations
    taken from the file).
    """
    _w, _h =  gtk.gdk.pixbuf_get_file_info(filepath)[1:]
    w = _w if w is None else w
    h = _h if h is None else h
    gpb = gdk.pixbuf_new_from_file_at_size(filepath, w, h)
    buff = ImgBuffer()
    gpb.save_to_callback(buff, 'png')
    im_mem = StringIO(buff.get_data())
    return pygame.image.load(im_mem, 'spam.png')


def surface_from_file (filepath):
    """
    Return a pygame.Surface object from the image file *filepath*.
    """
    return pygame.image.load(filepath.encode('utf-8')).convert_alpha()


# MISC


class Table (object):
    def __init__ (self, rows, columns, empty=None, seq=()):
        """
        Create a Table of *row* x *columns* size.
        *empty* is the value for the empty cells (default None).
        If *seq* is provided, must be a sequence; the table will be
        populated with it's items (missing positions are filled
        using *empty*).
        """
        super(Table, self).__init__()
        self._row = rows
        self._col = columns
        self._empty = empty
        self._grid = dict(
            it.takewhile(lambda args: args[0] != empty,
                         it.izip_longest(self.iter_pos(), seq, fillvalue=empty)))

    def __contains__ (self, item):
        return item in self._grid.values()

    def __eq__ (self, other):
        for pos, value in self.items():
            if other[pos] != value:
                return False
        return True

    def __ne__ (self, other):
        return not (self == other)

    def __getitem__(self, item):
        return self._grid[item]

    def __setitem__ (self, item, value):
        self._grid[item] = value

    def __iter__(self):
        return iter(self._grid[pos] for pos in self.iter_pos())

    def __len__ (self):
        return len(self._grid)

    def __str__ (self):
        return "Table object (%d, %d) at %s" % (self._row, self._col, hex(id(self)))

    @property
    def empty (self):
        """Table's 'empty' value."""
        return self._empty

    @property
    def isfull (self):
        """Return True if the table has been completely filled."""
        for value in self.values():
            if value == self.empty:
                return False
        return True

    @property
    def columns (self):
        """The table's columns, as a list of lists."""
        cols = []
        for col in range(self._col):
            cols.append(list(self[row, col] for row in range(self._row)))
        return cols

    @property
    def rows (self):
        """The table's rows, as a list of lists."""
        rows = []
        for row in range(self._row):
            rows.append(list(self[row, col] for col in range(self._col)))
        return rows

    @property
    def n_cols (self):
        """Number of table's columns."""
        return self._col

    @property
    def n_rows (self):
        """Number of table's rows."""
        return self._row

    def copy (self):
        """Returns a copy of the table."""
        new_table = Table(self._row, self._col, self.empty)
        for pos, value in self.items():
            new_table[pos] = value
        return new_table

    def diagonal (self, row=0, col=0, topright=False):
        """
        Returns a sequence of the table's values for the diagonal
        starting at *row* and *col*.
        *row* and *col* default to zero, i.e. returns the major diagonal.
        If *topright* is True, return the topright-to-bottomleft diagonal.
        Raise KeyError for *row* or *col* values out of index.
        """
        values = []
        endcol = (self._col, -1)[topright]
        stepcol = (1, -1)[topright]
        for pos in zip(range(row, self._row), range(col, endcol, stepcol)):
            values.append(self[pos])
        return values

    def free (self):
        """Yields the table's empty positions."""
        for pos, value in self.items():
            if value == self.empty:
                yield pos

    def get (self, symbol):
        """Yelds the table's positions which holds *symbol*."""
        for pos, item in self.items():
            if item == symbol:
                yield pos

    def items (self):
        """Yields pairs of ((row, col), value) for each cell in the table."""
        for pos in self.iter_pos():
            yield pos, self[pos]

    def iter_pos (self):
        """Yields the coordinates (row, column) of each cell in the table."""
        for row in range(self._row):
            for col in range(self._col):
                yield row, col

    def major_diagonal (self):
        """Returns the values on the table's major (or main) diagonal.""" 
        return self.diagonal()

    def minor_diagonal (self):
        """Returns the values on the table's minor diagonal.""" 
        values = []
        for pos in zip(range(self._row), range(self._col-1, -1, -1)):
            values.append(self[pos])
        return values

    def pprint (self, format=None):
        """Pretty print row-by-row using *format* or the default one."""
        format = format or "%s " * self._col
        for row in self.rows:
            print format % tuple(row)            

    def reflected_h (self):
        """Returns a (horizontal) reflected _copy_ of the table."""
        seq = it.chain(*list(x[::-1] for x in self.rows))
        return Table(self._row, self._col, empty=self.empty, seq=seq)

    def reflected_v (self):
        """Returns a (vertical) reflected _copy_ of the table."""
        seq = it.chain(*self.rows[::-1])
        return Table(self._row, self._col, empty=self.empty, seq=seq)

    def rotated (self):
        """Return a rotated _copy_ of the table."""
        seq = it.chain(*list(x[::-1] for x in zip(*self.rows)))
        return Table(self._col, self._row, empty=self.empty, seq=seq)

    def shuffle (self):
        cells = list(x for x in self)
        random.shuffle(cells)
        for pos in self.iter_pos():
            self[pos] = cells.pop()
        assert not cells

    def transposed (self):
        """Returns a transposed _copy_ of the table."""
        new = Table(self._col, self._row)
        for pos, val in zip(new.iter_pos(), it.chain(*self.columns)):
            new[pos] = val
        return new

    def values (self):
        """Yields the value of each cell in the table."""
        for _, value in self.items():
            yield value
