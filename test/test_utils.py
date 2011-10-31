#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010  Marco Chieppa (aka crap0101)
# See the file COPYING.txt in the root directory of this package.


import os
import re
import sys
import glob
import random
import string
import operator
import os.path as op_
import itertools as it_
import pygame
from pygame.locals import *
from collections import defaultdict
import unittest

pwd = op_.dirname(op_.realpath(__file__))

try:
    import bumpo
except ImportError:
    bumpopackdir = op_.join(op_.split(pwd)[0])
    sys.path.insert(0, bumpopackdir)

from bumpo import gameObjects
from bumpo import gameutils


pygame.init()

display_info = pygame.display.Info()
MAX_X = display_info.current_w / 3
MAX_Y = display_info.current_h / 3


BASE_PATH = 'data'
CONFIG_FILE_PATH = op_.join(BASE_PATH, 'config')
FONTS_PATH = op_.join(BASE_PATH, 'fonts')
IMAGES_PATH = op_.join(BASE_PATH, 'images')
SOUNDS_PATH = op_.join(BASE_PATH, 'sounds')

_DEF_FONT_NAME = 'FreeSans.otf'
_DEF_FONT = op_.join(FONTS_PATH, _DEF_FONT_NAME)
_DEF_FONT_SIZE = 20


def get_screen(x=None, y=None, iconify=True):
    screen = pygame.display.set_mode((MAX_X if x is None else x,
                             MAX_Y if y is None else y))
    pygame.display.iconify() if iconify else True 
    return screen


class TestImages(unittest.TestCase):

    def testDrawAndDelete(self):
        _r = random.randint
        screen = get_screen(MAX_X, MAX_Y)
        scr_rect = screen.get_rect()
        w, h = scr_rect.size
        bg_color = (0,0,0,255)
        background = pygame.Surface((w, h))
        background.fill(bg_color)
        original_background = background.copy()
        # test draw
        for i in range(500):
            point = (_r(0, w-1), _r(0, h-1))
            self.assertEqual(screen.get_at(point), background.get_at(point))
        # test delete objects
        positions = (['center', (0,0)], ['bottomleft', (1,-1)],
                     ['topright', (-1,1)], ['midtop', (0,1)],
                     ['midleft', (1,0)], ['midbottom', (0,-1)],
                     ['midright', (-1,0)], ['center', (0,0)])
        colors = list((_r(10, 255),_r(10, 255),_r(10, 255),255) for c in range(20))
        surfaces = list(pygame.Surface((10, 10)) for s in range(20))
        objects = list(gameObjects.GenericGameObject(s) for s in surfaces)
        bounce_rect = screen.get_rect()
        for obj, color in zip(objects, colors):
            obj.surface.fill(color)
            obj.move_random(bounce_rect)
            obj.move_random(bounce_rect)
            obj.move_random(bounce_rect)
            obj.draw_on(screen)
        for i in range(50):
            for obj in objects:
                for position, delta in positions:
                    point = map(sum, zip(getattr(obj.rect, position), delta))
                    self.assertTrue(obj.rect.collidepoint(point))
                    self.assertNotEqual(screen.get_at(point),
                                        original_background.get_at(point))


            
