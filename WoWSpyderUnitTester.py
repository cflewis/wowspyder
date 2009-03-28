#!/usr/bin/env python
# encoding: utf-8
"""
WoWSpyderUnitTester.py

Created by Chris Lewis on 2009-03-15.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import wowspyder
from wowspyder import Battlegroup, XMLDownloader, Arena, Logger

log = Logger.log()

def main():
    suite = unittest.TestLoader().loadTestsFromModule(wowspyder.XMLDownloader)
    suite.addTest(unittest.TestLoader().loadTestsFromModule(wowspyder.Arena))
    suite.addTest(unittest.TestLoader().loadTestsFromModule(wowspyder.Team))
    suite.addTest(unittest.TestLoader().loadTestsFromModule(wowspyder.Guild))
    suite.addTest(unittest.TestLoader().loadTestsFromModule(wowspyder.Character))
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()

