#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2011  Marco Chieppa (aka crap0101)
# See the file COPYING.txt in the root directory of this package.


import os
import sys
import glob
import random
import os.path as op_
import itertools as it_
import pygame
from pygame.locals import *
import unittest


pwd = op_.dirname(op_.realpath(__file__))

try:
    from bumpo import gameObjects
    from bumpo import gameutils
except ImportError:
    bumpopackdir = op_.split(pwd)[0]
    sys.path.insert(0, bumpopackdir)
    import gameObjects
    import gameutils

pygame.init()
SCREEN = pygame.display.set_mode((640,480))
pygame.display.iconify()

FONTS_PATH = op_.join('data', 'fonts')
IMAGES_PATH = op_.join('data', 'images')
SOUNDS_PATH = op_.join('data', 'sounds')

_DEF_FONT = op_.join(FONTS_PATH, 'FreeSans.otf')
_DEF_FONT_SIZE = 20


class TestGenericGameObject(unittest.TestCase):

    def testObjectDimensions(self):
        maxX, maxY = SCREEN.get_rect().size
        for dim in ((random.randint(0, maxX),
                     random.randint(0, maxY)) for i in range(100)):
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            self.assertTrue(obj.rect.size == obj.surface.get_size())
            w, h = dim
            self.assertTrue(obj.area == w * h)

    def testRectAttr(self):
        _r = random.randint
        attrs_ = [{'center':2, 'width':1, 'height':1},
                  {'centerx':1, 'centery':1, 'size':2},
                  {'w':1, 'h':1, 'topleft':2}]
        dim = (1,1)
        for i in range(100):
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            old_rect = gameutils.copy_rect(obj.rect)
            for attrs in attrs_:
                d1 = list((k, _r(66, 99) if v < 2 else tuple(_r(66, 200) for x in range(v)))
                    for k,v in attrs.items())
                d2 = dict(d1)
                obj.set_rect_attrs(d1)
                new_rect1 = gameutils.copy_rect(obj.rect)
                self.assertEqual(obj.rect, new_rect1)
                obj.set_rect_attrs(d2)
                new_rect2 = gameutils.copy_rect(obj.rect)
                self.assertEqual(obj.rect, new_rect2)
                for rect in (new_rect1, new_rect2):
                    for attr in attrs.iterkeys():
                        self.assertNotEqual(getattr(old_rect, attr), getattr(rect, attr))
        self.assertRaises(TypeError, obj.set_rect_attrs, [1,2,3,4])
        self.assertRaises(TypeError, obj.set_rect_attrs, (1,2,3,4))
        self.assertRaises(TypeError, obj.set_rect_attrs, ((1,2) for i in 'xxx'))
        self.assertRaises(ValueError, obj.set_rect_attrs, ['h', (1 for i in 'xx')])
        self.assertRaises(AttributeError, obj.set_rect_attrs, {'h':2, 'foo':0})
        self.assertRaises(AttributeError, obj.set_rect_attrs, {'bla!':2})


    def testSetSurface(self):
        _r = random.randint
        old_color = (0,0,0,255)
        old_size = (10, 10)
        _obj = gameObjects.GenericGameObject(pygame.Surface(old_size))
        self.assertTrue(isinstance(_obj.original_surface, pygame.Surface))
        self.assertEqual(_obj.original_surface.get_size(), _obj.surface.get_size())
        self.assertEqual(gameutils.average_color(_obj.original_surface),
                         gameutils.average_color(_obj.surface))
        for i in range(100):
            obj = gameObjects.GenericGameObject(pygame.Surface(old_size))
            obj.surface.fill(old_color)
            old_surface = obj.surface.copy()
            old_w, old_h = old_surface.get_size()
            new_color_1 = (_r(11,255),_r(11,255),_r(11,255),255)
            new_color_2 = (_r(11,255),_r(11,255),_r(11,255),255)
            new_size_1 = (_r(11,200),_r(11,200))
            new_size_2 = (_r(1,9),_r(1,9))
            for s, c in zip((new_size_1, new_size_2), (new_color_1, new_color_2)):
                new_surface = pygame.Surface(s)
                new_surface.fill(c)
                new_w, new_h = new_surface.get_size()
                obj.set_surface(new_surface)
                self.assertTrue(obj.rect.size == new_surface.get_size())
                self.assertTrue(obj.surface.get_size() == new_surface.get_size())
                self.assertFalse(old_surface.get_at((_r(0,old_w-1), _r(0,old_h-1)))
                                 == obj.surface.get_at((_r(0,new_w-1), _r(0,new_h-1))))
                obj.set_surface(old_surface)
                self.assertFalse(obj.rect.size == new_surface.get_size())
                self.assertTrue(obj.rect.size == old_surface.get_size())
                self.assertFalse(obj.surface.get_size() == new_surface.get_size())

    def testObjectDimensionsOnChange(self):
        _r = random.randint
        screen_rect = SCREEN.get_rect()
        maxX, maxY = SCREEN.get_rect().size
        for dim in ((random.randint(2, maxX-2),
                     random.randint(2, maxY-2)) for i in range(100)):
            # test move, move_at, clamp
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            old_rect = gameutils.copy_rect(obj.rect)
            old_surround_rect = gameutils.copy_rect(obj.surround_rect)
            dim = (maxX*2, maxY*2)
            for moving, args in (('move', dim),
                                 ('move_at', [(dim,)])):
                getattr(obj, moving)(*args)
                self.assertFalse(screen_rect.contains(obj.rect))
                self.assertTrue(obj.rect.size == old_rect.size)
                self.assertTrue(obj.surround_rect.size == old_surround_rect.size)
                obj.clamp(screen_rect)
                self.assertTrue(screen_rect.contains(obj.rect))
        # another test for move_at
        obj = gameObjects.GenericGameObject(pygame.Surface((maxX/2, maxY/2)))
        old_surround_rect = gameutils.copy_rect(obj.surround_rect)
        for attr in ('topleft', 'topright', 'bottomleft', 'bottomright'):
            obj.move_at(getattr(screen_rect, attr))
            self.assertFalse(screen_rect.contains(obj.rect))
            obj.move_at(getattr(screen_rect, 'center'), attr)
            self.assertTrue(screen_rect.contains(obj.rect))
            self.assertTrue(obj.surround_rect.size == old_surround_rect.size)
        # test for move_bouncing and move_random
        bounce_rect = gameutils.copy_rect(screen_rect)
        for i in range(2, 10):
            obj1 = gameObjects.GenericGameObject(pygame.Surface((maxX/i, maxY/i)), 1)
            obj2 = gameObjects.GenericGameObject(pygame.Surface((maxX/i, maxY/i)), 2)
            obj3 = gameObjects.GenericGameObject(pygame.Surface((maxX/i, maxY/i)), 3)
            cell1 = gameObjects.Cell(pygame.Surface((maxX/i, maxY/i)))
            item1 = gameObjects.Image(pygame.Surface((cell1.rect.w/2+1, cell1.rect.h/2+1)))
            cell1.add_item(item1, {'top':'bottom'})
            cell2 = gameObjects.Cell(pygame.Surface((maxX/i, maxY/i)))
            item2 = gameObjects.Image(pygame.Surface((cell2.rect.w/2, cell2.rect.h/2)))
            cell2.add_item(item2, {'bottomright':'topleft'})
            self.assertTrue(obj1.area == obj2.area)
            obj1.velocity = (_r(-11, 14), _r(-11, 14))
            for bouncing in range(500):
                urect1 = cell1.urect
                urect2 = cell2.urect
                obj1.move_bouncing(bounce_rect)
                obj2.velocity = (_r(-11, 14), _r(-11, 14))
                obj3.velocity = obj2.velocity
                obj2.move_bouncing(bounce_rect)
                obj3.move_random(bounce_rect)
                c_rect1 = gameutils.copy_rect(cell1.rect)
                c_rect2 = gameutils.copy_rect(cell2.rect)
                cell1.move_bouncing(bounce_rect, (_r(-11, 14), _r(-11, 14)), _r(0,1))
                cell2.move_bouncing(bounce_rect, (_r(-11, 14), _r(-11, 14)), _r(0,1))
                for obj in (obj1, obj2, obj3, cell1, cell2):
                    self.assertTrue(bounce_rect.contains(obj.rect))
                self.assertEqual(cell1.area, gameutils.rect_area(c_rect1))
                self.assertEqual(cell1.area, gameutils.rect_area(c_rect1))
                self.assertEqual(cell2.area, gameutils.rect_area(c_rect2))
                self.assertEqual(gameutils.rect_area(urect2), cell2.uarea)
        cell1.set_item_attrs({'center':'topleft'})
        self.assertEqual(cell1.rect.topleft, cell1.item.rect.center)
        cell1.set_item_attrs({'center':'bottomright'}, False)
        self.assertEqual(cell1.rect.topleft, cell1.item.rect.center)
        cell1.move(1, 1)
        self.assertNotEqual(cell1.rect.topleft, cell1.item.rect.center)
        self.assertEqual(cell1.rect.bottomright, cell1.item.rect.center)
        cell1.set_item_attrs({'bottomleft':None}, False)
        self.assertEqual(cell1.rect.bottomright, cell1.item.rect.center)
        cell1.update_item()
        self.assertEqual(cell1.rect.bottomleft, cell1.item.rect.bottomleft)
        attrs = ('width', 10), ('h', 20), ('center', (22,33))
        cell2.set_item_attrs((attrs))
        cell2.move(0, 0)
        for attr, value in attrs:
            self.assertEqual(getattr(cell2.item.rect, attr), value)            
        for x1 in (None, 100):
            for y1 in (None, 100):
                for x2 in (None, 100):
                    for y2 in (None, 100):
                        obj3.move_random(bounce_rect, (x1, x2), (y1, y2))
                        self.assertTrue(bounce_rect.contains(obj3.rect))
        self.assertRaises(TypeError, obj3.move_random, bounce_rect, 1, 2)
        self.assertRaises(TypeError, obj3.move_random, bounce_rect, 1, (2,2))
        self.assertRaises(TypeError, obj3.move_random, bounce_rect, (0,1,3), 2)
        self.assertRaises(TypeError, obj3.move_random, bounce_rect, [], (False,False))
        self.assertRaises(TypeError, obj3.move_random, bounce_rect, 1, "1")
        self.assertRaises(TypeError, obj3.move_random, obj.surface, 1, "1")
        # test resize
        obj = gameObjects.GenericGameObject(pygame.Surface((12, 12)))
        fit_obj = gameObjects.GenericGameObject(pygame.Surface((6, 6)))
        obj.resize_perc_from(obj.rect, 50)
        self.assertTrue(obj.rect.size == fit_obj.rect.size)
        self.assertTrue(obj.area == fit_obj.area)
        obj = gameObjects.GenericGameObject(pygame.Surface((128, 153)))
        old_w, old_h = obj.rect.size
        x_values = list(x for x in it_.chain(range(1, old_w), range(old_w+1, old_w*2)))
        y_values = list(x for x in it_.chain(range(1, old_h), range(old_h+1, old_h*2)))
        for i in range(500):
            old_rect = gameutils.copy_rect(obj.rect)
            obj.resize(random.choice(x_values), random.choice(y_values))
            self.assertTrue(obj.rect.size != old_rect.size)
            self.assertTrue(obj.surface.get_size() != old_rect.size)
            obj.rect.size = (old_w, old_h)
        # test fit
        obj = gameObjects.GenericGameObject(pygame.Surface((12, 12)))
        fit_obj = gameObjects.GenericGameObject(pygame.Surface((6, 6)))
        obj.fit(fit_obj.rect)
        self.assertTrue(fit_obj.rect.contains(obj.rect))

    def testSurroundRect(self):
        maxX, maxY = SCREEN.get_rect().size
        # test equality on perc
        obj = gameObjects.GenericGameObject(pygame.Surface((maxX, maxY)))
        old_rect = gameutils.copy_rect(obj.rect)
        obj.set_surround_rect(perc=100)
        equal_rect = gameutils.copy_rect(obj.surround_rect)
        self.assertTrue(obj.surround_rect.size == equal_rect.size)
        self.assertTrue(obj.rect.size == old_rect.size)
        self.assertTrue(obj.rect == old_rect)
        # test errors on invalid args
        self.assertRaises(TypeError, obj.set_surround_rect, perc=100, length=2)
        self.assertRaises(TypeError, obj.set_surround_rect, length=2, perc=100)
        self.assertRaises(TypeError, obj.set_surround_rect, 100, perc=100)
        self.assertRaises(TypeError, obj.set_surround_rect, 2, length=100)
        self.assertRaises(TypeError, obj.set_surround_rect, 100, 2)
        # test difference after set (both perc and pixels) and set_rect_attrs
        obj = gameObjects.GenericGameObject(pygame.Surface((10,10)))
        _size = obj.rect.size
        _center = obj.rect.center
        original_attrs = ({'size':_size}, {'center':_center})
        _new_size = tuple(map(sum, zip(_size, (-12, 22))))
        _new_center = tuple(map(sum, zip(_center, (12, -2))))
        new_attrs = ({'size':_new_size}, {'center':_new_center})
        original_surround_rect = gameutils.copy_rect(obj.surround_rect)
        original_rect = gameutils.copy_rect(obj.rect)
        original_area = obj.area
        for attr in new_attrs:
            obj.set_rect_attrs(attr)
        self.assertFalse(original_surround_rect == obj.surround_rect)
        self.assertFalse(original_rect == obj.rect)
        self.assertFalse(original_area == obj.area)
        for attr in original_attrs:
            obj.set_rect_attrs(attr)
        self.assertTrue(original_surround_rect == obj.surround_rect,
                        "SURROUND RECT CHANGED: %s -> %s"
                        % (original_surround_rect, obj.surround_rect))
        self.assertTrue(original_rect == obj.rect,
                        "RECT CHANGED: %s -> %s" % (original_rect, obj.rect))
        self.assertTrue(original_area == obj.area,
                        "AREA CHANGED: %s -> %s" % (original_area, obj.area))
        # using an iterable
        original_surround_rect = gameutils.copy_rect(obj.surround_rect)
        original_rect = gameutils.copy_rect(obj.rect)
        original_area = obj.area
        left, top, width, height = gameutils.copy_rect(obj)
        obj.set_rect_attrs(((k, v+4) for k, v in zip(
            ('left', 'top', 'width', 'height'),(left, top, width, height))))
        self.assertFalse(original_surround_rect == obj.surround_rect)
        self.assertFalse(original_rect == obj.rect)
        self.assertFalse(original_area == obj.area)
        obj.set_rect_attrs(list((k, v) for k, v in zip(
            ('left', 'top', 'width', 'height'),(left, top, width, height))))
        self.assertTrue(original_surround_rect == obj.surround_rect,
                        "SURROUND RECT CHANGED: %s -> %s"
                        % (original_surround_rect, obj.surround_rect))
        self.assertTrue(original_rect == obj.rect,
                        "RECT CHANGED: %s -> %s" % (original_rect, obj.rect))
        self.assertTrue(original_area == obj.area,
                        "AREA CHANGED: %s -> %s" % (original_area, obj.area))
        for dim in ((random.randint(0, maxX),
                     random.randint(0, maxY)) for i in range(100)):
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            for change in it_.chain(range(-2, 0), range(1, 2)):
                obj.set_surround_rect(perc=change)
                new_sperc_rect = gameutils.copy_rect(obj.surround_rect)
                try:
                    self.assertTrue(obj.rect.size != new_sperc_rect.size,
                                    "[PERC] dim: %s | change: %d | %s, %s"
                                        % (dim, change,obj.rect, new_sperc_rect))
                except AssertionError:
                    w, h = new_sperc_rect.size
                    diff = max(obj.area, w * h) - min(obj.area, w * h)
                    self.assertTrue(diff <= abs(change))
                obj.set_surround_rect(length=change)
                new_spixel_rect = gameutils.copy_rect(obj.surround_rect)
                self.assertTrue(obj.rect.size != new_spixel_rect.size,
                                "[PIXEL] dim: %s | change: %d | %s, %s"
                                    % (dim, change,obj.rect, new_sperc_rect))
        # other tests for surround_rect
        for dim in ((random.randint(0, maxX),
                     random.randint(0, maxY)) for i in range(100)):
            obj = gameObjects.GenericGameObject(pygame.Surface(dim))
            for perc in range(-10, 120):
                obj.set_surround_rect(perc=perc)
                old_srect = obj.surround_rect
                old_rect = obj.rect
                x, y = tuple(random.randint(0, 200) for i in 'xy')
                obj.move(x, y)
                nsr = old_srect.move(x, y)
                nsr.center = obj.rect.center
                self.assertTrue(nsr.size == old_srect.size == obj.surround_rect.size)
                self.assertTrue(nsr == obj.surround_rect)

    def testActions(self):
        obj = gameObjects.GenericGameObject(pygame.Surface((100,100)))
        obj.set_action(obj.move, (2, 2,), group='r')
        obj.set_action(obj.move, (-2, -2,), group='s')
        start_topleft = topleft = obj.rect.topleft
        for i in range(10):
            obj.raise_actions('r')
            topleft = tuple(map(sum, zip(topleft, (2,2))))
            self.assertTrue(obj.rect.topleft == topleft)
        for i in range(10):
            obj.raise_actions('s')
            topleft = tuple(map(sum, zip(topleft, (-2,-2))))
            self.assertTrue(obj.rect.topleft == topleft)
        self.assertTrue(start_topleft == topleft)
        group_r = [(obj.move, (2, 2,), {})]
        group_s = [(obj.move, (-2, -2,), {})]
        for actions, group in zip((group_r, group_s), ('r', 's')):
            self.assertTrue(obj.del_action_group(group) == actions)
            self.assertFalse(obj.del_action_group(group) == actions)
            self.assertTrue(obj.del_action_group(group) == None)

    def testProperty(self):
        # test compare
        for val1, val2 in zip((1, True, False, 4, 6, "ciao", "test"),
                              (2, False, None, [], "s", "ciao2", "2test")):
            obj1 = gameObjects.GenericGameObject(pygame.Surface((100,100)), val1)
            obj2 = gameObjects.GenericGameObject(pygame.Surface((100,100)), val2)
            self.assertFalse(obj1 == obj2)
            self.assertTrue(obj1.compare_value != obj2.compare_value)
            self.assertFalse(obj1.compare_value == obj2.compare_value)
            obj1.compare_value = obj2.compare_value
            self.assertFalse(obj1.compare_value != obj2.compare_value)
            self.assertTrue(obj1.compare_value == obj2.compare_value)
        buttons = []
        for b in range(10):
            buttons.append(gameObjects.GenericGameObject(cmp_value=b))
        for b in range(10):
            self.assertTrue(buttons[b].compare_value == b,
                "compare_value is: %s %s (should be %s instead)"
                % (buttons[b].compare_value, type(buttons[b].compare_value), b))
            self.assertTrue(buttons[b] == b,
                "compare_value is: %s %s (should be %s instead)"
                % (buttons[b].compare_value, type(buttons[b].compare_value), b))
        # test area
        for m in range(2, 20):
            def reassign_area(game_object, new_area):
                game_object.area = new_area
            obj = gameObjects.GenericGameObject(pygame.Surface((100,100)))
            area = obj.area
            w, h = obj.rect.w, obj.rect.h
            self.assertTrue(obj.area == w * h)
            self.assertRaises(AttributeError, reassign_area, obj, m)
            obj.resize(w*m, h*m)
            self.assertFalse(obj.area == area)


