#!/usr/bin/env python

import os
from setuptools import setup

setup(name='absence',
      version='0.1.0',
      description='Wrapper for day-to-day use of duplicity.',
      author='Walter Moreira',
      author_email='walter@waltermoreira.net',
      packages=['absence'],
      scripts=['bin/absence.py'],
      license='LICENSE.txt',
      long_description=open('README.rst').read(),
      install_requires=[
          "sh",
          "boto"
      ],
      )
