#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

VERSION = __import__('coop_cms').__version__

import os
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='coop-cms',
    version = VERSION,
    description='Small CMS built around a tree navigation open to any django models',
    packages=[  'coop_cms',
                'coop_cms.management',
                'coop_cms.management.commands',
                'coop_cms.templatetags',
                'coop_cms.migrations'
                ],
    include_package_data=True,
    author='Luc Jean',
    author_email='ljean@apidev.fr',
    license='BSD',
    zip_safe=False,
    install_requires = ['Django==1.3.1',
                        'django-floppyforms==0.4.7',
                        'django-livesettings==1.4-7',
                        'sorl-thumbnail==11.09',
                        ],
    long_description = open('README.rst').read(),
    download_url = "https://github.com/quinode/coop_cms/tarball/master",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Natural Language :: English',
        'Natural Language :: French',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ]                    

)

