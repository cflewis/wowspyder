#!/usr/bin/env python
# encoding: utf-8
"""
Preferences.py

Created by Chris Lewis on 2009-03-27.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import yaml
import re

class Preferences(object):
    def __init__(self, preferences_file= \
            re.sub("Preferences.py(c)?$", "", os.path.abspath(__file__)) + \
            ".wowspyder.yaml"):
        stream = open(preferences_file, 'r')
        self.__options__ = yaml.load(stream)

    @property
    def options(self):
        return self.__options__
        
    @property
    def refresh_all(self):
        return self.__options__["refresh_all"]
        
    @refresh_all.setter
    def refresh_all(self, value):
        self.__options__["refresh_all"] = value
        
    @property
    def database_url(self):
        return self.__options__["database_url"]
        
    @database_url.setter
    def database_url(self, value):
        self.__options__["database_url"] = value

class PreferencesTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()