class TestGenericGameObjectOnPaint(unittest.TestCase):
    def setUp(self):
        self.bg_color = (0,0,0,255)
        self.obj_color = (255,255,255,255)
        self.fake_surface = pygame.Surface((200, 200))
        self.fake_color = (100,25,200,255)
        self.fake_surface.fill(self.fake_color)
        SCREEN.fill(self.bg_color)

    @staticmethod
    def build_color ():
        _r = random.randint
        while True:
            yield (_r(1, 255),_r(1, 255),_r(1, 255), 255)

    def testDrawAndErase(self):
        _r = random.randint
        obj = gameObjects.GenericGameObject(pygame.Surface((100,100)))
        obj.surface.fill(self.obj_color)
        w, h = obj.rect.size
        for i in range(obj.area/2):
            coord = _r(1, w-1), _r(1, h-1)
            self.assertFalse(obj.surface.get_at(coord) == SCREEN.get_at(coord))
        obj.draw_on(SCREEN)
        for i in range(obj.area/2):
            coord = _r(1, w-1), _r(1, h-1)
            self.assertTrue(obj.surface.get_at(coord) == SCREEN.get_at(coord))
        obj.erase(SCREEN, self.fake_surface)
        for i in range(obj.area/2):
            coord = _r(1, w-1), _r(1, h-1)
            self.assertFalse(obj.surface.get_at(coord) == SCREEN.get_at(coord))
            self.assertTrue(self.fake_surface.get_at(coord) == SCREEN.get_at(coord))
        # implicit erase
        obj = gameObjects.GenericGameObject(pygame.Surface((100,100)))
        obj.surface.fill(self.obj_color)
        w, h = obj.rect.size
        surface =  gameutils.get_portion(SCREEN, obj.rect)
        obj.draw_on(SCREEN)
        for i in range(obj.area/2):
            coord = _r(1, w-1), _r(1, h-1)
            self.assertEqual(obj.surface.get_at(coord), SCREEN.get_at(coord))
            self.assertNotEqual(obj.surface.get_at(coord), surface.get_at(coord))
        obj.erase(SCREEN)
        for i in range(obj.area/2):
            coord = _r(1, w-1), _r(1, h-1)
            self.assertNotEqual(obj.surface.get_at(coord), SCREEN.get_at(coord))
            self.assertEqual(surface.get_at(coord), SCREEN.get_at(coord))
        # more tests
        obj = gameObjects.GenericGameObject(pygame.Surface((100,100)))
        obj.velocity = (10, 10)
        scr_rect = SCREEN.get_rect()
        bounce_rect = pygame.Rect(0,0,scr_rect.w/2, scr_rect.h/2)
        bounce_rect.center = scr_rect.center
        w, h = obj.rect.size
        SCREEN.fill(self.bg_color)
        self.fake_surface.fill(self.bg_color)
        for r, color in zip(range(800), self.build_color()):
            obj.move_bouncing(bounce_rect)
            obj.surface.fill(color)
            obj.draw_on(SCREEN)
            coord = _r(0, w-1), _r(0, h-1)
            scr_position = tuple(map(sum, zip(obj.rect.topleft, coord)))
            self.assertTrue(SCREEN.get_at(scr_position) == color)
            self.assertTrue(obj.surface.get_at(coord) == color)
            obj.erase(SCREEN, self.fake_surface)
            self.assertTrue(SCREEN.get_at(scr_position)
                            == self.fake_surface.get_at(coord)
                            == self.bg_color)