class TestRects(unittest.TestCase):

    def testUpdateRects(self):
        screen = get_screen(MAX_X, MAX_Y)
        scr_color = (0,0,0,255)
        obj_color = (255,255,255,255)
        surf_size = (2 * screen.get_size()[0] / 100,
                     2 * screen.get_size()[0] / 100)
        screen_rect = screen.get_rect()
        objects = [gameObjects.GenericGameObject(pygame.Surface(surf_size))
                    for i in range(10)]
        for obj in objects:
            obj.move_random(screen_rect)
            screen.fill(obj_color, obj.rect)
        for obj in objects:
            screen.fill(scr_color, obj.rect)
            self.assertTrue(screen.get_at(obj.rect.center) == scr_color)

    def testCopyRect(self):
        _r = random.randint
        attrs = ['top', 'left', 'bottom', 'right', 'topleft',
                 'bottomleft', 'topright', 'bottomright', 'midtop',
                 'midleft', 'midbottom', 'midright', 'center', 'centerx',
                 'centery', 'size', 'width', 'height', 'w', 'h']
        for i in range(200):
            w, h = _r(0, 1000), _r(0, 1000)
            top, left = _r(0, 100), _r(0, 100)
            orig_rect = pygame.Rect(top,left,w,h)
            new_rect = gameutils.copy_rect(orig_rect)
            for attr in attrs:
                self.assertEqual(getattr(orig_rect, attr), getattr(new_rect, attr))

    def testAreas(self):
        _r = random.randint
        for i in range(200):
            w, h = _r(0, 1000), _r(0, 1000)
            self.assertEqual(gameutils.rect_area(pygame.Rect(0,0,w,h)), w * h)
            w, h = _r(0, 1000), _r(0, 1000)
            self.assertEqual(gameutils.surface_area(pygame.Surface((w,h))), w * h)

    def testScale(self):
        def frange(start, stop, step):
            while start < stop:
                yield start
                start += step
        for i in range(200):
            size = tuple(random.randint(10, 1000) for dim in 'wh')
            r = pygame.Rect((0,0), size)
            area = gameutils.rect_area(r)
            for factor in frange(-55, 55, 3.5):
                scaled = gameutils.scale_rect(r, factor)
                self.assertEqual(scaled.w, int(r.w*factor))
                self.assertEqual(scaled.h, int(r.h*factor))
        for n in range(2, 10):
            w, h = tuple(random.randint(10, 1000) for dim in 'wh')
            r = pygame.Rect(0,0, w, h)
            new_r = gameutils.scale_rect_at_length(r, n, 'w')
            self.assertEqual(n, new_r.w)
            self.assertEqual(int(r.h*new_r.w/r.w), new_r.h)


    def testRectResize(self):
        _r = random.randint
        positions = ('center', 'midtop', 'topleft', 'bottomright')
        for i in range(200):
            for pos in positions:
                w, h = _r(10, 1000), _r(10, 1000)
                top, left = _r(0, 1000), _r(0, 1000)
                perc = _r(10, 90)
                rect = pygame.Rect(left, top, w, h)
                new_rect = gameutils.resize_rect_by_perc(rect, perc, pos)
                self.assertTrue(rect.contains(new_rect), "%s,%s"%(rect,new_rect))
                gameutils.resize_rect_by_perc_ip(rect, perc, pos)
                self.assertEqual(rect, new_rect)

    def testRectsAndObjectsCollide(self):
        scr = get_screen(640, 480)
        objects = list(gameObjects.GenericGameObject(pygame.Surface((10,20))) for i in range(9))
        for pos, o in enumerate(objects):
            o.set_surround_rect(perc=120)
            for attr in ('rect', 'surround_rect'):
                self.assertTrue(gameutils.gobj_collide_at(objects, pos, attr))
        scr_rect = scr.get_rect()
        rects = list(o.rect for o in objects)
        rects, pos = gameutils.distribute_rects(rects, scr_rect, 20)
        self.assertEqual(pos, len(objects))
        for o, r in zip(objects, rects):
            o.move_at(r.center, 'center')
        for pos, o in enumerate(objects):
            for attr in ('rect', 'surround_rect'):
                self.assertFalse(gameutils.gobj_collide_at(objects, pos, attr))
        for i in range(1,6):
            rects = [pygame.Rect(0,0,2,3) for x in range(i)]
            rects.append(pygame.Rect(5,5,5,5))
            rects.extend([pygame.Rect(7,7, 6,6) for x in range(i)])
            collisions = gameutils.rects_collide_at(rects, i)
            self.assertEqual(len(collisions), i)
            for c in collisions:
                self.assertTrue(c > i)
            rects = [pygame.Rect(5,5,2,3) for x in range(i)]
            rects.append(pygame.Rect(4,2,5,5))
            rects.extend([pygame.Rect(17,17, 6,6) for x in range(i)])
            collisions = gameutils.rects_collide_at(rects, i)
            self.assertEqual(len(collisions), i)
            for c in collisions:
                self.assertTrue(c < i)
        rects = [pygame.Rect(x*4,x*4,2,3) for x in range(5)]
        for i in range(len(rects)):
            self.assertFalse(gameutils.rects_collide_at(rects, i))

    def testDistributeRects(self):
        _r = random.randint
        screen = get_screen(800, 600)
        scr_rect = screen.get_rect()
        w, h = 30, 30
        for i in range(200):
            rects = list(pygame.Rect(0, 0, _r(1, w), _r(1, h)) for i in range(_r(2, 10)))
            pad = i%10
            rects, pos = gameutils.distribute_rects(rects, scr_rect, pad)
            for n, r in enumerate(rects):
                self.assertFalse(r.collidelistall(rects[:n]+rects[n+1:]))
        #fail
        scr_rect = pygame.Rect(10,10, 100,100)
        for i in range(500):
            rects = list(pygame.Rect(0, 0, _r(11, 51), _r(11, 51)) for i in range(_r(10, 20)))
            pad = i%13
            rects, pos = gameutils.distribute_rects(rects, scr_rect, pad)
            self.assertNotEqual(pos, len(rects))

    def testCmpRectsAndObjects(self):
        _r = random.randint
        rect_attrs = ('width', 'height', 'size')
        rect_types = ('rect', 'surround_rect', 'urect')
        for i in range(200):
            le_ = (((_r(0, 10), _r(0, 10)), (_r(11, 20), _r(11, 20))) for l in range(100))
            eq_ = (((e, e*2), (e, e*2)) for e in range(100))
            gt_ = (((_r(30, 50), _r(30, 50)), (_r(1, 20), _r(1, 20))) for l in range(100))
            for le, eq, gt in zip(le_, eq_, gt_):
                for comp, retval in zip((le, eq, gt), [-1,0,1]):
                    dim1, dim2 = comp
                    topleft1 = (_r(0, 100), _r(0, 100))
                    topleft2 = (_r(0, 100), _r(0, 100))
                    rect1 = pygame.Rect(topleft1, dim1)
                    rect2 = pygame.Rect(topleft2, dim2)
                    obj1 = gameObjects.GenericGameObject(pygame.Surface(rect1.size))
                    obj2 = gameObjects.GenericGameObject(pygame.Surface(rect2.size))
                    # for xrect
                    xobj1 = gameObjects.Cell(pygame.Surface(rect1.size))
                    xobj2 = gameObjects.Cell(pygame.Surface(rect2.size))
                    xobj1.add_item(gameObjects.GenericGameObject(pygame.Surface(rect1.size)),
                                   {'topleft':'bottomleft'})
                    xobj2.add_item(gameObjects.GenericGameObject(pygame.Surface(rect2.size)),
                                   {'topleft':'bottomleft'})
                    self.assertEqual(gameutils.cmp_rects_area(rect1, rect2), retval)
                    for delta, rect_type in enumerate(rect_types):
                        # rects
                        self.assertEqual(gameutils.cmp_rects_attrs(
                            rect1, rect2, rect_attrs, delta), retval)
                        self.assertEqual(gameutils.cmp_rects_attrs(
                            rect1, rect2, rect_attrs[:delta+1]), retval)


