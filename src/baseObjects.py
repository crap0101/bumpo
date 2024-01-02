# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010-2024  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


# std imports
from collections import defaultdict, namedtuple
try:
    from collections import Sequence, MutableSequence
except ImportError:
    from collections.abc import Sequence, MutableSequence
from functools import reduce
import operator
import random
import types
# local imports
from bumpo import gameUtils
from bumpo.const import SHAPE_RECT_ATTRS, CENTER, TOPLEFT
# external imports
import pygame

Velocity = namedtuple('Velocity', 'x y')

class ShapeMeta (type):
    """
    Shape metaclass used for set SHAPE_RECT_ATTRS attributes
    of the underlying pygame.Rect to the Shape instances.
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

class Shape (metaclass=ShapeMeta):
    def __init__ (self, obj=None):
        """
        Create a new Shape instance from obj.
        obj can be a pygame.Rect, a pygame.Surface, another shape
        or None (in the latter case a zero-sized shape is created).
        Raise TypeError for a non conforming object obj.
        """
        self._alpha_flag = 0
        if obj is None:
            self._surface = pygame.Surface((0,0))
            self._rect = self._surface.get_rect()
             # force alpha to be 0 instead of None for non sets alpha values.
            self.alpha = self._surface.get_alpha() or 0
        elif isinstance(obj, pygame.Rect):
            self._rect = pygame.Rect(obj)
            self._surface = pygame.Surface(obj.size)
            self.alpha = 0
        elif isinstance(obj, pygame.Surface):
            self._surface = obj.copy()
            self._rect = obj.get_rect()
            self.alpha = obj.get_alpha() or 0
        elif isinstance(obj, Shape):
            self._surface = obj.surface
            self._rect = obj.rect
            self.alpha = obj.alpha or 0
            self._alpha_flag = obj.get_alpha_flag()
        else:
            raise TypeError("Can't initialize a Shape object from <{}>".format(obj))
        self.convert()

    @property
    def alpha (self):
        """
        Returns the surface alpha value for this Shape.
        If the alpha value is not set then None is returned.
        """
        return self._surface.get_alpha()
    @alpha.setter
    def alpha (self, a):
        """
        Sets the surface alpha value for this Shape.
        The alpha value must be an integer from 0 to 255,
        0 is fully transparent and 255 is fully opaque.
        If None is passed for the alpha value, then the alpha will be disabled.
        """
        self._surface.set_alpha(a)

    def get_alpha_flag (self):
        """
        Return the current alpha flag for this Shape.
        """
        return self._alpha_flag

    def set_alpha_flag(self, alpha_flag):
        """
        Sets the alpha flag for this surface (must be 0 or pygame.RLEACCEL).
        """
        if alpha_flag not in (0, pygame.RLEACCEL):
            raise ValueError("Wrong value for alpha flag: {}".format(alpha_flag))
        self._alpha_flag = alpha_flag
        self._surface.set_alpha(self.alpha, alpha_flag)
        
    @property
    def area (self):
        """Returns the Shape's area."""
        return self.w * self.h

    def get_flags(self):
        return self._surface.get_flags()
    
    def at (self, point):
        """
        Returns a copy of the RGBA Color value at the given (x,y) point.
        If the pixel position is outside the area of the Shape
        an IndexError exception will be raised.
        """
        return self._surface.get_at(point)

    def set_at (self, point, color=None):
        """
        Sets the $color at $point.
        """
        self._surface.set_at(point, color)

    @property
    def rect (self):
        """Returns a copy of the Shape's rect."""
        return pygame.Rect(self._rect)

    @property
    def surface (self):
        """Returns a copy of the Shape's surface."""
        return self._surface.copy()

    @property
    def surfref (self):
        """Returns a reference of the Shape's surface."""
        return self._surface

    def clamp (self, obj):
        """
        Moves this Shape to be completely inside obj.
        If it is large to fit inside, it is centered inside the argument shape,
        but its size is not changed.
        """
        self._rect.clamp_ip(obj.rect)

    def contains (self, obj):
        """
        Return True if the argument shape is completely inside this Shape.
        """
        return bool(self._rect.contains(obj.rect))

    def collide (self, obj):
        """
        Returns True if any portion of either shape overlap
        (except the top+bottom or left+right edges). 
        """
        return bool(self._rect.colliderect(obj.rect))

    def collidepoint (self, point):
        """
        Returns true if the given point is inside this Shape.
        A point along the right or bottom edge is not considered to be inside. 
        """
        return bool(self._rect.collidepoint(point))

    def convert (self, reference_obj=None, alpha=True):
        """See gameUtils.convert."""
        if reference_obj is not None:
            if isinstance(reference_obj, Shape):
                pass
            elif isinstance(reference_obj, pygame.Surface):
                reference_obj = Shape(reference_obj)
            else:
                raise TypeError(
                    "'obj' must be Shape, GameObject or pygame.Surface")
        self._surface = gameUtils.convert(self.surfref, reference_obj, alpha)
        self.alpha = self._surface.get_alpha()

    def copy (self):
        """Returns a new shape from this Shape,
        copying its surface, rect and position.
        """
        return Shape(self)

    def fill (self, color):
        """Fill the Shape surface with a solid $color
        (anything accepted by pygame.Surface.fill)."""
        self._surface.fill(color)

    def fit (self, obj):
        """
        Move and resize this Shape to fit the argument shape.
        The aspect ratio of the Shape is preserved, so the new size
        may be smaller than the target in either width or height.
        Raise TypeError for invalid objects.
        """
        if isinstance(obj, (Shape, pygame.Surface)):
            rect = obj.rect
        elif isinstance(obj, pygame.Rect):
            rect = obj
        else:
            raise TypeError("Unknown object type: <{}>".format(type(obj)))
        self._rect = self._rect.fit(rect)
        self._surface = gameUtils.surface_resize(self._surface, self.w, self.h)

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
        self._rect.size = w, h

    def rotate (self, angle, anchor_at='center'): #XXX+TODO
        raise NotImplementedError

    def set_surface(self, surf):
        """Set the $surf Surface as the object surface. """
        center = self._rect.center
        self._surface = surf.copy()
        self._rect = self._surface.get_rect()
        self.alpha = surf.get_alpha()
        self._rect.center = center
        