class TestImageObject(unittest.TestCase):
    def setUp(self):
        self.images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(IMAGES_PATH), '*')))

    def testLoadImage(self):
        objects_1 = []
        objects_2 = []
        for path in self.images_path:
            val = op_.split(path)[-1]
            objects_1.append(gameObjects.Image(path, val))
            objects_2.append(gameObjects.Image(path, val))
        for obj1, obj2 in zip (objects_1, objects_2):
            self.assertTrue(obj1 == obj2, "%s, %s"% (obj1.compare_value, obj2.compare_value))
            self.assertTrue(obj1.rect == obj2.rect)
            self.assertTrue(obj1.surface.get_size() == obj2.surface.get_size())
            self.assertTrue(obj1.area == obj2.area)
            self.assertTrue(pygame.image.tostring(obj1.surface, "RGB")
                            == pygame.image.tostring(obj2.surface, "RGB"))
            for attr in ('get_flags', 'get_bitsize', 'get_bytesize',
                         'get_pitch', 'get_masks', 'get_shifts', 'get_losses'):
                self.assertTrue(getattr(obj1.surface, attr)() == getattr(obj2.surface, attr)(),
                    "%s, %s" % (getattr(obj1.surface, attr)(), getattr(obj2.surface, attr)()))

    def testLoadFromPath(self):
        objects_1 = []
        objects_2 = []
        for pos, path in enumerate(self.images_path):
            cmpvalue = op_.split(path)[-1]
            objects_1.append(gameObjects.Image(path, cmpvalue))
            objects_2.append(gameObjects.Image(path, cmpvalue))
            self.assertTrue(objects_1[pos].compare_value == cmpvalue)
            self.assertTrue(objects_2[pos].compare_value == cmpvalue)
        for obj1, obj2 in zip (objects_1, objects_2):
            self.assertTrue(obj1 == obj2)
            self.assertTrue(obj1.rect == obj2.rect)
            self.assertTrue(obj1.area == obj2.area)
            self.assertTrue(obj1.surface.get_size() == obj2.surface.get_size())

    def testLoadFromSurface(self):
        objects_1 = list(gameObjects.Image(b, op_.split(b)[-1])
            for b in self.images_path)
        objects_2 = []
        for b in objects_1:
            objects_2.append(gameObjects.GenericGameObject(b.surface, b.compare_value))
        for obj1, obj2 in zip (objects_1, objects_2):
            self.assertTrue(obj1 == obj2)
            self.assertTrue(obj1.rect == obj2.rect)
            self.assertTrue(obj1.area == obj2.area)
            self.assertTrue(pygame.image.tostring(obj1.surface, "RGB")
                            == pygame.image.tostring(obj2.surface, "RGB"))