class TestSurfacesAndColors(unittest.TestCase):

    def testGetPortion(self):
        screen = get_screen(600, 400)
        screen.fill(pygame.Color('pink'))
        for img in glob.glob(op_.join(IMAGES_PATH, '*.[pg][ni][gf]')):
            self.assertTrue(
                isinstance(gameutils.surface_from_file(img), pygame.Surface))
        img_path = op_.join(IMAGES_PATH, 'elements', 'megafono.svg')
        # test get_portion and draw_on / erase
        img = gameObjects.Image(img_path)
        portion_pink = gameutils.get_portion(screen, img.rect)
        self.assertEqual(portion_pink.get_rect().size, img.rect.size)
        img.draw_on(screen)
        portion_x = gameutils.get_portion(screen, img.rect)
        self.assertEqual(portion_x.get_rect().size, img.rect.size)
        self.assertEqual(
            pygame.surfarray.pixels2d(portion_pink).flatten().tolist(),
            pygame.surfarray.pixels2d(portion_pink).flatten().tolist())
        self.assertNotEqual(
            pygame.surfarray.pixels2d(portion_pink).flatten().tolist(),
            pygame.surfarray.pixels2d(portion_x).flatten().tolist())
        img.erase(screen)
        portion2 = gameutils.get_portion(screen, img.rect)
        self.assertEqual(portion2.get_rect().size, img.rect.size)
        for x in range(img.rect.w):
            for y in range(img.rect.h):
                self.assertEqual(portion_pink.get_at((x,y)), portion2.get_at((x,y)))
        self.assertEqual(
            pygame.surfarray.pixels2d(portion_pink).flatten().tolist(),
            pygame.surfarray.pixels2d(portion2).flatten().tolist())
        # other test, draw_on and gameutils.get_portion
        img.draw_on(screen)
        portion_x = gameutils.get_portion(screen, img.rect)
        img.rect.topleft = screen.get_rect().center
        screen.blit(portion_x, img.rect)
        portion_y = gameutils.get_portion(screen, img.rect)
        for x in range(img.rect.w):
            for y in range(img.rect.h):
                self.assertEqual(portion_x.get_at((x,y)), portion_y.get_at((x,y)))

    def test_grayscale (self):
        def t(surf):
            return pygame.image.tostring(surf, 'RGBA')
        def build_fill_surf (w, h, color):
            surf = pygame.Surface(((w, h)))
            surf.fill(color)
            return surf
        w, h = 300, 300
        colors = ('green', 'red', 'blue', 'yellow')
        surfaces = list(build_fill_surf(w, h, pygame.Color(c)) for c in colors)
        for surf in surfaces:
            for color in colors:
                w_points = list(random.randint(0, w-1) for i in range(w/2))
                h_points = list(random.randint(0, h-1) for i in range(h/2))
                for x, y in zip(w_points, h_points):
                    surf.set_at((x,y), pygame.Color(color))
        images = list(gameObjects.GenericGameObject(s) for s in surfaces)
        for img in images:
            surf = img.surface.copy()
            # grayscale
            gray = gameutils.grayscale(img.surface)
            self.assertNotEqual(t(img.surface), t(gray), "ERR0")
            self.assertEqual(t(img.surface), t(img._original_surface), "ERR1")
            for x, y in zip(w_points, h_points):
                self.assertNotEqual(img.surface.get_at((x,y)), gray.get_at((x,y)), "ERR PIX1")
            # grayscale_ip
            gameutils.grayscale_ip(img.surface)
            self.assertNotEqual(t(img.surface), t(img._original_surface), "ERR2")
            self.assertEqual(t(img.surface), t(gray), "ERR3")
            for x, y in zip(w_points, h_points):
                self.assertEqual(img.surface.get_at((x,y)), gray.get_at((x,y)), "ERR PIX2")

    def test_average (self):
        colors = {'green':0, 'red':0, 'blue':0, 'yellow':0, 'white':0, 'black':0}
        for c in colors:
            colors[c] = pygame.Color(c)
        surfaces = [pygame.Surface((10,10)) for _ in colors]
        for surface, color in zip(surfaces, colors):
            surface.fill(colors[color])
        for surface in surfaces:
            ac = gameutils.average_color(surface)
            self.assertTrue(isinstance(ac, pygame.Color))
            self.assertEqual(ac, surface.get_at((0,0)))

    def test_distance (self):
        colors = {'green':0, 'red':0, 'blue':0, 'yellow':0, 'white':0, 'black':0}
        for c in colors:
            colors[c] = pygame.Color(c)
        for c in colors.values():
            self.assertEqual(int(gameutils.edistance(c, c)), 0)


