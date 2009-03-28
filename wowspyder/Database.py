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
session = None

log = Logger.log()

class Database:
    def __init__(self, autocommit=True, echo=True):
        prefs = Preferences.Preferences()
        
        engine_url = prefs.database_url
        
        self.engine = sa.create_engine(engine_url, echo=echo)
		
        Session = sa.orm.sessionmaker(bind=self.engine, autocommit=autocommit)
        self.session = Session()
        
    def insert(self, obj):
        return_obj = None
        
        try:
            return_obj = self.session.merge(obj)
        except sae.IntegrityError, e:
            # cflewis | 2009-03-28 | Do nothing... merging shouldn't have
            # caused an integrity error
            log.warning("Integrity error " + str(e))
            raise
        
    def get_base(self):
        return Base



class DatabaseTests(unittest.TestCase):
	def setUp(self):
		self.database = Database()


if __name__ == '__main__':
	unittest.main()
