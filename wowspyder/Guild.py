#!/usr/bin/env python
# encoding: utf-8
"""
Guild.py

Created by Chris Lewis on 2009-03-12.
Copyright (c) 2009 Regents of University of Califonia. All rights reserved.
"""

import sys
import os
import unittest
from xml.dom import minidom
import Database
import Logger
import datetime
import WoWSpyderLib
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    DateTime, Unicode, Integer
from sqlalchemy.ext.declarative import declarative_base

log = Logger.log()
database = Database.Database()
Base = database.get_base()

class GuildParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the guild parser.'''
        self.database = database
        self.session = self.database.session
        Base.metadata.create_all(self.database.engine)
        
        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)


class Guild(Base):
    __table__ = Table("GUILD", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime(), index=True),
        ForeignKeyConstraint(['realm', 'site'], ['REALM.name', 'REALM.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    def __init__(self, name, realm, site, last_refresh=None):
        self.name = name
        self.realm = realm
        self.site = site
        self.last_refresh = last_refresh
        
    def __repr__(self):
        return unicode("<Guild('%s','%s','%s')>" % (self.name, self.realm, \
            self.site))
            
    def __cmp__(x, y):
        if x.name == y.name and x.realm == y.realm and x.site == y.site:
            return 0
        
        # cflewis | 2009-03-24 | You can't actually compare the order,
        # just the equality, so 1 is as good as -1!
        return 1
    
    @property
    def url(self):
        return self.get_url_page(1)
            
    def get_url_page(self, page_number):
        log.debug("Returning URL for " + guild + "," + realm + "," + site)
        
        return WoWSpyderLib.get_site_url(site) + "guild-info.xml?" + \
            "r=" + urllib2.quote(self.realm.encode("utf-8")) + \
            "&n=" + urllib2.quote(self.name.encode("utf-8")) + \
            "&p=" + str(page_number)
                
class GuildParserTests(unittest.TestCase):
    def setUp(self):
        pass

if __name__ == '__main__':
    unittest.main()
