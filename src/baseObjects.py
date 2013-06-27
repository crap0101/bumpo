# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


# std imports
from abc import ABCMeta
from collections import defaultdict, namedtuple, Sequence, MutableSequence
from functools import reduce
import operator
import random
# local imports
import gameUtils
from const import SHAPE_RECT_ATTRS, GAMEOBJ_SHAPE_ATTR, CENTER, TOPLEFT
# external imports
import pygame


GO_SHAPE_ATTRS = frozenset(SHAPE_RECT_ATTRS + GAMEOBJ_SHAPE_ATTR)

Velocity = namedtuple('Velocity', 'x y')

"""
NOTE: custom shape and game objects *must* register themself respectively
within the abstract classes BaseShape and BaseGameObject, or inherit from
a registered class.
"""

class BaseShape:
    __metaclass__ = ABCMeta

class BaseGameObject:
    __metaclass__ = ABCMeta


class ShapeMeta (type):
    """
    Shape metaclass used for set some attributes and....TODO.
    """
    def __new__(mcs, name, bases, dict):
        def _get_attr (attr):
            def _ga (inst):
                return getattr(inst._rect, attr)
            return _ga
        def _set_attr (attr):
            def _sa (inst, val):
                setattr(inst._rect, attr, val)
            return _sa
        for attr in SHAPE_RECT_ATTRS:
            dict[attr] = property(_get_attr(attr), _set_attr(attr))
        return type.__new__(mcs, name, bases, dict)

class Shape (object):
    __metaclass__ = ShapeMeta
    def __init__ (self, obj=None):
        """
        Create a new Shape instance from obj.
        obj can be a pygame.Rect, a pygame.Surface, another shape
        or None (in the latter case a zero-sized shape is created).
        Raise TypeError for a non conforming object obj.
        """
        if obj is None:
            self._surface = pygame.Surface((0,0))
            self._rect = self._surface.get_rect()
        elif isinstance(obj, BaseShape):
            self._surface = obj.surface
            self._rect = obj.rect
            self.alpha = obj.alpha
        elif isinstance(obj, pygame.Surface):
            self._surface = obj.copy()
            self._rect = self._surface.get_rect()
            self.alpha = obj.get_alpha()
        elif isinstance(obj, pygame.Rect):
            self._rect = pygame.Rect(obj)
            self._surface = pygame.Surface(self._rect.size)
        else:
            raise TypeError("Can't initialize a Shape object from %s" % obj)
        #self.convert()

    @property
    def alpha (self):
        """
        Return the current alpha value for this Shape.
        If the alpha value is not set then None is returned.
        """
        return self._surface.get_alpha()
    @alpha.setter
    def alpha (self, a):
        """
        Set the current alpha value for this Shape.
        The alpha value must be an integer from 0 to 255,
        0 is fully transparent and 255 is fully opaque.
        If None is passed for the alpha value, then the alpha will be disabled.
        """
        self._surface.set_alpha(a)

    @property
    def area (self):
        """Returns the Shape's area."""
        return self.w * self.h

    def at (self, point):
        """
        Returns a copy of the RGBA Color value at the given (x,y) point.
        If the pixel position is outside the area of the Shape
        an IndexError exception will be raised.
        """
        return self._surface.get_at(point)

    def _at (self, point, color=None): # XXX+TODO: use this?
        """
        Returns a copy of the RGBA Color value at the given (x,y) point.
        If color is not None, set the RGBA or mapped integer color value for
        the given pixel. If the pixel position is outside the area of the Shape
        an IndexError exception will be raised.
        """
        if color is None:
            self._surface.set_at(point, color)
        return self._surface.get_at(point)

    @property
    def rect (self):
        """Returns a copy of the Shape's rect."""
        return pygame.Rect(self._rect)

    @property
    def surface (self):
        """Returns a copy of the Shape's surface."""
        surf = self._surface.copy()
        surf.set_alpha(self.alpha)
        return surf

    @property
    def surfref (self):
        """Returns a reference of the Shape's surface."""
        return self._surface

    def clamp (self, shape):
        """
        Moves this Shape to be completely inside the argument shape.
        If it is large to fit inside, it is centered inside the argument shape,
        but its size is not changed.
        """
        self._rect.clamp_ip(shape.rect)

    def contains (self, shape):
        """
        Return True if the argument shape is completely inside this Shape.
        """
        return bool(self._rect.contains(shape.rect))

    def collide (self, shape):
        """
        Returns True if any portion of either shape overlap
        (except the top+bottom or left+right edges). 
        """
        return bool(self._rect.colliderect(shape.rect))

    def collidepoint (self, point):
        """
        Returns true if the given point is inside this Shape.
        A point along the right or bottom edge is not considered to be inside. 
        """
        return bool(self._rect.collidepoint(point))

    def convert (self, obj=None, alpha=True):
        """See gameUtils.convert."""
        if obj is not None:
            if isinstance(obj, BaseShape):
                obj = obj.surfref
            elif not isinstance(obj, pygame.Surface):
                raise TypeError(
                    "'obj' must be BaseShape, BaseGameObject or pygame.Surface")
        self._surface = gameUtils.convert(self._surface, obj, alpha)

    def copy (self):
        """Returns a new shape from this Shape, copying its surface,
        rect and position.
        """
        s = self.__class__(self.surfref)
        s.alpha = self.alpha
        s.move_at(self._rect.topleft, TOPLEFT)
        return s

    def fit (self, shape):
        """
        Move and resize this Shape to fit the argument shape.
        The aspect ratio of the Shape is preserved, so the new size
        may be smaller than the target in either width or height.
        Raise TypeError for invalid objects.
        """
        if isinstance(shape, (BaseShape,BaseGameObject)):
            rect = shape.rect
        elif isinstance(shape, pygame.Rect):
            rect = shape
        else:
            raise TypeError("Unknown object type: %s" % type(shape))
        self._rect = self._rect.fit(rect)
        self._surface = gameUtils.surface_resize(self._surface, self.w, self.h)
        # XXX+TODO: ulteriori metodi? tipo:
        # blit, fill, subsurface (in ogni caso una copia), get_buffer (... decidere) 

    def move (self, x, y):
        """Move the Shape by the given offset."""
        self._rect.move_ip(x, y)

    def move_at (self, point, anchor=CENTER):
        """
        Move the Shape at the given (x,y) point which
        becomes the new coordinates of the anchor's Shape
        attribute (default CENTER).
        """
        setattr(self._rect, anchor, point)

    def resize (self, w, h):
        """
        Resizes this Shape to a new (w,h) resolution.
        w and h must be positive integer, otherwise raise ValueError.
        """
        self._surface = gameUtils.surface_resize(self._surface, w, h)
        self._rect.size = w,h

    def _rotate (self, angle, anchor_at='center'): #XXX+TODO
        raise NotImplementedError

