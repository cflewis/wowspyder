#!/usr/bin/env python
# encoding: utf-8
"""
GuildCharacter.py

Created by Chris Lewis on 2009-03-28.
Copyright (c) 2009 Chris Lewis. All rights reserved.

This file is an amalgmation of Guilds and Characters. The functionality
became so tightly wound (characters could create guilds, guilds could
create characters) that Python tripped up on circular imports. This
file alleivates that problem. This is not to say I am happy about it.
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
import Preferences
import re

log = Logger.log()

Base = Database.get_base()

class CharacterParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the team parser.'''
        
        self.session = Database.session
        Base.metadata.create_all(Database.engine)
        self.prefs = Preferences.Preferences()
        self.downloader = downloader
        
        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
                        
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
        gp = GuildParser(downloader=self.downloader)
        
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
            guild = gp.get_guild(character_node.attributes["guildName"].value, \
                realm, site, get_characters=False)
            
            if guild is not None:
                guild_rank = gp.get_guild_rank(guild.name, realm, site, name)
                guild_name = guild.name
        
        # cflewis | 2009-03-28 | If the Armory fails out on us, this is the
        # only data that isn't returned (on the main sheet, anyway)
        # so we should check for it
        last_modified = None

        try:
            last_modified_string = character_node.attributes["lastModified"].value
            last_modified = datetime.datetime(\
                *time.strptime(last_modified_string, "%B %d, %Y")[0:5])
        except KeyError, e:
            # cflewis | 2009-03-28 | Armory must be down. Oh well.
            pass
        
        character = Character(name, realm, site, level, character_class, faction, \
            gender, race, guild_name, guild_rank, last_modified)
        log.debug("Creating character " + name)
        Database.insert(character)
                
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
        
    def testCharacter(self):
        c = self.cp.get_character(u"Moulin", u"Ravenholdt", u"us")
        
class GuildParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the guild parser.'''

        self.session = Database.session
        Base.metadata.create_all(Database.engine)
        self.prefs = Preferences.Preferences()
        self.downloader = downloader

        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)        

    def get_guild(self, name, realm, site, get_characters=True):
        if name is None or name == "": 
            return None

        guild = None

        # cflewis | 2009-03-28 | Get characters is only false when we're
        # worried about circular referencing from character creation, 
        # so we don't need to be concerned with finding fresh characters
        if not self.prefs.refresh_all or get_characters is False:
            guild = self.session.query(Guild).get((name, realm, site))

        if not guild:
            log.debug("Didn't find guild, creating...")     
            source = self.downloader.download_url(\
                 WoWSpyderLib.get_guild_url(name, realm, site))
            guild = self.parse_guild(StringIO.StringIO(source), site, get_characters)

        return guild

    def parse_guild(self, xml_file_object, site, get_characters=True):
        xml = minidom.parse(xml_file_object)
        guild_nodes = xml.getElementsByTagName("guildKey")
        guild_node = guild_nodes[0]

        name = guild_node.attributes["name"].value
        realm = guild_node.attributes["realm"].value
        site = site
        guild = Guild(name, realm, site)
        log.debug("Inserting guild " + guild.name)
        Database.insert(guild)

        # cflewis | 2009-03-28 | Now need to put in guild's characters
        if get_characters:
            log.debug("Parsing guild character")
            characters = self.parse_guild_characters(name, realm, site)
            guild.characters = characters
        else:
            log.debug("Not parsing guild characters")

        # cflewis | 2009-03-28 | SQLAlchemy wasn't actually committing,
        # so I'm merging twice, and it seems to bite now.
        Database.insert(guild)

        return guild

    def parse_guild_characters(self, name, realm, site):
        source = self.downloader.download_url( \
            WoWSpyderLib.get_guild_url(name, realm, site))
        max_pages = WoWSpyderLib.get_max_pages(source)
        character_list = []

        for page in range(1, (max_pages + 1)):
            log.debug(name + " " + realm + \
                ": Downloading guild page " + str(page) + " of " \
                + str(max_pages))

            source = self.downloader.download_url( \
                WoWSpyderLib.get_guild_url(name, realm, site, page=page))

            character_list.append(self.parse_guild_file(StringIO.StringIO(source), site))

        return WoWSpyderLib.merge(character_list)

    def parse_guild_file(self, xml_file_object, site):
        xml = minidom.parse(xml_file_object)
        guild_nodes = xml.getElementsByTagName("guildKey")
        guild_node = guild_nodes[0]
        cp = CharacterParser(downloader=self.downloader)
        
        realm = guild_node.attributes["realm"].value
        
        character_nodes = xml.getElementsByTagName("character")
        characters = []
        
        for character_node in character_nodes:
            name = character_node.attributes["name"].value
            character = cp.get_character(name, realm, site)
            characters.append(character)
            
        return characters

    def get_guild_rank_from_character(self, character):
        return self.get_guild_rank(character.guild, character.realm, \
            character.site, character.name)

    def get_guild_rank(self, guild_name, realm, site, character_name):
        source = self.downloader.download_url( \
            WoWSpyderLib.get_guild_url(guild_name, realm, site))
        max_pages = WoWSpyderLib.get_max_pages(source)

        for page in range(1, (max_pages + 1)):
            source = self.downloader.download_url( \
                WoWSpyderLib.get_guild_url(guild_name, realm, site, page=page))

            guild_rank_search = re.search("name=\"" + character_name + \
                "\".*rank=\"(\d*)\"", source)
            if guild_rank_search:
                return int(guild_rank_search.group(1))

        return None


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

    characters = relation(Character, backref=backref("guild_object"))

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
        log.debug("Returning URL for " + self.name + "," + self.realm + "," + self.site)

        return WoWSpyderLib.get_guild_url(self.name, self.realm, self.site)

class GuildParserTests(unittest.TestCase):
    def setUp(self):
        self.gp = GuildParser()

    def testGuildRank(self):
        self.assertEquals(self.gp.get_guild_rank(u"Meow", u"Cenarius", u"us", "Snicker"), 1)

    def testGuildRank2(self):
        self.assertEquals(self.gp.get_guild_rank(u"Meow", u"Cenarius", u"us", "Snoozer"), 4)

    def testInsertGuildNoCharacters(self):
        self.gp.get_guild(u"Meow", u"Cenarius", u"us", get_characters=False)

    def testInsertGuildCharacters(self):
        self.gp.get_guild(u"Beasts of Unusual Size", u"Ravenholdt", u"us", \
            get_characters=True)

if __name__ == '__main__':
    unittest.main()