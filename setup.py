#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

VERSION = __import__('djaloha').__version__

import os
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-coop-cms',
    version = VERSION,
    description='Small CMS built around a tree navigation open to any django models',
    packages=['coop_cms','coop_cms.management','coop_cms.templatetags',,'coop_cms.migrations'],
    include_package_data=True,
    author='Luc Jean',
    author_email='ljean@apidev.fr',
    license='BSD',
    #long_description=read('README.txt'),
    download_url='git://github.com/quinode/coop_cms.git',
    zip_safe=False,
    install_requires = [
        'Django==1.3.1',
        'django-floppyforms==0.4.7',
        'django-livesettings==1.4-7',
        'sorl-thumbnail==11.09',
    ]
)