class GameObject(Shape):
    def __init__ (self, obj=None, cmp_value=None):
        """
        Create a new GameObject instance, optionally from an existing
        object obj, which can be a pygame.Surface, a Shape compatible
        object, another GameObject or None (the default).
        Raise TypeError otherwise.
        cmp_value should be a special value which will be used in
        object's comparison, or None.
        cmp_value is None by default, which set it to id(self) unless
        obj is itself a GameObject, in which case its cmp_value is used
        (as its velocity). In such a case, to set cmp_value to id(self)
        pass a CopyValue instance instead of None.
        """
        self._cmp_value = id(self) if cmp_value is None else cmp_value
        self._velocity = Velocity(0,0)
        super().__init__(obj)
        if isinstance(obj, GameObject):
            self._velocity = obj.velocity
            if ((not cmp_value)
            and (not isinstance(cmp_value, gameUtils.CopyValue))):
                self._cmp_value = id(self)
        elif not isinstance(obj, (pygame.Surface, Shape, types.NoneType)):
            raise TypeError("Can't create an instance from <{}>".format(obj))
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
        return Shape(self)

    @property
    def velocity (self):
        return self._velocity
    @velocity.setter
    def velocity (self, xyv):
        self._velocity = Velocity(*xyv)

    def __eq__(self, other):
        return self._cmp_value == other

    def __ne__ (self, other):
        return not (self == other)

    def clamp (self, obj):
        """
        Clamps this object into obj (a pygame.Rect, a pygame.Surface,
        a Shape or derived object) or raise TypeError.
        """
        if isinstance(obj, pygame.Rect):
            super().clamp(Shape(obj))
        elif isinstance(obj, pygame.Surface):
            super().clamp(Shape(obj.get_rect()))
        elif isinstance(obj, Shape):
            super().clamp(obj)
        else:
            raise TypeError("Unsupported object to clamp in: <{}>".format(obj))

    def copy (self):
        """Returns a copy of this object."""
        return GameObject(self, self._cmp_value)

    def is_clicked (self, point=None):
        """
        Return True if the (x,y pair) point is inside the object's shape.
        A point along the right or bottom edge is not considered to be
        inside. Without argument use the result of pygame.mouse.get_pos().
        """
        return self.collidepoint(point or pygame.mouse.get_pos())

    def move_bouncing (self, obj, velocity=None):
        """
        Move the object bouncing inside *obj* (either a pygame.Rect, a
        pygame.Surface, a GameObject or a Shape object) by velocity,
        a pair of integer values, or None (in the latter case, the
        object's own velocity is used).
        """
        if isinstance(obj, pygame.Surface):
            obj = obj.get_rect()
        x, y = velocity if velocity is not None else self.velocity
        vx, vy = x, y
        if (self.left + x <= obj.left or self.right + x >= obj.right):
            vx = -x
        if (self.bottom + y >= obj.bottom or self.top + y <= obj.top):
            vy = -y
        self.move(x, y)
        self.velocity = (vx, vy)
        self.clamp(obj)

    def move_random (self, obj=None, xbound=None, ybound=None):
        """
        Move the object in a new pseudo-random position.
        xbound and ybound are a pair of integer representing the
        range in which choose the random value for each coordinate movement,
        or None (in the latter case, the object's velocity attr will be used).
        obj is an optional object (pygame.Rect, pygame.Surface, GameObject or Shape)
        used as bounding box, otherwise the object is free to move along
        the plane without limits (even negative ones).
        """
        if xbound is None:
            xbound = (0, self.velocity.x)
        if ybound is None:
            ybound = (0, self.velocity.y)
        self.move(random.randint(*xbound), random.randint(*ybound))
        if obj is not None:
            self.clamp(obj)

    def rotate (self, angle, anchor_at=CENTER): #XXX+TODO
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
          callable => callable object
          args     => seq of positional argument for the callable (optional)
          kwords   => dict of keyword arguments for the callable (optional)
          group    => name of the action-group this action belongs (optional)
        """
        self._action_groups[group].append((callable, args or (), kwords or {}))

    def del_action_group (self, group):
        """
        Delete the actions registered at group and return it (or None
        if the named group doesn't exsist).
        """
        return self._action_groups.pop(group, None)



class ImageInstanceError (Exception):
    pass

class Image (type): # <-- XXX+TODO: don't remember this... thing, actually.
    _classes = []
    def __new__ (cls, args=None, kwords=None, othercls=None, error=False):
        """
        Returns a new instance of the first succerfully ... XXX+TODO: write a sensible docstring
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
        else:
            raise ImageInstanceError("Can't create instance! error(s): {}".format(
                ' *** '.join(map(str,errors))))

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
        Register the class othercls to be used for the instantiation
        of the new  objects.
        The optional argument pos is the (integer) index of the internal
        register list: a class in a lower index gets high precedence
        and is tried first.
        """
        if othercls not in cls._classes:
            if pos is None:
                pos = len(cls._classes)
            cls._classes.insert(pos, othercls)


def draw_method (self, obj, dest=None, area=None, update=True):
    """A draw method for Board and Display.
    Blits obj on self; dest are topleft coordinates or None (in
    this case use the obj one; area is the smallest portion
    to blit (from the topleft corner anyway)."""
    if isinstance(obj, pygame.Surface):
        surf = obj
        if dest is None:
            dest = obj.get_rect()
        if area is None:
            area = obj.get_rect()
    elif isinstance(obj, Shape):
        surf = obj.surfref
        if dest is None:
            dest = obj.rect
        if area is None:
            area = obj.rect
            area.topleft = (0,0) #XXX+TODO: NOTE: area doesn't work if the rect is not at topleft
    else:
        raise TypeError("Unknown object <{}>".format(obj))
    self._surface.blit(surf, dest, area)
    if update:
        self.update(dest)


class Board(Shape):
    """A Shape with a draw() method to blit on its Surface."""
    def __init__(self, size, flags=0):
        super().__init__(pygame.Surface(size, flags))

    draw = draw_method

    def update(self, *a, **k):
        NotImplemented

class Display:
    """
    A sort of specialized Board class, wrapping
    the pygame's display, so it's a singleton class.
    """
    _inst = None
    def __new__ (cls, size=(0,0), flags=0):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            return cls._inst
        else:
            if flags:
                cls._inst.set_flags(flags)
            if tuple(cls._inst.size) != tuple(size):
                cls._inst.resize(*size)
            return cls._inst

    def __init__ (self, size=(0,0), flags=0):
        """
        Create a display object or returns the existing one.
        The flags argument have the same meaning of the flag argument in
        the pygame.display.set_mode function.
        """
        if not pygame.display.get_init():
            pygame.display.init()
        self._surface = pygame.display.set_mode(size, flags)
        self._default_size = size
        self._default_flags = flags
        self._fullscreen_size = gameUtils.pygame_display_size()
        self._fullscreen_flags = flags | pygame.FULLSCREEN

    @property
    def size (self):
        """Returns the Display size."""
        return self._surface.get_size()
    
    @property
    def surface (self):
        """Returns a copy of the Display surface."""
        return self._surface.copy()

    @property
    def surfref (self):
        """Returns a reference of the Display surface."""
        return self._surface

    draw = draw_method
        
    def fill (self, color, update=True):
        """
        Fill the Display with color (anything like a pygame.Color).
        If update is a true value (the default) update the board.
        """
        self._surface.fill(color)
        if update:
            self.update()
            
    def resize (self, w, h, update=True):
        """
        Resize the display at the new width and height.
        If update is a true value (the default) update the display.
        """
        s = Shape(self.surfref)
        flags = s.get_flags()
        s.resize(w, h)
        self._surface = pygame.display.set_mode((w, h), self._default_flags)
        self._default_size = (w, h)
        self.draw(s)

    def get_flags (self):
        """
        Get the display flags.
        """
        return self._default_flags

    def set_flags (self, flags, update=True):
        """
        Set the display flags to `flags` (an integer value).
        If update is a true value (the default) update the display.
        """
        s = Shape(self.surfref)
        self._surface = pygame.display.set_mode(self._default_size, flags)
        self.draw(s.surfref)
        self._default_flags = flags
        if update:
            self.update()

    def set_caption(self, string):
        pygame.display.set_caption(string)
        
    def toggle_fullscreen (self):
        #XXX: why not used directly: pygame.display.toggle_fullscreen()
        # uhm... there was a good reason... don't remember which :D
        if self.get_display_flags() & pygame.FULLSCREEN:
            self._surface = pygame.display.set_mode(
                self._default_size,
                self._default_flags)
        else:
            '''if self._default_size != self._fullscreen_size:
                s = Shape(self.surfref)
                s.resize(self._fullscreen_size)'''
            self._surface = pygame.display.set_mode(
                self._fullscreen_size,
                self._fullscreen_flags)
        self.update()

    def update (self, portions=None):
        """
        Update the display.
        portions can be a single pygame's rect-style object or
        a sequence of them, this allows to update only a portion of
        the screen, otherwise if no argument is passed (or portions is None)
        the entire display will be updated.
        """
        if portions is not None:
            pygame.display.update(portions)
        else:
            pygame.display.update()
