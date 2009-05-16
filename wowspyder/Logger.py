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

_log = logging.getLogger("wowspyder")
_log.setLevel(logging.DEBUG)

_handler = logging.FileHandler(".output.log", "w")
_formatter = logging.Formatter("%(asctime)s : %(levelname)s : " + \
    "%(module)s,%(lineno)d : %(message)s")

_handler.setFormatter(_formatter)

_log.addHandler(_handler)

def log():
    return _log