class TestSVG(unittest.TestCase):

    def testFromSVG(self):
        screen = get_screen(600, 400)
        screen.fill(pygame.Color('pink'))
        svg_images = glob.glob(op_.join(IMAGES_PATH, '*.svg'))
        for img_path in svg_images:
            img = gameObjects.Image(img_path)
            size = img.rect.size
            new_size = tuple(dim*11 for dim in size)
            img.resize(*new_size)
            self.assertEqual(new_size, img.rect.size)
            self.assertEqual(new_size, img.surface.get_rect().size)
            self.assertTrue(img.from_svg)

    def testIsSVG(self):
        svg_images = glob.glob(op_.join(IMAGES_PATH, '*.svg'))
        for img in svg_images:
            self.assertTrue(gameutils.is_svg(img))
        other_images = set(svg_images).symmetric_difference(
            glob.glob(op_.join(IMAGES_PATH, '*')))
        for img in filter(op_.isfile, other_images):
            self.assertFalse(gameutils.is_svg(img))

    def testSurfaceFromSVG(self):
        svg_images = glob.glob(op_.join(IMAGES_PATH, '*.svg'))
        for img in svg_images:
            surface = gameutils.surface_from_svg(img)
            self.assertTrue(isinstance(surface, pygame.Surface))

    def testImgBuffer(self):
        for i in range(10):
            s = list(string.letters)
            n = list(map(str, range(100)))
            buf = gameutils.ImgBuffer()
            data = []
            for r in range(random.randint(4, 21)):
                random.shuffle(s)
                random.shuffle(n)
                data.extend(s)
                data.extend(n)
                buf(''.join(s))
                buf(''.join(n))
            self.assertEqual(''.join(data), buf.get_data())