# reg Shape
BaseShape.register(Shape)

class GameObject (object):
    def __init__ (self, obj=None, cmp_value=None):
        """
        Create a new GameObject instance, optionally from an existing
        object obj, which can be a pygame.Surface, a Shape compatible
        object or None (the default). Raise TypeError otherwise.
        cmp_value should be a special value which will be used in
        object's comparison, or None (the default: means id(self)).
        """
        if obj is None:
            self._shape = Shape()
        elif isinstance(obj, pygame.Surface):
            self._shape = Shape(obj)
        elif isinstance(obj, BaseShape):
            self._shape = obj.copy()
        else:
            raise TypeError("Can't create an instance from %s" % obj)
        self._cmp_value = id(self) if cmp_value is None else cmp_value
        self._velocity = Velocity(0,0)
        self._action_groups = defaultdict(list)

    @property
    def compare_value (self):
        """The value used to compare this object."""
        return self._cmp_value
    @compare_value.setter
    def compare_value (self, cmp_value):
        """Set the value used to compare this object."""
        self._cmp_value = cmp_value

    @property
    def shape (self):
        """Returns a copy of the object's shape."""
        return self._shape.copy()

    @property
    def velocity (self):
        return self._velocity
    @velocity.setter
    def velocity (self, xyv):
        self._velocity = Velocity(*xyv)

    def __eq__(self, other):
        return self._cmp_value == other

    def __ne__ (self, other):
        return not self == other

    def __getattr__ (self, attr):
        """Get some attributes from the object's shape."""
        if attr in GO_SHAPE_ATTRS:
            return getattr(self._shape, attr)
        else:
            raise AttributeError("%s object has no attribute %s"
                                 % (self.__class__.__name__, attr))

    def __setattr__ (self, attr, value):
        """Set some attributes to the object's shape."""
        if attr in GO_SHAPE_ATTRS:
            return setattr(self._shape, attr, value)
        else:
            return super(GameObject, self).__setattr__(attr, value)

    def _clamp (self, obj):
        """
        Clamp this object into obj (either Shape or GameObject
        compatible object) or raise TypeError.
        """
        if isinstance(obj, BaseShape):
            self._shape.clamp(obj)
        elif isinstance(obj, BaseGameObject):
            self._shape.clamp(obj.shape)
        else:
            raise TypeError("Unsupported object to clamp in: %s" % obj)

    def clamp (self, obj):
        """
        Clamp this object into obj (either Shape or GameObject
        compatible object) or raise TypeError.
        """
        self._clamp(obj)

    def convert (self, obj=None, alpha=True):
        """See gameUtils.convert."""
        if obj is not None:
            if isinstance(obj, (BaseShape, GameObject)):
                obj = obj.surfref
            elif not isinstance(obj, pygame.Surface):
                raise TypeError(
                    "'obj' must be BaseShape, BaseGameObject or pygame.Surface")
        self._shape.convert(obj, alpha)

    def copy (self): #XXX+TODO: allow copy?
        """Returns a copy of this object copying its shape and velocity."""
        new = self.__class__(self._shape, self._cmp_value)
        new.velocity = self.velocity
        return new

    def fit (self, obj):
        """
        Move and resize this object to fit obj, which can be either a Shape
        or a GameObject. The aspect ratio of the object is preserved, so the
        new size may be smaller than the target in either width or height.
        """
        if isinstance(obj, BaseGameObject):
            obj = obj.shape
        self._shape.fit(obj)

    def is_clicked (self, point=None):
        """
        Return True if the (x,y pair) point is inside the object's shape.
        A point along the right or bottom edge is not considered to be
        inside. Without argument use the result of pygame.mouse.get_pos().
        """
        return self.collidepoint(point or pygame.mouse.get_pos())

    def move_bouncing (self, obj, velocity=None):
        """
        Move the object bouncing inside *obj* (either a GameObject
        or Shape object) by velocity, a pair of integer values, or
        None (in the latter case, the object's own velocity is used).
        """
        x, y = velocity if velocity is not None else self.velocity
        vx, vy = x, y
        if (self.left + x <= obj.left or self.right + x >= obj.right):
            vx = -x
        if (self.bottom + y >= obj.bottom or self.top + y <= obj.top):
            vy = -y
        self.move(x, y)
        self._clamp(obj)
        self._velocity = Velocity(vx, vy)

    def move_random (self, obj=None, xbound=None, ybound=None):
        """
        Move the object in a new pseudo-random position.
        xbound and ybound are a pair of integer representing the
        range in which choose the random value for each coordinate movement,
        or None (in the latter case, the object's velocity attr will be used).
        obj is an optional object (GameObject or Shape like)
        used as bounding box, otherwise the object is free to move along
        the plane without limits (even negative ones).
        """
        if xbound is None:
            xbound = (0, self.velocity.x)
        if ybound is None:
            ybound = (0, self.velocity.y)
        self.move(random.randint(*xbound), random.randint(*ybound))
        if obj is not None:
            self._clamp(obj)

    def resize (self, w, h):
        """Resizes to a new (w,h) size."""
        self._shape.resize(w, h)

    def _rotate (self, angle, anchor_at='center'): #XXX+TODO
        raise NotImplementedError

    def raise_actions (self, group=None):
        """
        Execute the action(s) in group previously set by the set_action method.
        """
        for func, args, kwords in self._action_groups[group]:
            func(*args, **kwords)

    def set_attrs (self, attrs):
        """Set object attributes.
        attrs => a sequence or iterator of (attribute_name, value) pair
                 or a dictionary like object.
        """
        try:
            attrs = tuple(attrs.items())
        except AttributeError:
            pass
        for attr, value in attrs:
            setattr(self, attr, value)

    def set_action (self, callable, args=None, kwords=None, group=None):
        """Set a new action which will be executed by the raise_actions method.
        Args:
          callable -> a callable object
          args     -> sequence of positional argument for the callable (optional)
          kwords   -> dict of keyword arguments for the callable (optional)
          group    -> name of the action-group this action belongs (optional)

        """

        self._action_groups[group].append((callable, args or (), kwords or {}))

    def del_action_group (self, group):
        """
        Delete the actions registered at group and return it (or None
        if the named group doesn't exsist).
        """
        return self._action_groups.pop(group, None)

