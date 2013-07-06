# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


"""This module contains some functions and classes utilities related to the games."""


# std imports
import math
import random
import operator
import itertools as it
# local imports
from const import HEIGHT, WIDTH, ALPHA_CONV, NORMAL_CONV
# external imports
import pygame


#############
# FUNCTIONS #
#############

def check_collisions(objs, r):
    for i, o1 in enumerate(objs):
        for o2 in objs[i+1:]:
            if o1.rect.colliderect(o2):
                o1.move_bouncing(r)


def convert (surface, obj=None, alpha=True):
    """
    Change the surface pixel format in conformity with the obj argument.
    If no arguments are passed the new pixel format is the same as the
    pygame's display Surface. obj can be either a Shape or GameObject
    object.
    If alpha is a boolean true value (default: True), the shape will be in
    a format suited for quick blitting to the given format with per pixel
    alpha. Unlike converting without aplha, the pixel format for the new
    Shape will not be exactly the same as the requested source, but it
    will be optimized for fast alpha blitting.
    If obj is given and alpha is not True, the surface transparency value
    will be get from obj.
    If no surface is given, the new surface will be optimized for blitting
    to the current display. 
    """
    conv = getattr(surface, ('convert', 'convert_alpha')[alpha])
    surf = conv(obj) if obj is not None else conv()
    if obj is not None and not alpha:
        surf.set_alpha(obj.get_alpha())
    return surf

def edistance (seq1, seq2):
    """Returns the Euclidean distance between *seq1* and *seq2*."""
    return sum((c1-c2)**2 for c1,c2 in zip(seq1, seq2))**.5

def pygame_display_size ():
    """Return (w,h) size, the width and height of the current video mode,
    or of the desktop mode if called before the display.set_mode is called.
    Raise pygame.error if the video sistem is not intialized.
    """
    vi = pygame.display.Info()
    return vi.current_w, vi.current_h


def finddiv (n):
    """
    Returns a pair of (rows, cols) for an hypothetical
    grid which can contains at least `n` object.
    n should be >= 0, if not, returns the pair (1,1).
    """
    if n <= 0:
        return 1,1
    c = int(math.ceil(n**.5))
    d, m = divmod(n,c)
    return c, d+(1 if m else 0)


def relative_point (p1, p2, size):
    w1, h1 = p1
    w2, h2 = p2
    w, h = size
    return w1 * w / w2, h1 * h / h2


def surface_from_file (filepath, convert='alpha'):
    """
    Return a pygame.Surface object from the image file *filepath*.
    convert must be 'alpha' (the default), 'normal' or - to
    avoid conversion - a boolean false value.
    Raise ValueError with unknown convertion values.
    Raise pygame.error for unsupported image formats.
    """
    surf = pygame.image.load(filepath.encode('utf-8'))
    if convert:
        if convert == 'normal':
            conv = getattr(surf, 'convert')
        elif convert == 'alpha':
            conv = getattr(surf, 'convert_alpha')
        else:
            raise ValueError("unknown conversion type <%s>" % str(convert))
    else:
        conv = lambda i:i
    return conv(surf)


def surface_resize (surface, width, height):
    """
    Returns a new surface resized at *width* and *height*.
    *width* and *height* must be >= 0, otherwise raise TypeError.
    """
    if width < 0 or height < 0:
        raise ValueError("(%d, %d), width and height must be two positive integer" % (width, height))
    try:
        return pygame.transform.smoothscale(surface, (width, height))
    except ValueError:
        return pygame.transform.scale(surface, (width, height))


def scale_perc (w, h, perc):
    """Scale (w,h) size by perc, e.g with perc=50, scale at 50%.
    Raise ValueError if any of the arguments is < 0.
    """
    if w < 0 or h < 0 or perc < 0:
        raise ValueError("width, height and perc must be >= 0")
    return w*perc/100, h*perc/100


def scale_perc_from (w, h, perc, dim=HEIGHT):
    """Scale (w,h) size at the perc size of dimension *dim*.
    Raise ValueError for invalid *dim* arg (default HEIGHT)."""
    if dim == HEIGHT:
        length = h*perc/100
    elif dim == WIDTH:
        length = w*perc/100
    else:
        raise ValueError("Unknown dim '%s'" % dim)
    return scale_from_dim(w, h, length, dim)


def scale_from_dim (w, h, length, dim=HEIGHT):
    """Returns the new (w,h) size scaling by the dim-relative length.
    Raise ValueError for invalid *dim* arg (default HEIGHT)."""
    if dim == HEIGHT:
        return w*length/h, length
    elif dim == WIDTH:
        return length, h*length/w
    else:
        raise ValueError("Unknown dim '%s'" % dim)


###########
# CLASSES #
###########

class FakeSound (object): #XXX+TODO: maybe useless. Wraps Channels and Sound object in another one?
    """A class for creating sound object that (partially) mimic the
    behaviour of pygame.mixer.Sound object (but using pygame.mixer.music).
    """
    def __init__ (self, path_or_fileobj, channel=None):
        self.target = path_or_fileobj
        self.channel = channel

    def get_length (self):
        """Return the length of the FakeSound (in seconds)."""
        return pygame.mixer.Sound(self.target).get_length()

    def play (self, channel=0):
        """Begin sound playback, returns a Channel object."""
        pygame.mixer.music.load(self.target)
        pygame.mixer.music.play()
        self.channel = pygame.mixer.Channel(channel)
        return self.channel
    
    def stop (self):
        """Stop sound playback, returns None."""
        pygame.mixer.music.stop()
        if self.channel:
            self.channel.stop()
            self.channel = None


class EmptyObject (object):
    """Table default empty object."""
    def __eq__ (self, other):
        return self.__class__.__name__ == other
    def __ne__ (self, other):
        return not (self == other)
    def __str__ (self):
        return ''

class Table (object):
    def __init__ (self, rows, columns, empty=EmptyObject(), seq=()):
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
        if self.size != other.size:
            return False
        try:
            for pos, value in self.items():
                if other[pos] != value:
                    return False
        except KeyError:
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
        return self.empty not in self

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

    @property
    def size (self):
        """Returns the table size as a (rows, columns) pair."""
        return self._row, self._col

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
        """Yields the table's positions which holds *symbol*."""
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
        """Returns a rotated _copy_ of the table."""
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
        new = Table(self._col, self._row, empty=self.empty)
        for pos, val in zip(new.iter_pos(), it.chain(*self.columns)):
            new[pos] = val
        return new

    def values (self):
        """Yields the value of each cell in the table."""
        for pos in self.iter_pos():
            yield self[pos]
