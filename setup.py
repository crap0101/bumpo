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


PACKAGE_NAME = 'bumpo'
PACKAGE_VERSION = '0.1'

if __name__ == '__main__':
    setup(
        name=PACKAGE_NAME,
        version=PACKAGE_VERSION,
        description="basic utility module for pygame's object",
        author='Marco Chieppa (aka crap0101)',
        author_email='crap0101@riseup.net',
        maintainer='Marco Chieppa (aka crap0101)',
        maintainer_email='crap0101@riseup.net',
        license='MIT-like License',
        platforms=['platform independent'],
        requires=['pygame(>=1.7)', 'pygtk(>=2.0.0)'],
        package_dir={PACKAGE_NAME: ''},
        packages=[PACKAGE_NAME],
        py_modules=['bumpo.gameObjects', 'bumpo.gameutils'])


