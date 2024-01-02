# -*- coding: utf-8 -*-

# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2010-2024  Marco Chieppa (aka crap0101)
# See the file COPYING in the root directory of this package.


"""
bumpo constants.
"""

SHAPE_RECT_ATTRS = ('bottom', 'bottomleft', 'bottomright',
                    'center', 'centerx', 'centery', 'h', 'height',
                    'left', 'midbottom', 'midleft', 'midright', 'midtop',
                    'right', 'size', 'top', 'topleft', 'topright',
                    'w', 'width', 'x', 'y')

# Shape/GameObjects coordinate constants
BOTTOMLEFT = 'bottomleft'
BOTTOMRIGHT = 'bottomright'
CENTER = 'center'
MIDBOTTOM = 'midbottom'
MIDLEFT = 'midleft'
MIDRIGHT = 'midright'
MIDTOP = 'midtop'
TOPLEFT = 'topleft'
TOPRIGHT = 'topright'
# ... and size
WIDTH = 'w'
HEIGHT = 'h'

# conversion constants
ALPHA_CONV = 'alpha' # pygame.SRCALPHA
NORMAL_CONV = 'normal'
