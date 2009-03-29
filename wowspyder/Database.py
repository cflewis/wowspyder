#!/usr/bin/env python
# encoding: utf-8
"""
Database.py

Created by Chris Lewis on 2009-03-21.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import sqlalchemy as sa
import Preferences
import Logger

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.exceptions as sae

Base = declarative_base()

prefs = Preferences.Preferences()

engine_url = prefs.database_url

engine = sa.create_engine(engine_url, echo=True)

Session = sa.orm.sessionmaker(bind=engine, autocommit=True)
session = Session()

log = Logger.log()

    
def insert(obj):
    return_obj = None
    
    try:
        return_obj = session.merge(obj)
    except sae.IntegrityError, e:
        # cflewis | 2009-03-28 | Do nothing... merging shouldn't have
        # caused an integrity error
        log.warning("Integrity error " + str(e))
        raise
    
def get_base():
    return Base



class DatabaseTests(unittest.TestCase):
	def setUp(self):
	    pass


if __name__ == '__main__':
	unittest.main()
