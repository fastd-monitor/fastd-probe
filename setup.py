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
        #'args',
    ],
    dependency_links=[
        'https://github.com/kennethreitz/args/tarball/0a6d5eb#egg=args',
        ],
    entry_points={
        'console_scripts': [
            'fastd-probe = fastd_probe:run',
            ],
        },
)