class TestMisc(unittest.TestCase):

    def testFindDiv(self):
        for i in range(200):
            self.assertTrue(operator.mul(*gameutils.finddiv(i)) >= i)

    def testGetAttrs(self):
        rect_attrs_ok = [('topleft', 'x', 'y', 'w', 'bottomright', 'width'),
                         ('height', 'midtop', 'center', 'centerx'),]
        rect_attrs_ko = ('bar', 'foo', 'baz', 'spam')
        surf_attrs_ok = [('get_flags', 'get_height', 'get_rect', 'subsurface'),
                         ('get_clip', 'get_colorkey', 'get_flags', 'set_alpha'),]
        surf_attrs_ko = rect_attrs_ko[:]
        rect = pygame.Rect(2,3,5,7)
        surf = pygame.Surface((11,13))
        # rect
        for attrs in rect_attrs_ok:
            ret_dict = gameutils.get_attrs_from(attrs, rect)
            self.assertEqual(set(attrs), set(ret_dict)) 
            for ret_attr, ret_value in ret_dict.items():
                self.assertEqual(ret_value, getattr(rect, ret_attr))
            err_attr = list(attrs[:]) + ['xx', 'yy']
            ret_dict = gameutils.get_attrs_from(attrs, rect, False)
            self.assertEqual(set(attrs), set(ret_dict))
        for attrs in rect_attrs_ko:
            self.assertRaises(AttributeError, gameutils.get_attrs_from, attrs, rect)
            self.assertFalse(gameutils.get_attrs_from(attrs, rect, False))
        # surface
        for attrs in surf_attrs_ok:
            surf_dict = gameutils.get_attrs_from(attrs, surf)
            self.assertEqual(set(attrs), set(surf_dict))
            for surf_attr, surf_value in surf_dict.items():
                self.assertEqual(surf_value, getattr(surf, surf_attr))
            err_attr = list(attrs[:]) + ['xx', 'yy']
            surf_dict = gameutils.get_attrs_from(attrs, surf, False)
            self.assertEqual(set(attrs), set(surf_dict))
        for attrs in surf_attrs_ko:
            self.assertRaises(AttributeError, gameutils.get_attrs_from, attrs, surf)
            self.assertFalse(gameutils.get_attrs_from(attrs, surf, False))




def load_tests():
    loader = unittest.TestLoader()
    test_cases = (TestImages, TestRects, TestSurfacesAndColors, TestSVG, TestMisc)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)



if __name__ == '__main__':
    os.chdir(pwd)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(load_tests()))