# reg GameObject
BaseGameObject.register(GameObject)


class ImageInstanceError (Exception):
    pass

class Image (type):
    _classes = []
    def __new__ (cls, args=None, kwords=None, othercls=None, error=False):
        """
        Returns a new instance of the first succerfully ... TODO
        othercls, if present, can be an already registered class (which is
        tried first) or a non registered class (same, note that this 'external'
        class will be not registered).
        error is interpreted as a boolen value (default: False); if True, an ...error is raised
        at the first instantiation fail, otherwise an ...error is raised only
        if any classes (registered or unregistered) fails to instantiate.
        """
        if othercls is not None:
            try:
                if othercls in cls._classes:
                    c = cls._classes[cls._classes.index(othercls)]
                else:
                    c = othercls
                inst = c(*args or (), **kwords or {})
                return inst
            except Exception as e:
                if error:
                    raise ImageInstanceError(e)
        errors = []
        if not cls._classes:
            raise ImageInstanceError("can't create instance! No object registered.")
        for c in cls._classes:
            try:
                inst = c(*args or (), **kwords or {})
                return inst
            except Exception as e:
                errors.append(e)
                #print "fail with %s ... try next" % c
        else:
            raise ImageInstanceError("Can't create instance! error(s): %s"
                            % ' *** '.join(map(str,errors)))

    @classmethod
    def classes (cls):
        """Returns registered classes."""
        return tuple(cls._classes)

    @classmethod
    def empty (cls):
        """Remove any registered class."""
        cls._classes = []

    @classmethod
    def register(cls, othercls, pos=None):
        """
        Register the class othercls to be used for the instantiation of
        the new  objects.
        The optional argument pos is the (integer) index of the internal
        register list, a class in a lower index is tried first, that is
        it get high precedence.
        """
        if othercls not in cls._classes:
            if pos is None:
                pos = len(cls._classes)
            cls._classes.insert(pos, othercls)


