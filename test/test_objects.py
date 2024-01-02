#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010-2024  Marco Chieppa (aka crap0101)
# See the file COPYING.txt in the root directory of this package.


# std imports
import glob
import itertools as it
import operator
import os
import os.path as op_
from random import randint, choice
import string
import sys
import unittest
# external imports
import pygame
from pygame.locals import *

DISPLAY_FLAGS = [pygame.HWSURFACE,
                 pygame.RESIZABLE, pygame.NOFRAME,
                 pygame.SCALED, pygame.HIDDEN]


pwd = op_.dirname(op_.realpath(__file__))

try:
    from bumpo import const, gameObjects, baseObjects
    try:
        from bumpo.plugins import gtkGameObject
        HAVE_GTK = True
    except ImportError:
        HAVE_GTK = False
except ImportError:
    os.chdir(op_.join(op_.split(pwd)[0]))
    sys.path.insert(0, os.getcwd())
    sys.modules['bumpo'] = __import__('src')
    from bumpo import const, gameObjects, baseObjects
    try:
        from bumpo.plugins import gtkGameObject
        HAVE_GTK = True
    except ImportError:
        HAVE_GTK = False

ANCHORS = [const.BOTTOMLEFT, const.BOTTOMRIGHT, const.CENTER,
           const.MIDBOTTOM, const.MIDLEFT, const.MIDRIGHT,
           const.MIDTOP, const.TOPLEFT, const.TOPRIGHT]
DIMS = (const.WIDTH, const.HEIGHT)

pygame.init()
SCREEN = pygame.display.set_mode((640,480))
pygame.display.iconify()

COLORS = [tuple(pygame.Color(c))
          for c in 'black green white blue red yellow'.split()]

FONTS_PATH = op_.join(pwd, 'data', 'fonts')
IMAGES_PATH = op_.join(pwd, 'data', 'images')
SOUNDS_PATH = op_.join(pwd, 'data', 'sounds')

_DEF_FONT = op_.join(FONTS_PATH, 'FreeSans.otf')
_DEF_FONT_SIZE = 20

CLSS = [baseObjects.GameObject, gameObjects.GenericGameObject]
if HAVE_GTK:
    CLSS.append(gtkGameObject.GtkGameObject)


def img_cls_reg ():
    baseObjects.Image.empty()
    baseObjects.Image.register(gameObjects.GenericGameObject)
    if HAVE_GTK:
        baseObjects.Image.register(gtkGameObject.GtkGameObject)


def get_random_color ():
    return tuple(randint(0,255) for _ in 'rgba')


class TestShape (unittest.TestCase):
    @staticmethod
    def _create_objects (x=0, y=0, w=100, h=100):
        rect = pygame.Rect(x,y,w,h)
        surf = pygame.Surface((w,h))
        shape1 = baseObjects.Shape(rect)
        shape2 = baseObjects.Shape(surf)
        shape2.move_at((x,y),const.TOPLEFT) # for later attributes comparing
        shape3 = baseObjects.Shape(shape1)
        shape4 = baseObjects.Shape(shape2)
        return shape1, shape2, shape3, shape4 

    def testCreationAndAtttributes (self):
        r = randint
        Shape = baseObjects.Shape
        foo1 = Shape()
        foo2 = Shape(None)
        for obj in (foo1, foo2):
            self.assertIsInstance(obj, baseObjects.Shape)
        objs = self._create_objects(*[r(1,1000) for _ in 'xywh'])
        for obj in objs:
            self.assertIsInstance(obj, baseObjects.Shape)
        for o1, o2 in it.combinations(objs,2):
            for attr in const.SHAPE_RECT_ATTRS + ('area',):
                self.assertEqual(getattr(o1, attr), getattr(o2, attr))
        fakes = (0, 1.1, 'spam', [], (), {}, set(),
                 type('Eggs', (object,), {}), baseObjects.GameObject(),
                 pygame.Rect(0,0,2,3), pygame.Surface((8,9)), complex(1,2))
        for fake in fakes:
            self.assertRaises(TypeError, Shape, [fake])

    def testShapeAttributesAndMethods (self):
        surf = pygame.Surface((10,10), pygame.SRCALPHA)
        c = get_random_color()
        surf.fill(pygame.Color(*c))
        shape = baseObjects.Shape(surf)
        shape.move_at((randint(-1000,1000),randint(-1000,1000)))
        self.assertEqual(pygame.image.tostring(surf, 'RGBA'),
                         pygame.image.tostring(shape.surface, 'RGBA'))
        copy = shape.copy()
        self.assertEqual(pygame.image.tostring(copy.surface, 'RGBA'),
                         pygame.image.tostring(shape.surface, 'RGBA'))
        self.assertEqual(copy.rect, shape.rect)
        for p in (choice(list(zip(range(shape.w), range(shape.h))))
                  for _ in range(10)):
            self.assertEqual(c, shape.at(p))
        for _ in range(20):
            a = randint(0,255)
            shape.alpha = a
            self.assertEqual(shape.alpha, a)

    def testSurface (self):
        pos = 0,0
        for _ in range(10):
            s = pygame.Surface((10,10))
            c1 = choice(COLORS)
            c2 = choice(tuple(set(COLORS).difference([c1])))
            s.fill(c1)
            shape = baseObjects.Shape(s)
            surf = shape.surface
            surf.fill(c2)
            self.assertNotEqual(shape.surface.get_at(pos), surf.get_at(pos))
            self.assertNotEqual(shape.surfref.get_at(pos), surf.get_at(pos))
            shape.surfref.fill(c2)
            self.assertEqual(shape.surface.get_at(pos), surf.get_at(pos))
            self.assertEqual(shape.surfref.get_at(pos), surf.get_at(pos))


