#!/usr/bin/env python

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import Command,setup

import gmail
long_description = gmail.description
version = gmail.version

class GenerateReadme(Command):
    description = "Generates README file from long_description"
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        open("README","w").write(long_description)

setup(name='gmail',
      version = version,
      description = 'Simple library to send email using GMail (includes background worker and logging classes)',
      long_description = long_description,
      author = 'Paul Chakravarti',
      author_email = 'paul.chakravarti@gmail.com',
      url = 'https://github.com/paulchakravarti/gmail-sender',
      cmdclass = { 'readme' : GenerateReadme },
      packages = ['gmail'],
      license = 'BSD',
      classifiers = [ "Topic :: Communications :: Email" ]
     )
