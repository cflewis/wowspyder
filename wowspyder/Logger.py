#!/usr/bin/env python
# encoding: utf-8
"""
Logger.py

Created by Chris Lewis on 2009-03-21.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import logging
import logging.handlers

__log = logging.getLogger("wowspyder")
__log.setLevel(logging.DEBUG)

__handler = logging.FileHandler(".output.log", "w")
__formatter = logging.Formatter("%(asctime)s : %(levelname)s : " + \
    "%(module)s,%(lineno)d : %(message)s")

__handler.setFormatter(__formatter)

__log.addHandler(__handler)

def log():
    return __log
