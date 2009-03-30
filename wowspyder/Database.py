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
import logging

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.exceptions as sae

Base = declarative_base()

prefs = Preferences.Preferences()

log = Logger.log()

engine_url = prefs.database_url

echo = False

if log.isEnabledFor(logging.DEBUG):
    echo = True

engine = sa.create_engine(engine_url, echo=echo)

Session = sa.orm.sessionmaker(bind=engine, autocommit=True)
session = Session()

    
def insert(obj):
    """Insert an object into the database. Really, this just happens with
    an SQLAlchemy merge, so WoWSpyder never has to worry about whether to
    insert or update.
    
    """
    return_obj = None
    
    try:
        return_obj = session.merge(obj)
    except sae.IntegrityError, e:
        # cflewis | 2009-03-28 | Do nothing... merging shouldn't have
        # caused an integrity error
        log.warning("Integrity error " + str(e))
        raise
    
def get_base():
    """Returns the SQLAlchemy Base object."""
    return Base



class DatabaseTests(unittest.TestCase):
	def setUp(self):
	    pass


if __name__ == '__main__':
	unittest.main()
