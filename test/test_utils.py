#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010-2024  Marco Chieppa (aka crap0101)
# See the file COPYING.txt in the root directory of this package.


# std imports
from collections import defaultdict
try:
    import exceptions
except ImportError:
    import builtins as exceptions
import glob
import itertools as it
import operator
import os
import os.path as op_
import random
from random import choice
import re
import string
import shutil
import sys
import tempfile
import unittest
# external imports
import pygame
from pygame.locals import *


pwd = op_.dirname(op_.realpath(__file__))

try:
    import bumpo.plugins
    from bumpo import gameObjects, baseObjects, gameUtils, const
    try:
        from bumpo.plugins import gtkGameObject
        HAVE_GTK = True
    except ImportError:
        HAVE_GTK = False
except ImportError:
    os.chdir(op_.join(op_.split(pwd)[0]))
    sys.path.insert(0, os.getcwd())
    sys.modules['bumpo'] = __import__('src')
    import bumpo.plugins
    from bumpo import gameObjects, baseObjects, gameUtils, const
    try:
        from bumpo.plugins import gtkGameObject
        HAVE_GTK = True
    except ImportError:
        HAVE_GTK = False



BASE_PATH = 'data'
FONTS_PATH = op_.join(BASE_PATH, 'fonts')
IMAGES_PATH = op_.join(BASE_PATH, 'images')

_DEF_FONT_NAME = 'FreeSans.otf'
_DEF_FONT = op_.join(FONTS_PATH, _DEF_FONT_NAME)
_DEF_FONT_SIZE = 20

MAX_X = 100
MAX_Y = 100

def get_screen(x=None, y=None, iconify=True):
    screen = pygame.display.set_mode((MAX_X if x is None else x,
                             MAX_Y if y is None else y))
    if iconify:
        pygame.display.iconify()
    return screen


def get_random_color ():
    return tuple(random.randint(0,255) for _ in 'rgba')


class TestConvert(unittest.TestCase):

    def testConvert (self):
        conv = gameUtils.convert
        r = random.randint
        for i in range(100):
            s = pygame.Surface((r(1,1000), r(1,1000)))
            for a in (True, False):
                obj = baseObjects.Shape(pygame.Surface((10,10)))
                obj.fill(get_random_color())
                res = [conv(s), conv(s,obj), conv(s,obj,a), conv(s,alpha=a)]
                for c in res:
                    self.assertIsInstance(c, pygame.Surface)
                    self.assertEqual(s.get_size(), c.get_size())

    def testConvertShape (self):
        r = random.randint
        surfs = [pygame.Surface((r(1,100),r(1,100))) for _ in range(50)]
        for s in surfs:
            s.fill(get_random_color())
        shapes = [baseObjects.Shape(s) for s in surfs]
        alpha_flags = (0, pygame.RLEACCEL)
        for shape in shapes:
            for alpha in (True, None):
                cshape = shape.copy()
                a = cshape.alpha
                cshape.convert(alpha=alpha)
                self.assertEqual(a,
                                 cshape.alpha,
                                 msg='a:{} ||, cshape.alpha:{}'.format(
                                     a, cshape.alpha))
            for af in alpha_flags:
                af1 = shape.get_alpha_flag()
                shape.set_alpha_flag(af)
                if af != af1:
                    self.assertNotEqual(af1, shape.get_alpha_flag())
                self.assertEqual(af, shape.get_alpha_flag())
        shapes = [baseObjects.Shape(s) for s in surfs]
        # errors
        tes = shapes[0]
        gtko = gtkGameObject.GtkGameObject() if HAVE_GTK else 'EGGS'
        invalid = (1, type('Spam', (), {}), baseObjects.GameObject(),
                   gameObjects.GenericGameObject(), gtko)
        for obj in invalid:
            self.assertRaises(TypeError, tes.convert, obj, msg="XXX:{}".format(obj))
        # from shapes and surfaces
        for shape in shapes:
            shape2 = shape.copy()
            shape2s = shape.copy()
            surf = pygame.Surface((9,9))
            surf.set_alpha(r(10,255))
            obj = baseObjects.Shape(surf)
            shape.convert(obj, alpha=None)
            self.assertEqual(surf.get_alpha(), obj.alpha)
            self.assertEqual(obj.alpha, shape.alpha)
            a = shape2.alpha
            shape2.convert(obj, alpha=None)
            self.assertNotEqual(a, shape2.alpha)
            a = shape2s.alpha
            shape2s.convert(surf, alpha=None)
            self.assertNotEqual(a, shape2s.alpha)

    def testConvertObjects (self):
        r = random.randint
        clsobjs = [baseObjects.GameObject, gameObjects.GenericGameObject]
        if HAVE_GTK:
            clsobjs.append(gtkGameObject.GtkGameObject)
        surfs = [pygame.Surface((r(1,1000),r(1,1000))) for _ in range(100)]
        for c in clsobjs:
            for surf in surfs:
                objs = [surf, baseObjects.Shape(surf)]
                objs.extend(c(surf) for c in clsobjs)
            for o in objs:
                obj = c(surf)
                alpha = r(0,255)
                if isinstance(o, pygame.Surface):
                    o.set_alpha(alpha)
                else:
                    o.alpha = alpha
                obj.convert(o, alpha=None)
                if isinstance(o, pygame.Surface):
                    self.assertEqual(o.get_alpha(), obj.alpha)
                else:
                    self.assertEqual(o.alpha, obj.alpha)


