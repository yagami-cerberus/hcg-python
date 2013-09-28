#!/usr/bin/env python

import os
import sys
from distutils.core import setup
from distutils.extension import Extension

from Cython.Distutils import build_ext

VERSION = __import__("hcg").VERSION

setup(
    name='hcg',
    version="0.0.1",
    url='https://github.com/yagami-cerberus/hcg-python',
    license='MIT',
    
    scripts=['hcg/bin/hcg'],
    cmdclass={'build_ext': build_ext},
    packages=['hcg'],
    ext_modules=[
        Extension(
            'hcg._compress', sources = ["src/compress.pyx"]
        ),
        Extension(
            'hcg._sampling', sources = ["src/sampling.pyx"]
        )
    ],
)
