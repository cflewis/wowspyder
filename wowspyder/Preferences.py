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

class Preferences:
    def __init__(self, preferences_file= \
            re.sub("Preferences.py(c)?$", "", os.path.abspath(__file__)) + \
            ".wowspyder.yaml"):
        stream = open(preferences_file, 'r')
        options = yaml.load(stream)
        self.database_url = options["database_url"]
        self.refresh_all = options["refresh_all"]


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()