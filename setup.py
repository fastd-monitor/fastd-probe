#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages, Command

setup(
    name='fastd-probe',
    version="0.0.1dev1",
    description='A fastd probing machinery based on gevent',
    license="AGPL 3",
    author="Andreas Motl",
    author_email="andreas.motl@elmyra.de",
    url='https://github.com/fastd-monitor/fastd-probe',
    keywords="fastd client probe",
    py_modules=['fastd_probe'],
    install_requires=[
        'Jinja2',
        'gevent',
        'gping==0.2dev3',
        'ripe.atlas.cousteau',
        'appdirs',
        'json-store',
        'progressbar2',
        'colorama',
        #'args',
    ],
    dependency_links=[
        'https://github.com/kennethreitz/args/tarball/0a6d5eb#egg=args',
        'https://github.com/fastd-monitor/gping/tarball/integrations#egg=gping-0.2dev2',
        ],
    entry_points={
        'console_scripts': [
            'fastd-probe = fastd_probe:run',
            ],
        },
)
