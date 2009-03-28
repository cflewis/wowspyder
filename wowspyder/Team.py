#!/usr/bin/env python
# encoding: utf-8
"""
Team.py

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
from Guild import Guild
from Battlegroup import Realm
import XMLDownloader
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    DateTime, Unicode, Integer
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declarative_base
import urllib2
import StringIO

log = Logger.log()
database = Database.Database()
Base = database.get_base()

class TeamParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the team parser.'''
        self.database = database
        self.session = self.database.session
        Base.metadata.create_all(self.database.engine)
        
        if downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
        
    def get_team(self, name, realm, site, size):
        # cflewis | 2009-03-27 | Can speed this up by querying the DB
        # for the object first
        team = self.session.query(Team).get((name, realm, site))
        
        if team:
            return team
        else:            
            source = self.downloader.download_url(WoWSpyderLib.get_site_url(site) + "team-info.xml?" + \
                "r=" + urllib2.quote(realm.encode("utf-8")) + \
                "&ts=" + str(size) + \
                "&t=" + urllib2.quote(name.encode("utf-8")))
            
        return self.parse_team(StringIO.StringIO(source), site)
        
    def parse_team(self, xml_file_object, site):
        xml = minidom.parse(xml_file_object)
        team_nodes = xml.getElementsByTagName("arenaTeam")
        team_node = team_nodes[0]
        
        name = team_node.attributes["name"].value
        realm = team_node.attributes["realm"].value
        url = team_node.attributes["teamUrl"].value
        size = int(team_node.attributes["teamSize"].value)
        team = Team(name, realm, site, size)
        log.debug("Creating team " + name)
        self.database.insert(team)
        
        self.parse_team_characters(xml_file_object, site)

        return team
        
    def parse_team_characters(self, xml_file_object, site):
        pass
        # xml = minidom.parse(xml_file_object)
        # character_nodes = xml.getElementsByTagName("character")
        # 
        # for character_node in character_nodes:
        #     try:
        #         name = character_node.attributes["guild"].value
        #         realm = character_node.attributes["realm"].value
        #         log.debug("Creating guild " + name)
        #         guild = Guild(name, realm, site)
        #         self.database.insert(guild)
        #         guilds.append(guild)
        #     except KeyError, e:
        #         log.debug("Found no guild")
        # 
        # return guilds


class Team(Base):
    __table__ = Table("TEAM", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("size", Integer()),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime(), index=True),
        ForeignKeyConstraint(['realm', 'site'], ['REALM.name', 'REALM.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    def __init__(self, name, realm, site, size, last_refresh=None):
        self.name = name
        self.realm = realm
        self.site = site
        self.size = size
        self.last_refresh = last_refresh
        
    def __repr__(self):
        return unicode("<Team('%s','%s','%s','%d','%s')>" % (self.name, \
            self.realm, self.site, self.size, self.team))
    
    @property
    def url(self):
        log.debug("Returning URL for " + self.name + "," + self.realm + "," + \
            self.site)
        return WoWSpyderLib.get_site_url(self.site) + "team-info.xml?" + \
            "r=" + urllib2.quote(self.realm.encode("utf-8")) + \
            "&ts=" + str(self.size) + \
            "&t=" + urllib2.quote(self.name.encode("utf-8"))
                
class TeamParserTests(unittest.TestCase):
    def setUp(self):
        self.tp = TeamParser()
        self.test_team = database.session.query(Team).filter(and_(\
            Team.realm == u"Cenarius", Team.name == u"Party Like Rockstars",
            Team.site == u"us")).one()

if __name__ == '__main__':
    unittest.main()
