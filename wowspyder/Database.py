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

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
session = None

class Database:
    def __init__(self, autocommit=True, echo=True):
        prefs = Preferences.Preferences()
        
        engine_url = prefs.database_url
        
        self.engine = sa.create_engine(engine_url, echo=echo)
		
        Session = sa.orm.sessionmaker(bind=self.engine, autocommit=autocommit)
        self.session = Session()
        
    def insert(self, obj):
        return self.session.merge(obj)
        
    def get_base(self):
        return Base



class DatabaseTests(unittest.TestCase):
	def setUp(self):
		self.database = Database()


if __name__ == '__main__':
	unittest.main()
