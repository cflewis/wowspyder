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
from Parser import Parser
import re

log = Logger.log()

Base = Database.get_base()

class TeamParser(Parser):
    def __init__(self, downloader=None):
        '''Initialize the team parser.'''
        log.debug("Creating TeamParser with " + str(downloader))
        Parser.__init__(self, downloader=downloader)
        self._cp = GuildCharacter.CharacterParser(downloader=self._downloader)        
        
    def _check_download(self, source, exception):
        if exception:
            log.error("Unable to download team file")
            raise exception
            
        if re.search("arenaTeam.*?teamUrlEscape=\"\"", source):
            log.error("Team was invalid or not returned")
            raise IOError("Team requested was invalid or not returned")
        
        return source
        
    def get_team(self, name, realm, site, size=None, get_characters=False, cached=False):
        """Returns a team object. Setting get_characters to True will
        cause characters in the team to be created at the same time. This is
        slower, but likely what you will want.
        
        Setting cached to True will return the cached version of the team, 
        if you're sure it's already in the database.
        
        """
        team = self._session.query(Team).get((name, realm, site))
        
        if cached and team:
            return team
        
        if not team and not size: raise NameError("No team on that PK, " + \
            "need size to create new team.")
            
        log.debug("Getting team...")
            
        # cflewis | 2009-04-02 | If downloading fails, the whole team
        # couldn't be found, so the exception should propagate up.
        source = self._download_url(\
            WoWSpyderLib.get_team_url(name, realm, site, size))
        team = self._parse_team(StringIO.StringIO(source), site, get_characters=get_characters)
        
        return team
        
    def _parse_team(self, xml_file_object, site, get_characters=False):
        """Parse a team and add its characters if necessary."""
        log.debug("Parsing team...")
        xml = minidom.parse(xml_file_object)
        team_nodes = xml.getElementsByTagName("arenaTeam")
        team_node = team_nodes[0]
        
        name = team_node.attributes["name"].value
        realm = team_node.attributes["realm"].value
        size = int(team_node.attributes["teamSize"].value)
        faction = team_node.attributes["faction"].value
        
        team = Team(name, realm, site, size, faction)
        log.info("Creating team " + unicode(team).encode("utf-8"))
        Database.insert(team)
        
        if get_characters:
            characters = self._parse_team_characters(StringIO.StringIO(xml_file_object.getvalue()), site)
        
            # cflewis | 2009-03-28 | Add the characters to the team
            for character in characters:
                # cflewis | 2009-04-08 | This memory leaks
                team.characters.append(character)
                log.debug("Adding " + character.name + " to team " + name)
                # cflewis | 2009-04-08 | Can't seem to get this to work
                # for unicode. Arghh!
                #Database.engine.execute(team_characters.insert(), \
                #    realm=unicode(realm), \
                #    site=site, team_name=unicode(name), \
                #    character_name=unicode(character.name))
                        
        # cflewis | 2009-03-28 | Merge to update the characters added
        Database.insert(team)
        # cflewis | 2009-04-08 | Doing this prevents leaks BUT ONLY
        # IF TEAM IS NOT REINSERTED INTO THE DATABASE!
        # cflewis | 2009-05-16 | This might also cause an exception if reenabled
        # as it intentionally orphans the old objects.
        team.characters = []
        #Database.insert(team)

        return team
        
    def _parse_team_characters(self, xml_file_object, site):
        """Parse a list of characters associated with a team"""
        log.debug("Parsing team characters...")
        xml = minidom.parse(xml_file_object)
        character_nodes = xml.getElementsByTagName("character")
        characters = []
                
        for character_node in character_nodes:
            log.debug("Looping through character nodes")
            name = character_node.attributes["name"].value
            realm = character_node.attributes["realm"].value
                        
            try:
                log.debug("Getting character...")
                # cflewis | 2009-04-02 | This is *ridiculous*, but
                # it simply won't work outside of this for loop.
                # No idea what to do.
                character = self._cp.get_character(name, realm, site)
            except Exception, e:
                log.warning("Couldn't get character " + name + ", continuing. ERROR: " + str(e))
                continue
            else:
                characters.append(character)
            
        return characters


team_characters = Table("TEAM_CHARACTERS", Base.metadata,
    Column("realm", Unicode(100)),
    Column("site", Unicode(2)),
    Column("team_name", Unicode(100)),
    Column("character_name", Unicode(100)),
    ForeignKeyConstraint(['team_name','realm', 'site'], ['TEAM.name', \
        'TEAM.realm', 'TEAM.site']),
    ForeignKeyConstraint(['character_name','realm', 'site'], ['CHARACTER.name', \
        'CHARACTER.realm', 'CHARACTER.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
)


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
        log.debug("%s, %s, %s, %s" % (name, realm, site, str(size)))
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
                
    def get_characters(self):
        tp = TeamParser()
        
        if characters is None:
            team = self.refresh(get_characters=True)
            assert team == self
        
        return self.characters

    def refresh(self, get_characters=False):
        """Refresh this team from the Armory"""
        tp = TeamParser()

        try:
            return_team = tp.get_team(self.name, self.realm, self.site, \
                get_characters=get_characters, cached=False)
        except Exception, e:
            log.warning("Couldn't refresh team")

        assert return_team == self

        return self
                
class TeamParserTests(unittest.TestCase):
    def setUp(self):
        self.tp = TeamParser()
    
    # def testCharacterTeam(self):
    #     team = self.tp.get_team(u"JUST DIED IN ONE HIT", u"Mug'Thol", 
    #         u"us", 2, get_characters=False)
    #         
    def testNoCharacterTeam(self):
        team = self.tp.get_team(u"JUST DIED IN ONE HIT", u"Mug'Thol", 
            u"us", 2, get_characters=True)
    
    # def testRelation(self):
    #     log.debug("Realm: " + str(self.test_team.realm_object))
    #     characters = self.test_team.characters
    #     log.debug("Characters: " + str(self.test_team.characters))
    #     self.assertTrue(characters)
        
        
    # def testPrimaryKey(self):
    #     self.assertTrue(self.tp.get_team(u"Party Like Rockstars", u"Cenarius", u"us"))


if __name__ == '__main__':
    unittest.main()
