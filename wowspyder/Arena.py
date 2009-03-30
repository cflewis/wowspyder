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
import Preferences
import datetime


log = Logger.log()
Base = Database.get_base()

class ArenaParser(object):
    """A class that parses the XML returned by the Armory Arena pages.
    
    This class is primarily used for finding teams, as the Arena's 
    themselves don't hold much interesting data.
    
    """
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        self._downloader = downloader
        
        if self._downloader is None:
            self._downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
                   
        self._session = Database.session
        Base.metadata.create_all(Database.engine)
        self._tp = Team.TeamParser(downloader=self._downloader)
        
    def __del__(self):
        self._downloader.close()
        
    def get_arena_teams(self, battlegroup, realm, site, get_characters=False):
        '''Returns a list of arena teams as team objects. Setting get_characters
        to true will cause teams, their characters and their guilds to be
        downloaded. This cascading effect is very slow and should be used
        with caution.
        
        '''
        for ladder_number in [2, 3, 5]:
            try:
                source = self._downloader.download_url( \
                    WoWSpyderLib.get_arena_url(battlegroup, realm, site, \
                    ladder_number=ladder_number))
            except Exception, e:
                log.warning("Couldn't get arena page for ladder " + 
                    ladder_number + ", continuing...")
                continue
            
            max_pages = WoWSpyderLib.get_max_pages(source)
        
            for page in range(1, (max_pages + 1)):
                log.debug(battlegroup + " " + realm + \
                    ": Downloading arena page " + str(page) + " of " \
                    + str(max_pages))
                
                try:
                    source = self._downloader.download_url( \
                        WoWSpyderLib.get_arena_url(battlegroup, realm, site, page=page, \
                            ladder_number=ladder_number))
                except Exception, e:
                    log.warning("Couldn't get arena page, continuing...")
                    continue
                
                teams = self.__parse_arena_file(StringIO.StringIO(source), site, get_characters=get_characters)
                
        # cflewis | 2009-03-24 | Query the DB to ensure that the teams are
        # unique and to avoid having to do annoying expansion and joining of
        # the returned teams list
        return self._session.query(Team.Team).filter(and_(Team.Team.realm == realm, Team.Team.site == site))
            
    def __parse_arena_file(self, xml_file_object, site, get_characters=False):
        """Parse the XML of an arena page"""
        xml = minidom.parse(xml_file_object)
        team_nodes = xml.getElementsByTagName("arenaTeam")
        teams = []
        
        for team_node in team_nodes:
            name = team_node.attributes["name"].value
            realm = team_node.attributes["realm"].value
            size = team_node.attributes["size"].value
            
            try:
                team = self._tp.get_team(name, realm, site, size, get_characters=get_characters)
                teams.append(team)
            except Exception, e:
                log.warning("Couldn't get team " + name + ", con")
            
        return teams
        
        
    def close_downloader(self):
        self._downloader.close()
        
class ArenaParserTests(unittest.TestCase):
    def setUp(self):
        self.us_realm = u"Ravenholdt"
        self.us_battlegroup = u"Whirlwind"
        self.eu_realm = u"Argent Dawn"
        self.eu_battlegroup = u"Bloodlust"
        self.ap = ArenaParser()
        self.prefs = Preferences.Preferences()
        
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
        
    def testGetTeamsNoCharacters(self):
        print "Started no character test at " + str(datetime.datetime.now())
        log.info("Started no character test at " + str(datetime.datetime.now()))
        teams = self.ap.get_arena_teams(self.us_battlegroup, self.us_realm, u"us", get_characters=False)
        log.info("Ended no character test at " + str(datetime.datetime.now()))
        print "Ended no character test at " + str(datetime.datetime.now())
        
    def testGetTeamsAndCharacters(self):
        original_option = self.prefs.refresh_all
        self.prefs.refresh_all = False
        print "Started character test at " + str(datetime.datetime.now())
        log.info("Started character test at " + str(datetime.datetime.now()))
        teams = self.ap.get_arena_teams(self.us_battlegroup, self.us_realm, u"us", get_characters=True)
        self.prefs.refresh_all = original_option
        print "Ended character test at " + str(datetime.datetime.now())
        log.info("Ended character test at " + str(datetime.datetime.now()))
        
        

if __name__ == '__main__':
    unittest.main()