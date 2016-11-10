#!/usr/bin/env python
# coding: utf-8
import os
from setuptools import setup, find_packages, Command

setup(
    name='fastd-probe',
    version="0.0.1dev1",
    description='A fastd probe client',
    author="Andreas Motl",
    author_email="andreas.motl@elmyra.de",
    url='https://github.com/fastd-monitor/fastd-probe',
    keywords="fastd client probe",
    py_modules=['fastd_probe'],
    install_requires=[
        'Jinja2',
        'gevent',
        'gping==0.2dev2',
        #'args',
    ],
    dependency_links=[
        'https://github.com/kennethreitz/args/tarball/0a6d5eb#egg=args',
        'https://github.com/fastd-monitor/gping/tarball/integrations#egg=gping-0.2dev1',
        ],
    entry_points={
        'console_scripts': [
            'fastd-probe = fastd_probe:run',
            ],
        },
)
