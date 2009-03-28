#!/usr/bin/env python
# encoding: utf-8
"""
Arena.py

Created by Chris Lewis on 2009-03-15.
Copyright (c) 2009 Regents of University of California. All rights reserved.
"""

import sys
import os
import unittest
import re
import XMLDownloader
import Battlegroup
import Logger
import WoWSpyderLib
import threading
import time
import urllib2
import Team
import Database
import StringIO
from xml.dom import minidom
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declarative_base

log = Logger.log()
database = Database.Database()
Base = database.get_base()

class ArenaParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        self.downloader = downloader
        
        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
                   
        self.database = database
        self.session = self.database.session
        Base.metadata.create_all(self.database.engine)
        self.tp = Team.TeamParser(downloader=downloader)
        
    def __del__(self):
        self.downloader.close()
        
    def get_arena_teams(self, battlegroup, realm, site):
        '''Returns a list of arena teams, stored in the database'''
        for ladder_number in [2, 3, 5]:
            source = self.downloader.download_url( \
                WoWSpyderLib.get_arena_url(battlegroup, realm, site, \
                ladder_number=ladder_number))
            max_pages = WoWSpyderLib.get_max_pages(source)
        
            for page in range(1, (max_pages + 1)):
                log.debug(battlegroup + " " + realm + \
                    ": Downloading arena page " + str(page) + " of " \
                    + str(max_pages))
                
                source = self.downloader.download_url( \
                    WoWSpyderLib.get_arena_url(battlegroup, realm, site, page=page, \
                        ladder_number=ladder_number))
                
                teams = self.parse_arena_file(StringIO.StringIO(source), site)
                
        # cflewis | 2009-03-24 | Query the DB to ensure that the teams are
        # unique and to avoid having to do annoying expansion and joining of
        # the returned teams list
        return self.session.query(Team.Team).filter(and_(Team.Team.realm == realm, Team.Team.site == site))
            
    def parse_arena_file(self, xml_file_object, site):
        xml = minidom.parse(xml_file_object)
        team_nodes = xml.getElementsByTagName("arenaTeam")
        teams = []
        
        for team_node in team_nodes:
            name = team_node.attributes["name"].value
            realm = team_node.attributes["realm"].value
            size = team_node.attributes["size"].value
            team = self.tp.get_team(name, realm, site, size)
            teams.append(team)
            
        return teams
        
        
    def close_downloader(self):
        self.downloader.close()
        
class ArenaParserTests(unittest.TestCase):
    def setUp(self):
        self.us_realm = u"Blackwater Raiders"
        self.us_battlegroup = u"Whirlwind"
        self.eu_realm = u"Argent Dawn"
        self.eu_battlegroup = u"Bloodlust"
        self.ap = ArenaParser()
        
    def testGetUSArenaURL(self):
        us_url = WoWSpyderLib.get_arena_url(self.us_battlegroup, \
            self.us_realm, u"us")
        self.assertTrue(re.match("http://www.wowarmory", us_url))
        
    def testGetEUArenaURL(self):
        eu_url = WoWSpyderLib.get_arena_url(self.eu_battlegroup, self.eu_realm, u"eu")
        self.assertTrue(re.match("http://eu.wowarmory", eu_url))
        
    def testGetEUArenaURLNonUnicode(self):
        eu_url = WoWSpyderLib.get_arena_url(self.eu_battlegroup, self.eu_realm, "eu")
        self.assertTrue(re.match("http://eu.wowarmory", eu_url))  
        
    def testGetGuilds(self):
        pass
        
        # guilds = self.ap.quick_get_arena_guilds(self.us_battlegroup, \
        #     self.us_realm, site="us")
        # 
        # log.debug(guilds)
        # log.debug("Found %d guilds", len(guilds))
        
    def testGetTeams(self):
        teams = self.ap.get_arena_teams(self.us_battlegroup, self.us_realm, u"us")
        

if __name__ == '__main__':
    unittest.main()