class TestGameObjects (unittest.TestCase):

    def testObjectDimensions (self):
        r = randint
        mx, my = SCREEN.get_rect().size
        for dim in ((r(0, mx), r(0, mx)) for _ in range(100)):
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            self.assertEqual(obj.size, dim)
            self.assertEqual(obj.area, operator.mul(*dim))

    def testActions (self):
        for c in CLSS:
            self._testActions(c)

    def _testActions (self, clsobj):
        _acts = {'m+': (lambda o:o.move, (2,2)),
                 'm-': (lambda o:o.move, (-2,-2)),
                 'm=': (lambda o:o.move, (2,-2))}
        obj = clsobj(
            baseObjects.Shape(pygame.Surface((100,100))))
        for name, (func, args) in _acts.items():
            obj.set_action(func(obj), args, group=name)
        topleft = obj.rect.topleft
        for i in range(10):
            for a in _acts:
                obj.raise_actions(a)
                topleft = tuple(map(sum, zip(topleft, _acts[a][1])))
                self.assertEqual(obj.topleft, topleft)
        acts = dict(_acts)
        for name, (f, args) in acts.items():
            self.assertEqual(obj.del_action_group(name), [(f(obj), args, {})])
            self.assertNotEqual(obj.del_action_group(name), [(f(obj), args, {})])
            self.assertEqual(obj.del_action_group(name), None)

    def testObjectsInstance (self):
        for c in CLSS:
            self.assertIsInstance(c(), baseObjects.GameObject)

    def testPropertiesAndMethods (self):
        for c in CLSS:
            self._testPropertiesAndMethods(c)

    def _testPropertiesAndMethods (self, clsobj):
        values1 = (1, True, False, 4, 6, "ciao", "test")
        values2 = (2, False, None, [], "s", "ciao2", "2test")
        values3 = tuple(randint(100,1000) for _ in values2)
        # compare
        for vals in zip(values1, values2, values3):
            objs = [clsobj(cmp_value=v) for v in vals]
            for obj1, obj2 in it.combinations(objs, 2):
                self.assertNotEqual(obj1, obj2)
                self.assertNotEqual(obj1.compare_value, obj2.compare_value)
                tmpv = obj1.compare_value
                obj1.compare_value = obj2.compare_value
                self.assertEqual(obj1, obj2)
                obj1.compare_value = tmpv
                self.assertNotEqual(obj1, obj2)
        # shape attrs
        for attr in const.SHAPE_RECT_ATTRS:
            self.assertTrue(hasattr(clsobj(), attr))
        # velocity
        for _ in range(10):
            obj = clsobj()
            v = tuple(randint(-100,100) for _ in 'xy')
            obj.velocity = v
            self.assertEqual(obj.velocity, v)

    def testMoving (self):
        for c in CLSS:
            self._testMoving(c)

    def _testMoving (self, clsobj):
        shape = baseObjects.Shape()
        shape.resize(*[randint(1, 1000) for _ in 'wh'])
        obj = clsobj(shape)
        # move_bouncing
        bounce = getattr(obj, 'move_bouncing')
        velocity = [(randint(-100,100), randint(-100,100)) for _ in range(50)]
        bs = baseObjects.Shape()
        bs.resize(shape.w*3, shape.h*3)
        for v in velocity:
            bounce(bs, v)
            self.assertTrue(bs.contains(obj.shape))
        # move_random
        randmove = getattr(obj, 'move_random')
        bounds = [[(randint(1,10), randint(10,100)) for _ in range(50)],
                  [(randint(1,10), randint(10,100)) for _ in range(50)]]
        for xbound, ybound in zip(*bounds):
            oldx, oldy = obj.topleft
            randmove(None, xbound, ybound)
            x, y = obj.topleft
            self.assertTrue(x in range(xbound[0]+oldx, xbound[1]+oldx+1))
            self.assertTrue(y in range(ybound[0]+oldy, ybound[1]+oldy+1))

    def testCopy (self):
        for c in CLSS:
            shape = baseObjects.Shape()
            shape.resize(randint(1,10), randint(1,20))
            obj = c(shape, randint(0, 1000))
            self.assertEqual(obj, obj.copy())

    def testReloadOnResize (self):
        g1 = gameObjects.GenericGameObject()
        g2 = gameObjects.GenericGameObject()
        self.assertTrue(g1.reload)
        self.assertTrue(g2.reload)
        g1.reload = False
        g3 = gameObjects.GenericGameObject()
        self.assertFalse(g1.reload)
        self.assertTrue(g2.reload)
        self.assertTrue(g3.reload)
        g1.reload = True
        self.assertTrue(g1.reload)
        objs = [g1,g2,g3]
        values = [False, True]
        for _ in range(10):
            obj = choice(objs)
            val = choice(values)
            othervals_pre = [o.reload for o in objs if o != obj]
            obj.reload = val
            self.assertEqual(obj.reload, val)
            othervals_post = [o.reload for o in objs if o != obj]
            self.assertEqual(othervals_pre, othervals_post)

    def testResizing (self):
        for c in CLSS:
            self._testResizing(c)

    def _testResizing (self, clsobj):
        for arg in (None, pygame.Surface((100, 100)), baseObjects.Shape()):
            obj = clsobj(arg)
            fitshape = baseObjects.Shape()
            clampshape = baseObjects.Shape()
            for size in ((randint(1,900), randint(1,500)) for _ in range(50)):
                # resize
                obj.resize(*size)
                self.assertEqual(obj.size, size)
                # clamp
                clampshape.resize(*size)
                obj.clamp(clampshape)
                self.assertTrue(clampshape.contains(obj.shape))
                if obj.w < 100 or obj.h < 100:
                    obj.resize(1000, 1000)
                    self.assertEqual(obj.size, (1000,1000))
                    clampshape.resize(randint(4,obj.w//2), randint(4,obj.h//2))
                    obj.clamp(clampshape)
                    self.assertFalse(fitshape.contains(obj.shape))
                    self.assertEqual(obj.center, clampshape.center)
                # fit
                if obj.w < 100 or obj.h < 100:
                    obj.resize(1000, 1000)
                fitshape.resize(randint(4, obj.w//2), randint(4, obj.h//2))
                obj.fit(fitshape)
                self.assertTrue(fitshape.contains(obj.shape))
        if hasattr(clsobj, 'scale_perc'):
            obj = clsobj()
            for anchor in ANCHORS:
                w, h = 400, 500
                # scale_perc
                for p in range(10, 200, 10):
                    obj.resize(w, h)
                    old_anchor = getattr(obj, anchor)
                    obj.scale_perc(p, anchor)
                    esize = w*p//100, h*p//100
                    self.assertEqual(obj.size, esize, "%s != %s" % (size, esize))
                    self.assertEqual(getattr(obj, anchor), old_anchor)
                    obj.resize(w, h)
                    # resize_perc_from
                    o = clsobj()
                    o.resize(*list(choice(range(10,200)) for _ in 'wh'))
                    old_anchor = getattr(obj, anchor)
                    obj.resize_perc_from(o, p, anchor)
                    o.scale_perc(p)
                    self.assertEqual(obj.size, o.size)
                    self.assertEqual(getattr(obj, anchor), old_anchor)
                    obj.resize(w, h)
                    # scale_from_dim
                    for dim in DIMS:
                        otherdim = set(DIMS).difference(dim).pop()
                        ovdim = getattr(obj, dim)
                        oodim = getattr(obj, otherdim)
                        old_anchor = getattr(obj, anchor)
                        obj.scale_from_dim(p, dim, anchor)
                        self.assertEqual(getattr(obj, dim), p)
                        self.assertEqual(getattr(obj, otherdim), oodim*p//ovdim)
                        self.assertEqual(getattr(obj, anchor), old_anchor)
                        obj.resize(w, h)
                        # scale_perc_from
                        o = clsobj()
                        o.resize(*list(choice(range(100,2000)) for _ in 'wh'))
                        o_odim = getattr(o, dim)*p//100
                        o_oodim = o_odim*oodim//ovdim
                        if dim == const.WIDTH:
                            osize = (o_odim, o_oodim)
                        else:
                            osize = (o_oodim, o_odim)
                        old_anchor = getattr(obj, anchor)
                        obj.scale_perc_from(o, p, dim, anchor)
                        self.assertEqual(obj.size, osize)
                        self.assertEqual(getattr(obj, anchor), old_anchor)
                        obj.resize(w, h)

    def testClick (self):
        for c in CLSS:
            obj = c()
            for _ in range(50):
                w, h = (randint(10, 1000) for _ in 'wh')
                x, y = (randint(10, 100) for _ in 'xy')
                obj.resize(w, h)
                obj.move(x,y)
                _d = lambda o, p: (o.rect, p)
                for top in range(obj.top+1, obj.bottom, (obj.h//10) or 2):
                    for left in range(obj.left+1, obj.right, (obj.w//10) or 2):
                        point = left, top
                        self.assertTrue(obj.is_clicked(point), "%s" % str(_d(obj,point)))


class TestImage(unittest.TestCase):

    def testPushPop (self):
        reg = []
        self.assertEqual(tuple(), baseObjects.Image.classes())
        self.assertRaises(baseObjects.ImageInstanceError, baseObjects.Image)
        inst = baseObjects.Image(othercls=CLSS[0])
        self.assertIsInstance(inst, CLSS[0])
        self.assertEqual(tuple(), baseObjects.Image.classes())
        for c in CLSS:
            reg.append(c)
            baseObjects.Image.register(c)
            self.assertEqual(tuple(reg), baseObjects.Image.classes())
            inst = baseObjects.Image(othercls=c)
            self.assertIsInstance(inst, c)
        baseObjects.Image.empty()
        self.assertEqual(tuple(), baseObjects.Image.classes())
        for c in CLSS:
            reg.append(c)
            baseObjects.Image.register(c, pos=0)
            inst = baseObjects.Image()
            self.assertIsInstance(inst, c)


class TestFromImageFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        img_cls_reg()

    def setUp(self):
        self.images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(IMAGES_PATH), '*')))

    def testLoadImage(self):
        objects1 = []
        objects2 = []
        for path in self.images_path:
            _, cmpval = op_.split(path)
            objects1.append(baseObjects.Image((path, cmpval)))
            objects2.append(baseObjects.Image((path, cmpval)))
        for obj1, obj2 in zip (objects1, objects2):
            self.assertEqual(obj1, obj2)
            self.assertEqual(obj1.rect, obj2.rect)
            self.assertEqual(obj1.size, obj2.size)
            self.assertEqual(obj1.area, obj2.area)
            self.assertEqual(pygame.image.tostring(obj1.surface, "RGB"),
                             pygame.image.tostring(obj2.surface, "RGB"))
            s1, s2 = obj1.surface, obj2.surface
            for attr in ('get_flags', 'get_bitsize', 'get_bytesize',
                         'get_pitch', 'get_masks', 'get_shifts', 'get_losses'):
                self.assertEqual(getattr(s1, attr)(), getattr(s2, attr)())

    def testLoadFromPath(self):
        objects1 = []
        objects2 = []
        for path in self.images_path:
            _, cmpval = op_.split(path)
            objects1.append(baseObjects.Image((path, cmpval)))
            objects2.append(baseObjects.Image((path, cmpval)))
            self.assertEqual(objects1[-1].compare_value, cmpval)
            self.assertEqual(objects2[-1].compare_value, cmpval)
        for obj1, obj2 in zip (objects1, objects2):
            self.assertEqual(obj1, obj2)
            self.assertEqual(obj1.rect, obj2.rect)
            self.assertEqual(obj1.area, obj2.area)
            self.assertEqual(obj1.size, obj2.size)

    def testLoadFromSurface(self):
        GGO = gameObjects.GenericGameObject
        GI = baseObjects.Image
        objects = list(GI((b, op_.split(b)[-1])) for b in self.images_path)
        objectsG = []
        objectsS = []
        for b in objects:
            objectsG.append(GGO(b.surface, b.compare_value))
            objectsS.append(GGO(b.shape, b.compare_value))
        for obj1, obj2 in zip(objectsG, objectsS):
            self.assertEqual(obj1, obj2)
            self.assertEqual(obj1.rect, obj2.rect)
            self.assertEqual(obj1.area, obj2.area)
            self.assertEqual(pygame.image.tostring(obj1.surface, "RGB"),
                             pygame.image.tostring(obj2.surface, "RGB"))


class TestTextImageObject(unittest.TestCase):

    def setUp(self):
        self.fonts_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(FONTS_PATH), '*')))
        self.test_text = ''.join(choice(string.printable)
                                 for _ in range(randint(10,40)))
    def testArgs(self):
        for arg in [1, type('FOO', (), {})]:
            self.assertRaises(AttributeError,
                              gameObjects.TextImage, arg,0,0,0)
        _r = randint
        for font_path in self.fonts_path:
            fg = get_random_color()
            bg = get_random_color()
            size = _r(1,100)
            font = pygame.font.Font(font_path, size)
            to1 = gameObjects.TextImage(self.test_text, font, size, fg)
            to2 = gameObjects.TextImage(self.test_text, font, size, fg, bg)
            to3 = gameObjects.TextImage(to1, font, size, fg)
            to4 = gameObjects.TextImage(to2, font, size, fg, bg)
            pairs = [(to1, to3), (to2, to4)]
            for obj in it.chain(*pairs):
                w, h = obj.size_of(choice(string.ascii_letters))
                self.assertTrue(w > 0)
                self.assertTrue(h > 0)
            for o1, o2 in pairs:
                self.assertEqual(pygame.image.tostring(o1.surface, "RGB"),
                                 pygame.image.tostring(o2.surface, "RGB"))
                self.assertEqual(o1.fg, o2.fg)
                self.assertEqual(o1.bg, o2.bg)
            for o1, o2 in it.combinations(it.chain(*pairs), 2):
                self.assertEqual(o1.size, o2.size)
                self.assertEqual(o1.fsize, o2.fsize)
                self.assertEqual(o1.text, o2.text)
                self.assertEqual(o1.fname, o2.fname)

    def testLoadAndResize(self):
        _r = randint
        tostring = pygame.image.tostring
        text = self.test_text
        for size in range(5, 50):
            for font_path in self.fonts_path:
                text_color = get_random_color()
                bg_color = get_random_color()
                # test (un)equality for TextImage
                obj1 = gameObjects.TextImage(
                    text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color)
                obj2 = gameObjects.TextImage(
                    text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color)
                self.assertNotEqual(obj1, obj2)
                # now, use the text as compare_value
                obj1 = gameObjects.TextImage(
                    text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color, text)
                obj2 = gameObjects.TextImage(
                    text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color, text)
                for i in range(1, 10):
                    w, h = tuple(_r(size, size*2) for x in 'hw')
                    obj1.resize(w,h)
                    obj2.resize(w,h)
                    self.assertEqual(obj1, obj2)                    
                    self.assertEqual(obj1.rect, obj2.rect)
                    self.assertEqual(obj1.area, obj2.area)
                    self.assertEqual(obj1.size, obj2.size)
                    self.assertEqual(tostring(obj1.surface, "RGB"),
                                     tostring(obj2.surface, "RGB"))

    def testMovement(self):
        _r = randint
        text = self.test_text
        objs = []
        for size in range(5, 150):
            for font_path in self.fonts_path:
                text_color = get_random_color()
                bg_color = get_random_color()
                objs.append(gameObjects.TextImage(
                        text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color))
        for o in objs:
            ocenter = o.center
            otop, oleft = o.top, o.left
            w, h = _r(2,33), _r(5,55)
            o.move(w, h)
            self.assertNotEqual(ocenter, o.center)
            self.assertEqual(o.top, otop+h)
            self.assertEqual(o.left, oleft+w)


class TestGrid (unittest.TestCase):
    def setUp (self):
        self.grows = randint(2, 200)
        self.gcols = randint(2, 200)
        self.gsize = tuple(randint(100, 1000) for _ in 'wh')
        self.grid = gameObjects.Grid(self.grows, self.gcols, self.gsize)

    def testGridInit (self):
        for _ in range(20):
            self.setUp()
            self.assertEqual(self.grid.dims, (self.grows, self.gcols))
            self.assertEquals(self.grid.size, self.gsize)

    def testGridShuffle (self):
        for _ in range(20):
            cell = gameObjects.GenericGameObject()
            cell.resize(*[randint(1,50) for _ in 'wh'])
            self.grid.add([cell.copy() for _ in range(self.grows*self.gcols)])
            old = []
            for i, cell in enumerate(self.grid.values()):
                cell.compare_value = i
                old.append(i)
            self.grid.shuffle()
            new = [cell.compare_value for cell in self.grid.values()]
            self.assertNotEqual(old, new)
            self.setUp()

    def testGridMove (self):
        for _ in range(10):
            anchor = choice(ANCHORS)
            point = tuple(randint(1, 1000) for _ in 'wh')
            self.grid.move_at(point, anchor)
            self.assertEqual(point, getattr(self.grid.rect, anchor))
            x, y = tuple(randint(1, 1000) for _ in 'wh')                
            xold, yold = self.grid.rect.topleft
            self.grid.move(x, y)
            xnew, ynew = self.grid.rect.topleft
            self.assertEqual(x + xold, xnew)
            self.assertEqual(y + yold, ynew)

    def testGridResize (self):
        for _ in range(10):
            newsize = tuple(randint(1, 1000) for _ in 'wh')
            self.grid.resize(*newsize)
            self.assertEqual(self.grid.size, newsize)

    def testGridAdd (self):
        total = self.grows * self.gcols
        GE = gameObjects.GenericGameObject
        objs = [GE(cmp_value=i) for i in range(total)]
        rest = self.grid.add(objs)
        self.assertFalse(rest)
        for i, (pos, val) in enumerate(self.grid.items()):
            self.assertEqual(val.compare_value, i, "%d != %d %s" % (val.compare_value, i, self.grid.dims))
        for i in range(10):
            self.setUp()
            total = self.grows * self.gcols
            sub = randint(1, total-2)
            objs = [GE(cmp_value=i) for i in range(sub)]
            rest = []
            for i in range(total//sub+1):
                rest = self.grid.add(objs)
            self.assertEqual(sub-total%sub, len(rest))
            self.setUp()
            total = self.grows * self.gcols
            excess = randint(total+1, total+100)
            objs = [GE(cmp_value=i) for i in range(excess)]
            rest = self.grid.add(objs)
            self.assertEqual(total, excess-len(rest))


class TestBoardAndDisplay (unittest.TestCase):

    def _testCreation(self, clsobj):
        for size in ((randint(10,1000), randint(10,1000)) for _ in range(20)):
            for flag in (0, pygame.SRCALPHA):
                if issubclass(clsobj, baseObjects.Display):
                    dflag = pygame.HIDDEN
                    for _ in range(3):
                        dflag |= choice(DISPLAY_FLAGS)
                    board = clsobj(size, dflag)
                else:
                    board = clsobj(size, flag)
                if issubclass(clsobj, baseObjects.Display):
                    self.assertTrue(board.get_flags() & dflag)
                self.assertEqual(board.size, size)

    def _testDrawAndFill(self, clsobj):
        tostring = pygame.image.tostring
        colors = set(get_random_color() for _ in range(10))
        objs = []
        pos = (0,0)
        for c in COLORS:
            for update in (True, False):
                if issubclass(clsobj, baseObjects.Display):
                    board = clsobj((10,10)) #, pygame.HIDDEN)
                else:
                    board = clsobj((10,10))
                old_color = board.surfref.get_at(pos)
                if issubclass(clsobj, baseObjects.Display):
                    board.fill(c, update=update)
                else:
                    board.fill(c)
                new_color = board.surfref.get_at(pos)
                if old_color != c:
                    self.assertNotEqual(old_color, new_color)
        # draw pygame surfaces
        for _ in range(10):
            w,h = size = randint(10,100), randint(10,100)
            color = randint(1,255), randint(1,255), randint(1,255)
            bc = (0,0,0)
            board = clsobj(size)
            board.fill(bc)
            self.assertEqual(bc, board.surfref.get_at((1,1)))
            s = pygame.Surface(size)
            s.fill(color)
            self.assertEqual(color, s.get_at((1,1)))
            board.draw(s)
            self.assertEqual(s.get_at((1,1)),
                             board.surfref.get_at((1,1)),
                             msg='surface color:{} | board color:{} [{}|{}]'.format(
                                 color, bc, s.get_rect(),board.surfref.get_rect()))
            board.fill(bc)
            board.draw(s, pygame.Rect(0, 0, w//2, h//2), pygame.Rect(0, 0, w//2, h//2))
            self.assertEqual(s.get_at((0,0)), board.surfref.get_at((0,0)))
            self.assertNotEqual(s.get_at((0,0)), board.surfref.get_at((w//2+1,h//2+1)))
            board.fill(bc)
            r = pygame.Rect(0,0,w//2,h//2)
            r.topleft = r.center
            board.draw(s, r)
            self.assertNotEqual(s.get_at((0,0)), board.surfref.get_at((0,0)))
            self.assertEqual(s.get_at((0,0)), board.surfref.get_at((w//2,h//2)))
            board.fill(bc)
            r.topleft = 0,0
            board.draw(s, area=r)
            self.assertEqual(s.get_at((0,0)), board.surfref.get_at((0,0)))
            self.assertNotEqual(s.get_at((0,0)), board.surfref.get_at((w//2,h//2)))
        # draw game objects
        for c in colors:
            for _ in range(10):
                s = pygame.Surface((randint(1,100), randint(1,100)))
                s.fill(c)
                center = tuple(randint(0, d) for d in s.get_size())
                pygame.draw.circle(s, get_random_color(), center, randint(1, s.get_width()))
                objs.append(gameObjects.GenericGameObject(s))
        w, h = size = randint(100, 500), randint(100, 700)
        bound = baseObjects.Shape(pygame.Surface((w*90//100,h*90//100)))
        bound.move_at((w//2,h//2))
        for update in (False, True):
            board = clsobj(size)
            for obj in objs:
                obj.fit(bound)
                obj.move_bouncing(bound)
                board.draw(obj, update=update)
                if not update and issubclass(clsobj, baseObjects.Display):
                    self.assertEqual(tostring(pygame.display.get_surface(), "RGB"),
                                     tostring(board.surface, "RGB"),
                                     "board surfaces not equals!")
                    board.update()
                surf = board.surface.subsurface(obj.rect)
                surf = surf.convert_alpha(board.surfref)
                self.assertNotEqual(tostring(obj.surface, "RGB"),
                                 tostring(surf, "RGB"),
                                 "A:{} != {} ({})".format(obj.surface,surf, clsobj))
                # draw in another position
                s = baseObjects.Shape(obj.surface)
                obj.move_bouncing(bound)
                board.draw(s, obj.rect, update=update)
                if not update and issubclass(clsobj, baseObjects.Display):
                    self.assertEqual(tostring(pygame.display.get_surface(), "RGB"),
                                     tostring(board.surface, "RGB"),
                                     "board surfaces not equals!")
                    board.update()
                surf = board.surface.subsurface(obj.rect)
                self.assertNotEqual(tostring(s.surface, "RGB"),
                                 tostring(surf, "RGB"),
                                 "B:%s != %s" % (s.surface,surf))

    def testCreation(self):
        for clsobj in (baseObjects.Board, baseObjects.Display):
            self._testCreation(clsobj)

    def testDrawAndFill(self):
        for clsobj in (baseObjects.Board, baseObjects.Display):
            self._testDrawAndFill(clsobj)



def load_tests (args=None):
    loader = unittest.TestLoader()
    if not args:
        test_cases = (TestShape, TestGameObjects, TestImage,
                      TestFromImageFiles, TestTextImageObject,
                      TestGrid, TestBoardAndDisplay)
    else:
        g = globals()
        test_cases = (g[t] for t in args)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)



if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(load_tests(sys.argv[1:])))
    pygame.quit()
