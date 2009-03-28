#!/usr/bin/env python
# encoding: utf-8
"""
Character.py

Created by Chris Lewis on 2009-03-28.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
from xml.dom import minidom
import Database
import Logger
import datetime
import time
import WoWSpyderLib
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
import Guild
import Preferences

log = Logger.log()
database = Database.Database()
Base = database.get_base()

class CharacterParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the team parser.'''
        self.database = database
        self.session = self.database.session
        Base.metadata.create_all(self.database.engine)
        self.prefs = Preferences.Preferences()
        
        if downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
                
        self.gp = Guild.GuildParser(downloader=downloader)
        
    def get_character(self, name, realm, site):
        character = None
        
        if not self.prefs.refresh_all:
            character = self.session.query(Character).get((name, realm, site))
        
        if not character:      
            source = self.downloader.download_url(\
                WoWSpyderLib.get_character_sheet_url(name, realm, site))
            character = self.parse_character(StringIO.StringIO(source), site)
            
        return character
        
    def parse_character(self, xml_file_object, site):
        xml = minidom.parse(xml_file_object)
        character_nodes = xml.getElementsByTagName("character")
        character_node = character_nodes[0]
        
        name = character_node.attributes["name"].value
        realm = character_node.attributes["realm"].value
        site = site
        level = character_node.attributes["level"].value
        character_class = character_node.attributes["class"].value
        faction = character_node.attributes["faction"].value
        gender = character_node.attributes["gender"].value
        race = character_node.attributes["race"].value
        
        # cflewis | 2009-03-28 | Get characters is false to "stub" the Guild
        # into the DB in order to satisfy the foreign key. However, creating
        # guilds usually results in a parse of the characters of the guild,
        # which causes a creation loop.
        guild = None
        guild_rank = None
        guild_name = None
        
        if character_node.attributes["guildName"].value != "" or \
            character_node.attributes["guildName"].value is not None:
            guild = self.gp.get_guild(character_node.attributes["guildName"].value, \
                realm, site, get_characters=False)
            
            if guild is not None:
                guild_rank = self.gp.get_guild_rank(guild.name, realm, site, name)
                guild_name = guild.name
                
        last_modified_string = character_node.attributes["lastModified"].value
        last_modified = datetime.datetime(\
            *time.strptime(last_modified_string, "%B %d, %Y")[0:5])
        character = Character(name, realm, site, level, character_class, faction, \
            gender, race, guild_name, guild_rank, last_modified)
        log.debug("Creating character " + name)
        self.database.insert(character)
                
        return character


class Character(Base):
    __table__ = Table("CHARACTER", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("level", Integer()),
        Column("character_class", Enum([u"Druid", u"Hunter", u"Mage", u"Paladin", \
            u"Priest", u"Rogue", u"Shaman", u"Warlock", u"Warrior", \
            u"Death Knight"])),
        Column("faction", Enum([u"Alliance", u"Horde"])),
        Column("gender", Enum([u"Male", u"Female"])),
        Column("race", Enum([u"Human", u"Dwarf", u"Night Elf", u"Gnome", \
            u"Draenei", u"Orc", u"Undead", u"Tauren", u"Troll", \
            u"Blood Elf"])),
        Column("guild", Unicode(100), ForeignKey("GUILD.name")),
        Column("guild_rank", Integer()),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_modified", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime(), index=True),
        ForeignKeyConstraint(['realm', 'site'], ['REALM.name', 'REALM.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
        
    def __init__(self, name, realm, site, level, character_class, faction, gender, \
            race, guild, guild_rank, last_modified=None, last_refresh=None):
        self.name = name
        self.realm = realm
        self.site = site
        self.level = level
        self.character_class = character_class
        self.faction = faction
        self.gender = gender
        self.race = race
        self.guild = guild
        self.guild_rank = guild_rank
        self.last_modified = last_modified
        self.last_refresh = last_refresh
        
    def __repr__(self):
        return unicode("<Character('%s','%s','%s','%s','%s')>" % (self.name, \
            self.realm, self.site, self.race, self.character_class))
    
    @property
    def url(self):
        return WoWSpyderLib.get_team_url(self.name, self.realm, self.site, \
                self.size)
                
class CharacterParserTests(unittest.TestCase):
    def setUp(self):
        self.cp = CharacterParser()
        self.gp = Guild.GuildParser()
        
    def testCharacter(self):
        c = self.cp.get_character(u"Moulin", u"Ravenholdt", u"us")
        
    def testInsertGuild(self):
        self.gp.get_guild(u"Meow", u"Cenarius", u"us", get_characters=False)

if __name__ == '__main__':
    unittest.main()
