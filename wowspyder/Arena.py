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
from Parser import Parser

log = Logger.log()

class ArenaParser(Parser):
    """A class that parses the XML returned by the Armory Arena pages.
    
    This class is primarily used for finding teams, as the Arena's 
    themselves don't hold much interesting data.
    
    """
    def __init__(self, downloader=None):
        log.debug("Creating arena with downloader " + str(downloader))
        Parser.__init__(self, downloader=downloader)
        self._tp = Team.TeamParser(downloader=self._downloader)
        
    def _check_download(self, source, exception):
        if exception:
            log.error("Unable to download file for arena")
            raise exception
            
        if re.search("arenaLadderPagedResult.*?filterValue=\"\"", source):
            log.error("Realm was invalid or not returned")
            raise IOError("Realm requested was invalid or not returned")
            
        return source
        
    def get_arena_teams(self, battlegroup, realm, site, get_characters=False, \
        ladders=[2,3,5], max_pages=None):
        '''Returns a list of arena teams as team objects. Setting get_characters
        to true will cause teams, their characters and their guilds to be
        downloaded. This cascading effect is very slow and should be used
        with caution.
        
        '''
        all_teams = []
        
        for ladder_number in ladders:
            try:
                source = self._download_url( \
                    WoWSpyderLib.get_arena_url(battlegroup, realm, site, \
                    ladder_number=ladder_number))
            except Exception, e:
                log.warning("Couldn't get arena page for ladder " + 
                    str(ladder_number) + ", continuing. ERROR: " + str(e))
                continue
            
            if not max_pages: 
                try:
                    max_pages = WoWSpyderLib.get_max_pages(source)
                except AttributeError, e:
                    # cflewis | 2009-04-22 | This means that
                    # this arena will be skipped, but it's better than
                    # crashing
                    max_pages = 0
        
            for page in range(1, (max_pages + 1)):
                log.debug(battlegroup + " " + realm + \
                    ": Downloading arena page " + str(page) + " of " \
                    + str(max_pages))
                
                try:
                    source = self._download_url( \
                        WoWSpyderLib.get_arena_url(battlegroup, realm, site, page=page, \
                            ladder_number=ladder_number))
                except Exception, e:
                    log.warning("Couldn't get arena page, continuing... ERROR: " + str(e))
                    continue
                
                teams = self._parse_arena_file(StringIO.StringIO(source), site, get_characters=get_characters)
                all_teams.append(teams)
                
        return WoWSpyderLib.merge(all_teams)
            
    def _parse_arena_file(self, xml_file_object, site, get_characters=False):
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
            except Exception, e:
                log.warning("Couldn't get team " + name + " continuing. ERROR: " + str(e))
                continue
            else:
                teams.append(team)
            
        return teams
        
class ArenaParserTests(unittest.TestCase):
    def setUp(self):
        self.us_realm = u"Blackwater Raiders"
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
        teams = self.ap.get_arena_teams(self.us_battlegroup, self.us_realm, \
            u"us", get_characters=False, ladders=[2], max_pages=1)

    def testGetTeamsAndCharacters(self):
        from guppy import hpy
        h = hpy()
        print h.heap()
        teams = self.ap.get_arena_teams(self.us_battlegroup, self.us_realm, \
            u"us", get_characters=True, ladders=[2], max_pages=1)
        h = hpy()
        print h.heap()
        

if __name__ == '__main__':
    unittest.main()