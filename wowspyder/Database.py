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
import gc

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
Session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine, autoflush=False, autocommit=False, weak_identity_map=True))

def insert(obj):
    """Insert an object into the database. Actually this just happens with
    an SQLAlchemy merge, so WoWSpyder never has to worry about whether to
    insert or update.
    
    """
    return_obj = None
        
    try:
        return_obj = session().merge(obj)
        session().commit()
    except (sa.exceptions.IntegrityError, sa.exceptions.FlushError), e:
        # cflewis | 2009-04-11 | Merge shouldn't do this, so ignore
        log.warning("Error commiting: " + str(e))
    
    # except Exception, e:
    #     log.warning("Database problem: " + str(e))
    #     session().rollback()
    #     raise
    # else:
    #     log.debug("Saved to database")
    #     
    #     # cflewis | 2009-04-06 | I've been unhappy with SQLA's detection
    #     # of when to autocommit when it's placed into a scoped session.
    #     # I have no idea what the problem is, but it is aggravating.
    #     # It looks like i'll have to force commits myself.
    #     session().commit()
    #     session().expunge_all()
            
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
