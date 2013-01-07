# -*- coding: utf-8 -*-
# Setup file for bumpo.
# This file is part of bumpo and is released under a MIT-like license
# Copyright (c) 2011  Marco Chieppa (aka crap0101)
# See the file COPYING.txt in the root directory of this package.

import os
import sys
import shutil
import subprocess
import os.path as op_
from distutils.core import setup


MODULE_NAME = 'bumpo'
MODULE_VERSION = '0.3'

if __name__ == '__main__':
    os.chdir(op_.dirname(op_.realpath(__file__)))
    setup(
        name=MODULE_NAME,
        version=MODULE_VERSION,
        description="module for create and manage game objects with pygame",
        author='Marco Chieppa (aka crap0101)',
        author_email='crap0101@riseup.net',
        maintainer='Marco Chieppa (aka crap0101)',
        maintainer_email='crap0101@riseup.net',
        license='MIT-like License',
        platforms=['platform independent'],
        requires=['pygame(>=1.7)'], #optional: 'pygtk(>=2.0.0)'],
        package_dir={'bumpo': 'src'},
        packages = ['bumpo', 'bumpo.plugins'],
        )


