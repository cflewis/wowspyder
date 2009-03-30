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
from GuildCharacter import Guild, Character
import GuildCharacter
from Battlegroup import Realm
import XMLDownloader
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    DateTime, Unicode, Integer
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref
from Enum import Enum
import urllib2
import StringIO
import Preferences

log = Logger.log()

Base = Database.get_base()

class TeamParser(object):
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the team parser.'''
        self.downloader = downloader
        
        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
        
        self._session = Database.session
        Base.metadata.create_all(Database.engine)
        self._prefs = Preferences.Preferences()
        
        self._cp = GuildCharacter.CharacterParser(downloader=self.downloader)
        
    def get_team(self, name, realm, site, size=None, get_characters=True):
        """Returns a team object. Setting get_characters to False will
        cause characters in the team to not be created. This means you
        can just get the team name quickly, but is most probably
        not what you want to do.
        
        """
        team = None
        
        if not self._prefs.refresh_all:
            # cflewis | 2009-03-28 | This won't check if there are the right
            # characters in the team
            team = self._session.query(Team).get((name, realm, site))
        
        if not team:
            if not size: raise NameError("No team on that PK, " + \
                "need size to create new team.")         
            source = self.downloader.download_url(\
                WoWSpyderLib.get_team_url(name, realm, site, size))
            team = self.__parse_team(StringIO.StringIO(source), site, get_characters=get_characters)
            
        return team
        
    def __parse_team(self, xml_file_object, site, get_characters=True):
        """Parse a team and add its characters if necessary."""
        xml = minidom.parse(xml_file_object)
        team_nodes = xml.getElementsByTagName("arenaTeam")
        team_node = team_nodes[0]
        
        try:
            name = team_node.attributes["name"].value
            realm = team_node.attributes["realm"].value
            size = int(team_node.attributes["teamSize"].value)
            faction = team_node.attributes["faction"].value
        except KeyError, e:
            log.warning("No team here")
            return None
        
        team = Team(name, realm, site, size, faction)
        log.info("Creating team " + unicode(team).encode("utf-8"))
        
        if get_characters:
            characters = self.__parse_team_characters(StringIO.StringIO(xml_file_object.getvalue()), site)
        
            # cflewis | 2009-03-28 | Add the characters to the team
            for character in characters:
                team.characters.append(character)
        
        # cflewis | 2009-03-28 | Merge to update the characters added
        Database.insert(team)

        return team
        
    def __parse_team_characters(self, xml_file_object, site):
        """Parse a list of characters associated with a team"""
        xml = minidom.parse(xml_file_object)
        character_nodes = xml.getElementsByTagName("character")
        characters = []
        
        for character_node in character_nodes:
            name = character_node.attributes["name"].value
            realm = character_node.attributes["realm"].value
            
            try:
                character = self._cp.get_character(name, realm, site)
                characters.append(character)
            except Exception, e:
                log.warning("Couldn't get character " + name + ", continuing...")
                continue
            
        return characters


team_characters = Table("TEAM_CHARACTERS", Base.metadata,
    Column("realm", Unicode(100)),
    Column("site", Unicode(2)),
    Column("team_name", Unicode(100)),
    Column("character_name", Unicode(100)),
    ForeignKeyConstraint(['team_name','realm', 'site'], ['TEAM.name', \
        'TEAM.realm', 'TEAM.site']),
    ForeignKeyConstraint(['character_name','realm', 'site'], ['CHARACTER.name', \
        'CHARACTER.realm', 'CHARACTER.site']))


class Team(Base):
    """A team."""
    __table__ = Table("TEAM", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("size", Integer()),
        Column("faction", Enum([u"Alliance", u"Horde"])),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime(), index=True),
        ForeignKeyConstraint(['realm', 'site'], ['REALM.name', 'REALM.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    realm_object = relation(Realm, backref=backref("teams"))
    characters = relation(Character, secondary=team_characters, backref=backref("teams"))
    
    def __init__(self, name, realm, site, size, faction, last_refresh=None):
        self.name = name
        self.realm = realm
        self.site = site
        self.size = size
        self.faction = faction
        self.last_refresh = last_refresh
        
    def __repr__(self):
        return unicode("<Team('%s','%s','%s','%d')>" % (self.name, \
            self.realm, self.site, self.size))
    
    @property
    def url(self):
        return WoWSpyderLib.get_team_url(self.name, self.realm, self.site, \
                self.size)
                
class TeamParserTests(unittest.TestCase):
    def setUp(self):
        self.tp = TeamParser()
        self.test_team = self.tp.get_team(u"Party Like Rockstars", u"Cenarius", 
            u"us", 5)
            
    def testRelation(self):
        log.debug("Realm: " + str(self.test_team.realm_object))
        characters = self.test_team.characters
        log.debug("Characters: " + str(self.test_team.characters))
        self.assertTrue(characters)
        
    def testRepitition(self):
        test_team2 = self.tp.get_team(u"Party Like Rockstars", u"Cenarius", 
            u"us", 5)
        
    # def testPrimaryKey(self):
    #     self.assertTrue(self.tp.get_team(u"Party Like Rockstars", u"Cenarius", u"us"))


if __name__ == '__main__':
    unittest.main()