class Board (object):
    def __init__ (self, size=(0,0), flags=0):
        """
        Create a new Board object with size `size`.
        The flags argument is a bitmask of additional features for
        the surface, as in pygame.Surface().
        """
        self._surface = pygame.Surface(size, flags)

    @property
    def size (self):
        """Returns the size of the board."""
        return self._surface.get_size()

    @property
    def surface (self):
        """Returns a copy of the board's surface."""
        return self._surface.copy()

    @property
    def surfref (self):
        """Returns a reference of the board's surface."""
        return self._surface

    def convert (self, obj=None, alpha=True):
        """See gameUtils.convert."""
        if obj is not None:
            if isinstance(obj, (BaseShape,BaseGameObject)):
                obj = obj.surfref
            elif not isinstance(obj, pygame.Surface):
                raise TypeError(
                    "'obj' must be BaseShape, BaseGameObject or pygame.Surface")
        self._surface = gameUtils.convert(self._surface, obj, alpha)

    def draw (self, obj, dest=None, area=None, update=True):
        """
        Draw obj on this board, positioned with the dest argument
        (default: None, i.e. use the obj own position). dest can
        be either a pygame.Rect like object or a pair of coordinates
        representing the top-left corner of obj.
        An optional area can be passed as well. This represents a
        smaller portion of the source surface to draw.
        If update is a true value (the default) update the screen.

        obj => a Board, Shape, GameObject or pygame.Surface object
        dest => a pygame.Rect object, a tuple of (x, y) coordinates or None
        area => a pygame.Rect object or None
        update => bool value (default True)
        """
        if isinstance(obj, pygame.Surface):
            obj = Shape(obj)
        if dest is None:
            dest = obj.rect
        elif isinstance(dest, (Sequence, MutableSequence)):
            r = obj.rect
            r.topleft = dest
            dest = r
        if area is None:
            self._surface.blit(obj.surfref, dest)
        else:
            self._surface.blit(obj.surfref, dest, area)
        if update:
            self.update(dest)

    def fill (self, color, update=True):
        """
        Fill this board with color (anything like a pygame.Color).
        If update is a true value (the default) update the board.
        """
        self._surface.fill(color)
        if update:
            self.update()

    def flags (self, *args):
        """
        Called without arguments, returns the Board's surface flag value,
        otherwise set the surface flag, produced applying the bitwise OR
        operator on *args, then update the board.
        (Note: much of the job is performed by the set_flags method).
        """
        if not args:
            return self._surface.get_flags()
        else:
            self.set_flags(reduce(operator.ior, args))

    def resize (w, h, update=True):
        """
        Resize this board at the new width and height.
        If update is a true value (the default) update the board.
        """
        flags = self.flags()
        surf = self.surface
        self._surface = pygame.Surface((w,h), flags)
        self._surface.blit(gameUtils.surface_resize(surf, w, h), (0,0))
        if update:
            self.update()

    def set_flags (flags, update=True):
        """
        Set the board's surface flags to `flags` (an integer value).
        If update is a true value (the default) update the board.
        """
        surf = self.surface
        self._surface = pygame.Surface(surf.get_size(), flags)
        self._surface.blit(surf, (0,0))
        if update:
            self.update()

    def update (self, portions=None):
        """Not implemented."""
        pass