class TestTextImageObject(unittest.TestCase):
    def setUp(self):
        self.images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(FONTS_PATH), '*')))

    def testInvalidArgs(self):
        _r = random.randint
        text_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
        bg_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
        font = pygame.font.Font(self.images_path.pop(), 10)

    def testLoadAndResize(self):
        _r = random.randint
        text = "jnOJojOjOJ"
        for size in range(5, 50):
            for font_path in self.images_path:
                text_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
                bg_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
                font = pygame.font.Font(font_path, size)
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
                for i in range(0, 4):
                    if i:
                        w, h = tuple(_r(size, size*2*i) for x in 'hw')
                        obj1.resize(w,h)
                        obj2.resize(w,h)
                    self.assertEqual(obj1, obj2)                    
                    self.assertEqual(obj1.rect, obj2.rect)
                    self.assertEqual(obj1.area, obj2.area)
                    self.assertEqual(pygame.image.tostring(obj1.surface, "RGB"),
                                     pygame.image.tostring(obj2.surface, "RGB"))

    def testMovement(self):
        _r = random.randint
        text = "jnOJojOjOJ"
        mtb = []
        for size in range(5, 50):
            for font_path in self.images_path:
                text_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
                bg_color = (_r(0, 255),_r(0, 255),_r(0, 255), 255)
                mtb.append(gameObjects.TextImage(
                    text, _DEF_FONT, _DEF_FONT_SIZE, text_color, bg_color))
        for b in mtb:
            center = b.rect.center
            b.move(_r(2,33), _r(5,55))
            self.assertNotEqual(center, b.rect.center)
            b.goto_start()
            self.assertEqual(center, b.rect.center)
        for attr in ('topleft', 'bottomright', 'left', 'midtop'):
            for b in mtb:
                b.update_start_position(attr)
                pos = getattr(b.rect, attr)
                b.move(_r(2,33), _r(5,55))
                self.assertNotEqual(pos, getattr(b.rect, attr))
                b.goto_start()
                self.assertEqual(pos, getattr(b.rect, attr))

            
