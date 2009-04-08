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

Session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine, autocommit=False))
    
def insert(obj):
    """Insert an object into the database. Actually this just happens with
    an SQLAlchemy merge, so WoWSpyder never has to worry about whether to
    insert or update.
    
    """
    return_obj = None
        
    try:
        return_obj = session().add(obj)
        session.commit()
    except Exception, e:
        try:
            return_obj = session().merge(obj)
        except Exception, e:
            log.warning("Database problem: " + str(e))
            session().rollback()
            raise
        else:
            log.debug("Merged with database: " + str(obj))
            try:
                session().commit()
            except Exception, e:
                log.warning("Database problem: " + str(e))
                session().rollback()
    else:
        log.debug("Inserted to database: " + str(obj))
    
def session():
    return Session()
    
def get_base():
    """Returns the SQLAlchemy Base object."""
    return Base



class DatabaseTests(unittest.TestCase):
	def setUp(self):
	    pass
	    
	def testSession(self):
	    s1 = Session()
	    s2 = Session()
	    self.assertEquals(s1, s2)


if __name__ == '__main__':
	unittest.main()
