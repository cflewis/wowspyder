#!/usr/bin/env python
# encoding: utf-8
"""
Item.py

Created by Chris Lewis on 2009-04-06.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
from Parser import Parser
from xml.dom import minidom
import Database
import Logger
import datetime
import WoWSpyderLib
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    DateTime, Unicode, Integer
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref
from Enum import Enum
import urllib2
import StringIO
import re

log = Logger.log()

Base = Database.get_base()

class AchievementParser(Parser):
    def __init__(self, downloader=None):
        '''Initialize the achievement parser.'''
        Parser.__init__(self, no_downloader=True)
        
    def _check_download(self, source, exception):
        pass
        
    def get_achievement(self, achievement_id, category_id, name, points, description):
        """Returns an achievement object.
        
        """
        achievement = self._session.query(Achievement).get(achievement_id)
        
        if achievement:
            return achievement
            
        log.debug("Saving achievement...")
            
        # cflewis | 2009-04-02 | If downloading fails, the whole team
        # couldn't be found, so the exception should propagate up.
        achievement = Achievement(achievement_id, category_id, name, points, \
            description)
        Database.insert(achievement)
        
        return achievement

class AchievementParserTests(unittest.TestCase):
    def setUp(self):
        pass
        
class Achievement(Base):
    """An achievement"""
    __table__ = Table("ACHIEVEMENT", Base.metadata,    
        Column("achievement_id", Integer(), primary_key=True),
        Column("category_id", Integer()),
        Column("name", Unicode(100), index=True),
        Column("points", Integer()),
        Column("description", Unicode(200)),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime()),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )

    def __init__(self, achievement_id, category_id, name, points, \
            description, last_refresh=None):
        self.achievement_id = achievement_id
        self.category_id = category_id
        self.name = name
        self.points = points
        self.description = description
        self.last_refresh = last_refresh

    def __repr__(self):
        return unicode("<Achievement('%d','%s')>" % \
            (self.achievement_id, self.name))

if __name__ == '__main__':
    unittest.main()