class TestCellObject(unittest.TestCase):
    def setUp(self):
        self.images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(IMAGES_PATH), '*')))

    def testDrawAndAdd(self):
        SCREEN = pygame.display.set_mode((640,480))
        pygame.display.iconify()
        obj_color = (0,0,0,255)
        item_color = (255,255,111,255)
        obj = gameObjects.Cell(self.images_path.pop())
        obj.surface.fill(obj_color)
        item = gameObjects.Image(self.images_path.pop())
        item.resize(*obj.rect.size)
        item.surface.fill(item_color)
        self.assertTrue(obj.surface.get_at(obj.rect.center) == obj_color)
        self.assertTrue(obj.draw_on(SCREEN) == obj.rect)
        old_center = obj.rect.center
        new_center = tuple(map(sum, zip(old_center, (4, 4))))
        self.assertTrue(obj.draw_on(SCREEN) == obj.rect)
        self.assertTrue(obj.surface.get_at(obj.rect.center) == obj_color)
        obj.rect.center = old_center
        obj.add_item(item, {'center': new_center})
        self.assertFalse(obj.rect.center == obj.item.rect.center)
        self.assertTrue(obj.item.rect.center == new_center)
        obj.add_item(item)
        self.assertTrue(obj.rect.center == obj.item.rect.center)
        obj.draw_on(SCREEN)
        self.assertTrue(obj.surface.get_at(obj.rect.center) == obj_color)
        obj.draw_on(SCREEN, draw_item=True)
        self.assertFalse(obj.surface.get_at(obj.rect.center) == obj_color)
        self.assertTrue(obj.surface.get_at(obj.rect.center) == item_color)
        # more tests
        obj = gameObjects.Cell(pygame.Surface((73,84)))
        item = gameObjects.GenericGameObject(pygame.Surface((12, 14)))
        self.assertFalse(obj.item)
        obj.add_item(item)
        self.assertEqual(obj.rect.center, obj.item.rect.center)
        obj.move_at((200, 50))
        self.assertEqual(obj.rect.center, obj.item.rect.center)
        obj.move(100, 150)
        self.assertEqual(obj.rect.center, obj.item.rect.center)
        obj.resize(20, 50)
        self.assertEqual(obj.rect.center, obj.item.rect.center)
        obj.add_item(item, dict((('bottom',None), ('right',None))))
        for attr in ('bottom', 'right'):
            self.assertEqual(getattr(obj.rect, attr),
                             getattr(obj.item.rect, attr))
        obj.add_item(item, (('bottom',None), ('left',None)))
        for attr in ('bottom', 'left'):
            self.assertEqual(getattr(obj.rect, attr),
                             getattr(obj.item.rect, attr))
        obj.add_item(item, (('bottom','top'),))
        self.assertEqual(obj.rect.top, obj.item.rect.bottom)
        obj.add_item(item, (('left','right'),))
        self.assertEqual(obj.rect.right, obj.item.rect.left)
        obj.add_item(item, (('left',0),))
        self.assertEqual(0, obj.item.rect.left)
        obj.add_item(item, (('topleft',(11,3)),))
        self.assertEqual((11,3), obj.item.rect.topleft)
        obj = gameObjects.Cell(pygame.Surface((73,84)))
        item = gameObjects.GenericGameObject(pygame.Surface((12, 14)))
        obj.add_item(item, dict((('bottom',lambda : obj.rect.bottom-2),
                                 ('right', lambda : obj.rect.right-2))))
        for attr in ('bottom', 'right'):
            self.assertEqual(getattr(obj.rect, attr),
                             getattr(obj.item.rect, attr) + 2)
        # test urect
        _r = random.randint
        for i in range(100):
            w, h = tuple(_r(3, 100) for i in 'xy')
            obj = gameObjects.Cell(pygame.Surface((w,h)))
            item = gameObjects.GenericGameObject(pygame.Surface((w, h)))
            obj.add_item(item, {'topleft':'bottomleft'})
            self.assertEqual( gameutils.rect_area(obj.urect), obj.area*2)


