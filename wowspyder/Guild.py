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
from sqlalchemy.orm import relation, backref
from Battlegroup import Realm
import XMLDownloader
import re
import StringIO
import Preferences

log = Logger.log()
database = Database.Database()
Base = database.get_base()

class GuildParser:
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        '''Initialize the guild parser.'''
        self.database = database
        self.session = self.database.session
        Base.metadata.create_all(self.database.engine)
        self.prefs = Preferences.Preferences()
        
        self.downloader = downloader
        
        if self.downloader is None:
            self.downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)
                
    def get_guild(self, name, realm, site, get_characters=True):
        if name is None or name == "": 
            return None
        
        guild = None
        
        if not self.prefs.refresh_all:
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
        self.database.insert(guild)
         
        # cflewis | 2009-03-28 | Now need to put in guild's characters
        if get_characters:
            log.debug("Parsing guild character")
            characters = self.parse_guild_characters(name, realm, site)
            guild.characters.append(characters)
        else:
            log.debug("Not parsing guild characters")

        # cflewis | 2009-03-28 | SQLAlchemy wasn't actually committing,
        # so I'm merging twice, and it seems to bite now.
        self.database.insert(guild)

        return guild
         
    def parse_guild_characters(self, name, realm, site):
        source = self.downloader.download_url( \
            WoWSpyderLib.get_guild_url(name, realm, site))
        max_pages = WoWSpyderLib.get_max_pages(source)
        character_list = []
    
        for page in range(1, (max_pages + 1)):
            log.debug(battlegroup + " " + realm + \
                ": Downloading guild page " + str(page) + " of " \
                + str(max_pages))
            
            source = self.downloader.download_url( \
                WoWSpyderLib.get_guild_url(name, realm, site, page=page))
            
            character_list.append(self.parse_guild_file(StringIO.StringIO(source), site))
            
        return WoWSpyderLib.merge(character_list)
            
    def parse_guild_file(self, source, site):
        pass
        
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
    
    characters = relation("Character", backref=backref("guild_object"))
    
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


if __name__ == '__main__':
    unittest.main()
