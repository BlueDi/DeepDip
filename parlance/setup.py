#!/bin/env python
r'''Parlance setup script
    Copyright (C) 2008  Eric Wald
    
    This distribution script uses setuptools, by Phillip J. Eby.
    To use it, enter "python setup.py install" at a command line.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

try:
    readme = open('README.txt').read()
except:
    # Todo: Attempt to find the README file.
    readme = None

from setuptools import setup

setup(
    # Provided items
    name = "Parlance",
    version = "1.4.1",
    packages = ["parlance"],
    entry_points = {
        "console_scripts": [
            "parlance-server = parlance.server:run",
            "parlance-holdbot = parlance.player:run",
            "parlance-chatty = parlance.chatty:run",
            "parlance-config = parlance.config:run",
            "parlance-raw-client = parlance.main:run",
            "parlance-raw-server = parlance.network:run",
        ],
        "gui_scripts": [
        ],
        "parlance.bots": [
            "HoldBot = parlance.player:HoldBot",
        ],
        "parlance.judges": [
            "standard = parlance.judge:Judge",
        ],
        "parlance.variants": [
            "mini = parlance.xtended:mini",
            "small = parlance.xtended:small",
            "standard = parlance.xtended:standard",
            "three = parlance.xtended:three",
        ],
    },
    
    # Project metadata
    author = "Eric Wald",
    author_email = "breadman@users.sourceforge.net",
    description = "A framework for playing the Diplomacy board game over a network.",
    long_description = readme,
    license = "Artistic License 2.0",
    keywords = "daide diplomacy board game server",
    url = "http://sourceforge.net/projects/parlance/",
    platforms = "Any",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: Artistic License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Games/Entertainment :: Turn Based Strategy",
    ],
    
    # Installation options
    zip_safe = True,
    test_suite = "parlance.test",
    package_data = {
        "parlance": ["data/*.html", "data/*.cfg"],
    },
)