class TestGridObject(unittest.TestCase):
    def testDimensions(self):
        _r = random.randint
        for i in range(20):
            h, w = _r(1, 100), _r(1, 100)
            cell_size = _r(8,23), _r(8,23)
            grid = gameObjects.Grid(w, h)
            self.assertTrue(grid.size == (0, 0))
            grid.build(gameObjects.GenericGameObject, cell_size=cell_size)
            self.assertEqual(grid.size, (h*cell_size[0], w*cell_size[1]))
            self.assertEqual(len(grid), h * w)
            self.assertEqual(len(grid.columns), h)
            self.assertEqual(len(grid.rows), w)
            self.assertEqual(grid.n_cols, h)
            self.assertEqual(grid.n_rows, w)
            for cell in grid:
                self.assertEqual(cell.size, cell_size)

    def testItems(self):
        _r = random.randint
        h, w = 12, 17
        grid = gameObjects.Grid(w, h)
        p = 0
        for x in range(w):
            for y in range(h):
                grid[x,y] = p
                p += 1
        # iter
        for i, j in zip(grid, range(h*w)):
            self.assertTrue(i == j)
        coords = ((x, y) for x in range(w) for y in range(h))
        list(coords)
        for gc, cc in zip(grid, coords):
            self.assertEqual(grid.current_coord, cc)
        # item changes
        len_ = len(grid)-1
        for i in range(20):
            c, r = _r(0, h-1), _r(0, w-1)
            c1, r1 = _r(0, h-1), _r(0, w-1)
            x = grid[r,c]
            y = grid[r1,c1]
            grid[r,c], grid[r1,c1] = grid[r1,c1], grid[r,c]
            self.assertTrue(grid[r1,c1] == x and grid[r,c] == y)
        self.assertRaises(KeyError, grid.__getitem__, h*w)
        self.assertRaises(KeyError, grid.__getitem__, (2,1,3,2,3))
        self.assertRaises(KeyError, grid.__getitem__, "2")
        self.assertRaises(KeyError, grid.__getitem__, None)
        self.assertRaises(AttributeError, setattr, grid, 'rows', 9)
        self.assertRaises(AttributeError, setattr, grid, 'columns', 9)


    def testWithGameObjects(self):
        _r = random.randint
        images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(IMAGES_PATH), '*')))
        r, c, cell_size = 3,5, (12,10)
        grid = gameObjects.Grid(r, c)
        self.assertFalse(grid.isfull)
        grid.build(gameObjects.Image, [images_path.pop()], cell_size=cell_size)
        for pos, obj in zip(grid.iter_pos(), grid):
            self.assertTrue(obj.rect.size == cell_size)
            self.assertTrue(obj.rect.width == cell_size[0])
            self.assertTrue(obj.rect.height == cell_size[1])
            self.assertEqual(pygame.image.tostring(grid[pos].surface, "RGB"),
                             pygame.image.tostring(obj.surface, "RGB"))
        self.assertTrue(grid.isfull)
        self.assertEqual(grid.area, c * r * obj.rect.width * obj.rect.height)
        self.assertEqual(grid, grid)
        self.assertEqual(grid, grid.copy())
        # other tests for size & co.
        _new_size = (grid.rect.width / 2,grid.rect.width / 2)
        grid.size = _new_size
        self.assertEqual(grid.size, _new_size)
        for pos, obj in zip(grid.iter_pos(), grid):
            self.assertEqual(obj.rect.size, grid[pos].rect.size)
            self.assertEqual(pygame.image.tostring(grid[pos].surface, "RGB"),
                            pygame.image.tostring(obj.surface, "RGB"))
        self.assertEqual(grid.area, c * r * obj.rect.width * obj.rect.height)
        aRect = pygame.Rect(0,0,grid.rect.width*2,grid.rect.height*2)
        grid.resize_from_rect(aRect)
        self.assertEqual(grid.rect, aRect)
        # test draw
        positions = ['topleft', 'bottomleft', 'topright', 'bottomright',
                     'midtop', 'midleft', 'midbottom', 'midright',
                     'center',]
        bg_color = (0,0,0,255)
        cells_color = (255,255,255,255)
        scr_w, scr_h = SCREEN.get_size()
        SCREEN.fill(bg_color)
        for i in grid:
            i.surface.fill(cells_color)
        for i in range(20):
            self.assertEqual(SCREEN.get_at((_r(0, scr_w-1), _r(0, scr_h-1))),
                             bg_color)
        grid.draw_on(SCREEN)
        for obj in grid:
            self.assertEqual(SCREEN.get_at(obj.rect.center), cells_color)
        # test moving
        movement = [(10,12),(1,0),(0,3),(-2,-2),(-3,7),(20,5),(5,6),(4,7),(9,11)]
        for m in movement:
            old_rects = [gameutils.copy_rect(obj.rect) for obj in grid]
            old_grid_rect = gameutils.copy_rect(grid.rect)
            grid.move(*m)
            self.assertEqual(grid.rect.topleft, tuple(map(sum, zip(old_grid_rect, m))))
            for i, obj in enumerate(grid):
                for p in positions[:4]:
                    old_attr = getattr(old_rects[i], p)
                    new_attr = getattr(obj.rect, p)
                    self.assertEqual(new_attr, tuple(map(sum, zip(old_attr, m))))
        # shuffle
        old = []
        for pos, cell in zip(grid.iter_pos(), grid):
            cell.compare_value = pos
            old.append(pos)
        grid.shuffle()
        new = [cell.compare_value for cell in grid]
        self.assertTrue(any(o != n for o, n in zip(old, new)))

    def testGridCell(self):
        _r = random.randint
        gc = list(gameObjects.GridCell(pygame.Surface((_r(2,14),_r(3,33))), x)
                  for x in range(20))
        for c in gc:
            self.assertTrue(c.covered)
            self.assertRaises(AttributeError, gc.__setattr__, 'covered', 333)
        t = list(_r(0,1) for x in gc)
        for p, x in enumerate(t):
            if x:
                gc[p].toggle()
        for p, x in enumerate(t):
            self.assertEqual(gc[p].covered, bool(not x))


