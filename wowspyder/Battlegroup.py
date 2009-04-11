#!/usr/bin/env python
# encoding: utf-8
"""
Battlegroup.py

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
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    Unicode, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

log = Logger.log()

Base = Database.get_base()

class BattlegroupParser(object):
    """A parser to retrieve realms and battlegroups from the XML file
    provided by Okoloth's Armory Musings. http://armory-musings.appspot.com/
    
    """
    def __init__(self):
        self._session = Database.session
        Base.metadata.create_all(Database.engine)
        
    def parse_battlegroup_file(self, filename):
        # cflewis | 2009-03-15 | This should parse as UTF-8 automatically
        xml = minidom.parse(filename)
        log.debug("XML is %s" % xml.toxml())
        battlegroups = xml.getElementsByTagName("battlegroup")
        
        for bg_node in battlegroups:
            self._parse_battlegroup_node(bg_node)
        
    def _parse_battlegroup_node(self, bg_node):
        name = bg_node.attributes["name"].value
        site = bg_node.attributes["site"].value
                
        bg = Battlegroup(name, site)
        Database.insert(bg)
        log.debug("Battlegroup is %s %s" % (site, name))
        
        realms = bg_node.getElementsByTagName("realm")
        
        for realm_node in realms:
            self._parse_realm_node(realm_node)
        
    def _parse_realm_node(self, realm_node):
        name = realm_node.attributes["name"].value
        site = realm_node.attributes["site"].value
        battlegroup = realm_node.parentNode.attributes["name"].value
        server_type = realm_node.attributes["type"].value
        language = realm_node.attributes["lang"].value        
        
        realm = Realm(name, site, battlegroup, server_type, language)
        Database.insert(realm)
        log.debug("Realm is %s %s" % (site, name))
        
    def get_realm_list(self):
        return self._session.query(Realm).all()
        
    def get_us_realm_list(self):
        return self._session.query(Realm).filter(Realm.site == u"us").all()


class Battlegroup(Base):
    """A battlegroup, with a name and a site."""
    
    __table__ = Table("BATTLEGROUP", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    def __init__(self, name, site):
        self.name = name
        self.site = site
        
    def __repr__(self):
        return unicode("<Battlegroup('%s','%s')>" % (self.name, self.site))
        
        
class Realm(Base):
    """A realm"""
    __table__ = Table("REALM", Base.metadata,    
        Column("name", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("battlegroup", Unicode(100)),
        Column("server_type", Unicode(6)),
        Column("language", Unicode(2)),
        Column("last_refresh", DateTime(), index=True),
        Column("lock_id", String(100), index=True),
        Column("lock_time", DateTime()),
        ForeignKeyConstraint(['battlegroup', 'site'], ['BATTLEGROUP.name', 'BATTLEGROUP.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    def __init__(self, name, site, battlegroup, server_type, language, last_refresh=None):
        self.name = name
        self.site = site
        self.battlegroup = battlegroup
        self.server_type = server_type
        self.language = language
        
    def __repr__(self):
        return unicode("<Realm('%s','%s', '%s', '%s', '%s')>" % (self.name, \
            self.site, self.battlegroup, self.server_type, self.language))
    

class BattlegroupParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = BattlegroupParser()
        
    def testParser(self):
        self.parser.parse_battlegroup_file("data/battlegroups.xml")

if __name__ == '__main__':
    unittest.main()