class Display (Board):
    """
    Since it is basically a specialized Board class wrapping
    the pygame's display, it's a singleton class.
    """
    _inst = None
    def __new__ (cls, size=(0,0), flags=0):
        if cls._inst is None:
            cls._inst = super(Display, cls).__new__(cls, size, flags)
        else:
            if cls._inst.flags() != flags:
                cls._inst.set_flags(flags)
            if cls._inst.size != tuple(size):
                cls._inst.resize(*size)
        return cls._inst

    def __init__ (self, size=(0,0), flags=0):
        """
        Create a display object or returns the existing one.
        The flag argument have the same meaning of the flag argument in
        the pygame.display.set_mode function.
        """
        if not pygame.display.get_init():
            pygame.display.init()
        fs_size = gameUtils.pygame_display_size()
        self._surface = pygame.display.set_mode(size, flags)
        self._default_size_and_mode = type(
            'DefSizeMode', (), {'size':size, 'flags':flags})
        self._fullscreen_size_and_mode = type(
            'FullScrrenSizeMode', (), {'size':fs_size, 'flags':pygame.FULLSCREEN})

    def resize (self, w, h, update=True):
        """
        Resize the display at the new width and height.
        If update is a true value (the default) update the display.
        """
        flags = self.flags()
        s = Shape(self._surface)
        s.resize(w,h)
        self._surface = pygame.display.set_mode((w,h), flags)
        self._default_size_and_mode.size = (w,h)
        self.draw(s)
        if update:
            self.update()

    def set_flags (self, flags, update=True):
        """
        Set the board's surface flags to `flags` (an integer value).
        If update is a true value (the default) update the display.
        """
        surf = self.surface
        self._surface = pygame.display.set_mode(surf.get_size(), flags)
        self._surface.blit(surf, (0,0))
        self._default_size_and_mode.flags = flags
        if update:
            self.update()

    def toggle_fullscreen (self):
        if self._surface.get_flags() & pygame.FULLSCREEN:
            self._surface = pygame.display.set_mode(
                self._default_size_and_mode.size,
                self._default_size_and_mode.flags)
        else:
            self._surface = pygame.display.set_mode(
                self._fullscreen_size_and_mode.size,
                self._fullscreen_size_and_mode.flags)

    def update (self, portions=None):
        """
        Update the display.
        portions can be a single pygame's rect-style object or
        a sequence of them, this allows to update only a portion
        of the screen, otherwise if no argument is passed (or portions is None)
        the entire display will be updated.
        """
        if portions:
            pygame.display.update(portions)
        else:
            pygame.display.update()
            