class TestBox (unittest.TestCase):

    def testBasicBox (self):
        box = gameObjects.Box()
        self.assertFalse(box.items())
        for x in range(20):
            args = dict(left=0, top=0, width=0, height=0)
            for k in args:
                args[k] = random.randint(0, 500)
            b = gameObjects.Box(**args)
            r = b.rect
            for k in args:
                self.assertEqual(args[k], getattr(r, k))
            b1 = gameObjects.Box(**args)
            for i in range(x):
                b1.add_item(i)
            self.assertEqual(len(b1.items()), x)

    def testVHbox(self):
        self.images_path = filter(op_.isfile,
            glob.glob(op_.join(op_.realpath(IMAGES_PATH), '*')))
        vbox = gameObjects.Vbox()
        hbox = gameObjects.Hbox()
        for path in self.images_path: 
            hbox.add_item(gameObjects.Image(path))
            vbox.add_item(gameObjects.Image(path))
        self.assertEqual(len(vbox.items()), len(self.images_path))
        self.assertEqual(len(hbox.items()), len(self.images_path))
        for vitem, hitem in zip(vbox.items(), hbox.items()):
            self.assertTrue(vbox.rect.contains(vitem.rect))
            self.assertTrue(hbox.rect.contains(hitem.rect))
        w, h = SCREEN.get_size()
        rects = tuple(pygame.Rect(0, 0, w/i, h/i) for i in range(1, 5))
        for rect in rects:
            vbox.resize(*rect.size)
            hbox.resize(*rect.size)
            for vitem, hitem in zip(vbox.items(), hbox.items()):
                self.assertTrue(vbox.rect.contains(vitem.rect))
                self.assertTrue(hbox.rect.contains(hitem.rect))
                rect.topleft = vbox.rect.topleft
                self.assertTrue(rect.contains(vitem.rect))
                rect.topleft = hbox.rect.topleft
                self.assertTrue(rect.contains(hitem.rect))




def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestGenericGameObject, TestGenericGameObjectOnPaint,
                  TestImageObject, TestTextImageObject,
                  TestCellObject, TestGridObject, TestBox)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)



if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