class TestMisc (unittest.TestCase):

    def testDiv (self):
        func = gameUtils.finddiv
        for i in (-1, 0):
            self.assertEqual(func(i), (1,1))
        for i in range(1, int(1e6)):
            self.assertGreaterEqual(operator.mul(*func(i)), i)

    def testTable (self):
        r = random.randint
        c = random.choice
        Table = gameUtils.Table
        E = Table(1,1).empty
        args = []
        for _ in range(50):
            rows, cols = r(1, 100), r(1,100)
            seq1 = [r(-100,100) for _ in range(0, rows*cols + r(10,40))]
            seq2 = [r(-100,100) for _ in range(0, rows*cols - r(1, 10))]
            args.append((rows,cols, c((None, E, "egg")), seq1))
            args.append((rows,cols, c((None, E, "egg")), seq2))
        for a in args:
            rows, cols, empty, seq = a
            table = Table(*a)
            self.assertEquals(table, Table(*a))
            self.assertEquals(table.size, (rows, cols))
            self.assertNotEquals(table, Table(rows+1, cols, seq))
            if seq:
                self.assertNotEquals(table, Table(rows, cols, empty))
            self.assertNotEquals(table, Table(rows, cols-1, empty, seq))
            self.assertEquals(rows, table.n_rows)
            self.assertEquals(cols, table.n_cols)
            self.assertEquals(empty, table.empty)
            self.assertEquals(len(table), rows*cols)
            if len(seq) >= rows*cols:
                self.assertTrue(table.isfull)
                for p, (_, item) in enumerate(table.items()):
                    self.assertEquals(seq[p], item)
                self.assertFalse(table.empty in table)
            else:
                self.assertFalse(table.isfull)
                self.assertTrue(table.empty in table)
                for s, v in zip(seq, table.values()):
                    self.assertEquals(s, v)
                free = len(list(table.free()))
                self.assertEquals(free, len(table) - len(seq), "%d %d" % (len(table),len(seq))  )
                for i in seq:
                    self.assertTrue(i in table)
            iters = zip(table.iter_pos(), table.values(), table.items())
            for pos, val, (ipos, ival) in iters:
                self.assertEquals(pos, ipos)
                self.assertEquals(val, ival)

    #TODO: test FakeSound

