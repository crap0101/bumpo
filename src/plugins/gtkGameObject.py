# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


# std imports
from StringIO import StringIO
import tempfile
# local imports
from bumpo.baseObjects import GameObject
from bumpo.const import WIDTH, HEIGHT, CENTER
from bumpo import gameUtils
# external imports
import pygame


MODULE_PLUGINS = ['GtkGameObject']


try:
    import gtk
    GTK_VERSION = 2
except ImportError:
    #from gi.repository import Gtk #as gtk
    from gi.repository import GdkPixbuf
    GTK_VERSION = 3

class ImgBuffer (object):
    """
    Helper class to be used as a callback for store data
    generated from some gtk.gdk.pixbuf* functions.
    """
    def __init__(self):
        self.data = []
    def __call__(self, data, **kw):
        self.data.append(data)
        return True
    def clear (self):
        """Clear the data cache."""
        self.data = []
    def get_data(self):
        """Returns the data read until now."""
        return ''.join(self.data)


def surface_from_file__gtk2 (filepath, size=None):
    """
    Return a pygame.Surface object from a svg file.
    *filepath* is the file to read from,
    Optional *w* and *h* are the image width and height
    for the new image (default None, use the informations
    taken from the file).
    """
    if size is None:
        pixbuf = gtk.gdk.pixbuf_new_from_file(filepath)
    else:
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filepath, *size)
    buff = ImgBuffer()
    pixbuf.save_to_callback(buff, 'png')
    stream = StringIO(buff.get_data())
    return pygame.image.load(stream, 'spam.png')

def surface_from_file__gtk3 (filepath, size=None):
    """
    Return a pygame.Surface object from a svg file.
    *filepath* is the file to read from,
    Optional *w* and *h* are the image width and height
    for the new image (default None, use the informations
    taken from the file).
    """
    if size is None:
        print "XXXXX"*3,filepath
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)
        print "YYYYYYYY"
        size = pixbuf.get_width(), pixbuf.get_height()
    else:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filepath, *size)
    with tempfile.NamedTemporaryFile(delete=False) as t:
        outf = t.name
    # XXX+NOTE: actually need this shit because
    # the other methods (save_to_callback, etc) doesn't works
    # or not exists at all.
    pixbuf.savev(outf, 'png', (), ())
    with open(outf) as _:
        return pygame.image.load(_, 'spam.png')


if GTK_VERSION == 2:
    surface_from_file__gtk = surface_from_file__gtk2
else:
    surface_from_file__gtk = surface_from_file__gtk3


class GtkGameObject (GameObject):
    """DOC: TODO
    copied resize_* and scale_* methods to be compatible with GenericGameObject
    (also the _reload_on_resize class attribute)
    """
    _reload_on_resize = True
    def __init__ (self, obj=None, cmp_value=None, reload=None):
        """
        TODO: doc
        """
        if isinstance(obj, basestring):
            self._filepath = obj
            obj = surface_from_file__gtk(obj)
        else:
            self._filepath = None
        super(GtkGameObject, self).__init__(obj, cmp_value)
        self.convert()
        self._orig_shape = self.shape
        if reload is not None:
            self._reload_on_resize = bool(reload)

    @property
    def reload_on_resize (self): 
        """
        Returns the boolean value used by other methods (resize, fit, etc.)
        for decide if reload the object's source image before doing their job.
        """
        return self._reload_on_resize
    @reload_on_resize.setter
    def reload_on_resize (self, value):
        """
        If set to a true value, resizing, fitting or any other operation
        which cause changing the object's dimensions will be performed
        possibly reloading the original shape image (Shape, GameObject
        or whatever) if information loss can happen.
        """
        if value and self._filepath:
            size = self.size
            m = max(size)
            self._shape = self._shape.__class__(
                surface_from_file__gtk(self._filepath, (m,m)))
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
                    m = max(obj.w, obj.h)
                    self._shape = self._shape.__class__(
                        surface_from_file__gtk(self._filepath, (m,m)))
                    self.convert()
                else:
                    self._shape = self._orig_shape.copy()
        super(GtkGameObject, self).fit(obj)

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
                    m = max(width, height)
                    self._shape = self._shape.__class__(
                        surface_from_file__gtk(self._filepath, (m,m)))
                    self.convert()
                else:
                    self._shape = self._orig_shape.copy()
        super(GtkGameObject, self).resize(width, height)
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