class TestSurfaces (unittest.TestCase):

    def testSurfaceFromFile (self):
        func = gameUtils.surface_from_file
        tostring = pygame.image.tostring
        images = glob.glob(op_.join(IMAGES_PATH, '*'))
        wrong_conv = it.cycle(['foobar', 'spam', 'eggs'])
        for img in images:
            for conv in (const.ALPHA_CONV, const.NORMAL_CONV):
                try:
                    surf = func(img)
                    surf2 = func(img, conv)
                except pygame.error as e:
                    if str(e) == 'Unsupported image format':
                        pass
                    else: raise e
                else:
                    self.assertRaises(ValueError, func, img, next(wrong_conv))
                    self.assertIsInstance(surf, pygame.Surface)
                    self.assertIsInstance(surf2, pygame.Surface)
                    if conv == const.ALPHA_CONV:
                        self.assertEqual(tostring(surf, 'RGBA'),
                                         tostring(surf2, 'RGBA'))

    def testSurfaceResize (self):
        r = random.randint
        resize = gameUtils.surface_resize
        for _ in range(100):
            surf = pygame.Surface((r(1,1000),r(1,1000)))
            newsize = r(1,1000), r(1,1000)
            newsurf = resize(surf, *newsize)
            self.assertEqual(newsurf.get_size(), newsize)
            ws = r(-100, -1)
            for w,h in ([ws,ws], [ws,abs(ws)], [abs(ws),ws]):
                self.assertRaises(ValueError, resize, surf, w, h)

    def testScale (self):
        r = random.randint
        sizes = [(r(1, 1000), r(1,1000)) for _ in range(100)]
        for w,h in sizes:
            # scale_perc
            perc = r(1,500)
            pw, ph = w*perc//100, h*perc//100
            self.assertEqual(gameUtils.scale_perc(w,h,perc), (pw,ph))
            # scale_perc_from
            fs = gameUtils.scale_perc_from(w,h,perc,const.WIDTH)
            self.assertEqual(fs, (pw, h*pw//w))
            fs = gameUtils.scale_perc_from(w,h,perc,const.HEIGHT)
            self.assertEqual(fs, (ph*w//h, ph))
            # scale_from_dim
            length = r(1,500)
            ds = gameUtils.scale_from_dim(w,h, length, const.WIDTH)
            self.assertEqual(ds, (length, length*h//w))
            ds = gameUtils.scale_from_dim(w,h, length, const.HEIGHT)
            self.assertEqual(ds, (length*w//h, length))
            # test errors
            for func in (gameUtils.scale_perc_from, gameUtils.scale_from_dim):
                for dim in 'foo spam eggs'.split():
                    self.assertRaises(ValueError, func, w,h,perc, dim)
            args = [list(r(-10, 10) for _ in 'whp') for _ in range(100)]
            for a in args:
                if all(v >= 0 for v in a):
                    i = a.index(max(a))
                    a[i] = -(a[i]+1)
                self.assertRaises(ValueError, gameUtils.scale_perc, *a)


class TestPlugin (unittest.TestCase):

    @classmethod
    def setUpClass (cls):
        cls.runtime_fake_module_format_fail_import = '''
import %s # fake module name
'''
        cls.runtime_fake_module_format_fail_plugin = '''
MODULE_PLUGINS = ["foo", "bar", "Baz"]
EX_ERR = ['ZeroDivisionError', 'IndexError', 'AttributeError']
def foo (*a, **k):
  1//0
def bar (*a, **k):
  raise IndexError("raised from a fake plugin object.")
class Baz:
  def __init__ (self):
    print(self.spam)
'''

    def setUp (self):
        self.bk_dir = tempfile.mkdtemp()
        with open(op_.join(self.bk_dir, '__init__.py'), 'w'):
            pass

    def tearDown (self):
        shutil.rmtree(self.bk_dir)

    def testFindModules (self):
        expect = ('gtkGameObject',)
        res = bumpo.plugins.find_plugin_modules()
        self.assertEqual(res, expect)
        files = []
        for _ in range(10):
            f = tempfile.NamedTemporaryFile(suffix='.py', dir=self.bk_dir,  delete=False)
            files.append(op_.splitext(op_.basename(f.name))[0])
            f.close()
        res = sorted(bumpo.plugins.find_plugin_modules(self.bk_dir))
        self.assertEqual(sorted(files), res)

    def testLoadPlugin (self):
        modules = bumpo.plugins.find_plugin_modules()
        paths = bumpo.plugins.__path__
        for modname in modules:
            module = bumpo.plugins.get_module(modname, paths)
            for plugname in module.MODULE_PLUGINS:
                plugin = bumpo.plugins.load_plugin(plugname, modname, paths)
                # nothing to do here, should run as expected.
        # fail on module load
        fakemodulenames = [string.ascii_letters, 'foobarbaz', 'spam_module']
        f = tempfile.NamedTemporaryFile(suffix='.py', dir=self.bk_dir,  delete=False)
        f.write((self.runtime_fake_module_format_fail_import % choice(fakemodulenames)).encode('utf-8'))
        f.close()
        plugname = op_.splitext(op_.basename(f.name))[0]
        module = bumpo.plugins.find_plugin_modules(self.bk_dir)[0]
        self.assertRaises(bumpo.plugins.LoadPluginError,
                          bumpo.plugins.load_plugin,
                          plugname, module, [self.bk_dir])
        self.tearDown()
        self.setUp()
        # fail on plugin use
        f = tempfile.NamedTemporaryFile(suffix='.py', dir=self.bk_dir,  delete=False)
        f.write(self.runtime_fake_module_format_fail_plugin.encode('utf-8'))
        f.close()
        plugname = op_.splitext(op_.basename(f.name))[0]
        modname = bumpo.plugins.find_plugin_modules(self.bk_dir)[0]
        module = bumpo.plugins.get_module(modname, [self.bk_dir])
        for plugname, err in zip(module.MODULE_PLUGINS, module.EX_ERR):
            plugin = bumpo.plugins.load_plugin(plugname, modname, [self.bk_dir])
            self.assertRaises(getattr(exceptions, err), plugin)


def load_tests(args=None):
    loader = unittest.TestLoader()
    if not args:
        test_cases = (TestConvert, TestMisc, TestSurfaces, TestPlugin)
    else:
        g = globals()
        test_cases = (g[t] for t in args)
    return (loader.loadTestsFromTestCase(t) for t in test_cases)



if __name__ == '__main__':
    os.chdir(pwd)
    pygame.init()
    get_screen()
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(load_tests(sys.argv[1:])))
    pygame.quit()
