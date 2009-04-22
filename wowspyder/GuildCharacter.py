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
from Parser import Parser
from Item import ItemParser

log = Logger.log()

Base = Database.get_base()

class CharacterParser(Parser):
    """A class to parse the character sheets from the Armory and return
    character objects. 
    
    Returning a character object will only *stub out* the
    guild, and not recursively grab the guild, as other parser classes. This
    is because defining the guild at the same time would define characters
    which would create a loop.
    
    """
    def __init__(self, downloader=None):
        '''Initialize the character parser.'''
        log.debug("Creating character parser with downloader " + str(downloader))
        Parser.__init__(self, downloader=downloader)
        self._gp = GuildParser(downloader=self._downloader)
        self._ip = ItemParser(downloader=self._downloader)
        Base.metadata.create_all(Database.engine)
        
    def _check_download(self, source, exception):
        if exception:
            log.error("Unable to download file for character")
            raise exception
            
        if re.search("errCode=\"noCharacter\"", source):
            log.error("Character was invalid or not returned")
            raise IOError("Character requested was invalid or not returned")
            
        return source
                        
    def get_character(self, name, realm, site, cached=False):
        """Return a character object. This only stubs the guild, which means
        the guild won't be populated with characters."""
        log.debug("Getting character " + name + "...")
        
        character = self._session.query(Character).get((name, realm, site))
        
        # cflewis | 2009-04-11 | Check if a character is actually updated
        # on the armory. If not, return the database version anyway.
        if character and (cached == True or character.is_updated_on_armory() == False):
            return character            
        
        source = self._download_url(\
            WoWSpyderLib.get_character_sheet_url(name, realm, site))
        character = self._parse_character(StringIO.StringIO(source), site)
            
        return character
        
    def _parse_character(self, xml_file_object, site):
        """Parse the XML of a character sheet from the Armory."""
        log.debug("Parsing character...")
        
        xml = minidom.parse(xml_file_object)
        character_nodes = xml.getElementsByTagName("character")
        
        try:
            character_node = character_nodes[0]
        except IndexError, e:
            log.debug("No character found in the XML")
            raise 
        
        name = character_node.attributes["name"].value
        realm = character_node.attributes["realm"].value
        site = site
        level = character_node.attributes["level"].value
        character_class = character_node.attributes["class"].value
        faction = character_node.attributes["faction"].value
        gender = character_node.attributes["gender"].value
        race = character_node.attributes["race"].value
        
        # cflewis | 2009-03-28 | Get characters is false to "stub" the Guild
        # into the DB in order to satisfy the foreign key. Creating
        # guilds usually results in a parse of the characters of the guild,
        # which causes a creation loop.
        guild = None
        guild_rank = None
        guild_name = None
        
        log.debug("Working on guild ranks...")
        
        # cflewis | 2009-04-02 | Check if character is in a guild at all
        if character_node.attributes["guildName"].value != "" or \
            character_node.attributes["guildName"].value is not None:
            
            try:
                guild = self._gp.get_guild(character_node.attributes["guildName"].value, \
                    realm, site, get_characters=False, cached=True)
            except Exception, e:
                log.warning("Couldn't get guild for " + name + ". ERROR: " + str(e))
            else:
                try:
                    guild_rank = self._gp.get_guild_rank(guild.name, realm, site, name)
                except Exception, e:
                    log.warning("Couldn't get guild rank. ERROR: " + str(e))
                else:
                    guild_name = guild.name
        
        # cflewis | 2009-04-02 | Last modified continues to be weird and
        # I can't track this bug down!
        last_modified = None
        
        log.debug("Guilds done, working on last modified date...")

        try:
            last_modified_string = character_node.attributes["lastModified"].value
        except KeyError, e:
            log.warning("Couldn't get last modified date. ERROR: " + str(e))
            last_modified = None
        else:
            last_modified = WoWSpyderLib.convert_last_modified_to_datetime(last_modified_string)
            log.debug("Last modified date is " + str(last_modified))
            if last_modified.year < 2008:
                log.warning("Last modified year was broken, fixing it to this year")
                # cflewis | 2009-03-30 | The Armory has been returning strange
                # years intermittently, not replicable when I manually visit
                # the page. I'll set the year to what the current year is.
                last_modified.replace(year=datetime.datetime.now().year)
            else:
                log.debug("Last modified year is " + str(last_modified.year) + " so continuing")
        
        log.debug("Character done, getting items...")
        
        items = []
        
        for x in range(0, 19):
            items.append(CharacterItem(name, realm, site, x, None))
        
        item_nodes = xml.getElementsByTagName("item")
        
        for item_node in item_nodes:
            item = self._ip.get_item(item_node.attributes["id"].value)
            items[int(item_node.attributes["slot"].value)] = CharacterItem(name, realm, site, \
                int(item_node.attributes["slot"].value), item.item_id)

        talents1 = None
        talents2 = None
        
        try:    
            talents = self._get_character_talents(name, realm, site)
        except Exception, e:
            log.warning("Couldn't get talents for " + name + " " + realm + \
                " " + site + ". ERROR: " + str(e))
        else:
            talents1 = talents[0]
            talents2 = talents[1]
            log.debug("Talents 1 is " + str(talents1))
            log.debug("Talents 2 is " + str(talents2))
        
        character = Character(name, realm, site, level, character_class, faction, \
            gender, race, guild_name, guild_rank, last_modified=last_modified, \
            items=items, talents1=talents1, talents2=talents2)
        log.info("Creating character " + unicode(character).encode("utf-8"))
        Database.insert(character)
        
        statistics = []
        
        try:
            statistics = self._get_character_statistics(name, realm, site)
        except Exception, e:
            log.warning("Couldn't get statistics for " + name + " " + realm + \
                " " + site + ". ERROR: " + str(e))
        
        for statistic in statistics:
            character.statistics.append(statistic)
                
        Database.insert(character)
                
        return character
        
        
    def _get_character_talents(self, name, realm, site):
        source = self._download_url(\
            WoWSpyderLib.get_character_talents_url(name, realm, site))
        talents = self._parse_character_talents(StringIO.StringIO(source))
            
        return talents
        
    def _parse_character_talents(self, xml_file_object):
        """Parse the XML of a talents character sheet from the Armory."""
        log.debug("Parsing character talents...")
        
        xml = minidom.parse(xml_file_object)
        talent_tree_nodes = xml.getElementsByTagName("talentSpec")
        talents = []
        
        for node in talent_tree_nodes:
            talents.append(node.attributes["value"].value)
            
        if len(talents) == 1:
            talents.append(None)
                
        return talents
        
    def _get_character_statistics(self, name, realm, site):
        urls = WoWSpyderLib.get_character_statistics_urls(name, realm, site)
        statistics = []
        
        for url in urls:
            source = self._download_url(url)
            statistics.append(self._parse_character_statistics(StringIO.StringIO(source), name, realm, site))
            
        return WoWSpyderLib.merge(statistics)
            
            
    def _parse_character_statistics(self, xml_file_object, name, realm, site):
        """Parse the XML of a statistics character sheet from the Armory."""
        log.debug("Parsing character statistics...")
        xml = minidom.parse(xml_file_object)
        statistics = []
        statistic_nodes = xml.getElementsByTagName("statistic")

        for statistic_node in statistic_nodes:
            try:
                statistic = statistic_node.attributes["name"].value
            except KeyError, e:
                # cflewis | 2009-04-07 | This wasn't a statistic node at all
                # or a blank one, like <statistic/>
                continue
                
            quantity = statistic_node.attributes["quantity"].value
            
            if quantity == "--": quantity = 0
            
            highest = None
            
            try:
                highest = statistic_node.attributes["highest"].value
            except KeyError, e:
                pass
            
            statistic = CharacterStatistic(name, realm, site, \
                statistic, quantity, highest)
            Database.insert(statistic)
            statistics.append(statistic)
                
        return statistics

class CharacterStatistic(Base):
    """A statistic on a character."""
    __table__ = Table("CHARACTER_STATISTIC", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("statistic", Unicode(100), primary_key=True),
        Column("quantity", Unicode(100)),
        Column("highest", Unicode(100)),
        ForeignKeyConstraint(['name','realm', 'site'], ['CHARACTER.name', 'CHARACTER.realm', 'CHARACTER.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )

    def __init__(self, name, realm, site, statistic, quantity, highest):
        self.name = name
        self.realm = realm
        self.site = site
        self.statistic = statistic
        self.quantity = quantity
        self.highest = highest

    def __repr__(self):
        return unicode("<CharacterStatistic('%s','%s','%s','%s','%s')>" % (self.name, \
            self.realm, self.site, self.statistic, self.value))
            

class CharacterItem(Base):
    """An item on a character."""
    __table__ = Table("CHARACTER_ITEM", Base.metadata,
        Column("name", Unicode(100), primary_key=True),
        Column("realm", Unicode(100), primary_key=True),
        Column("site", Unicode(2), primary_key=True),
        Column("slot", Integer(), primary_key=True, autoincrement=False),
        Column("item_id", Integer(), ForeignKey("ITEM.item_id")),
        ForeignKeyConstraint(['name','realm', 'site'], ['CHARACTER.name', 'CHARACTER.realm', 'CHARACTER.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )

    def __init__(self, name, realm, site, slot, item_id):
        self.name = name
        self.realm = realm
        self.site = site
        self.slot = slot
        self.item_id = item_id

    def __repr__(self):
        return unicode("<Item('%s','%s','%s','%s','%d')>" % (self.name, \
            self.realm, self.site, self.slot, self.item_id))


class Character(Base):
    """A WoW Character."""
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
        Column("talents_1", Unicode(100)),
        Column("talents_2", Unicode(100)),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_modified", DateTime()),
        Column("last_refresh", DateTime(), default=datetime.datetime.now(), index=True),
        ForeignKeyConstraint(['realm', 'site'], ['REALM.name', 'REALM.site']),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )
    
    statistics = relation(CharacterStatistic, backref="character")
    items = relation(CharacterItem, backref="character")
        
    def __init__(self, name, realm, site, level, character_class, faction, gender, \
            race, guild, guild_rank, items=None, talents1=None, \
            talents2=None, last_modified=None, last_refresh=None):            
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
        self.talents_1 = talents1
        self.talents_2 = talents2
        
        if last_refresh:
            if last_refresh.year < datetime.datetime.now().year:
                log.warning("Last refresh year was broken, removing it to None.")
                # cflewis | 2009-03-30 | The Armory has been returning strange
                # years intermittently, not replicable when I manually visit
                # the page. I'll set the year to what the current year is.
                last_refresh = None
                
        self.last_refresh = last_refresh
        
        if items:
            self.items = items
        
    def __repr__(self):
        return unicode("<Character('%s','%s','%s','%s','%s')>" % (self.name, \
            self.realm, self.site, self.race, self.character_class))      
    
    @property
    def url(self):
        return WoWSpyderLib.get_character_sheet_url(self.name, self.realm, self.site)
                
    def refresh(self):
        cp = CharacterParser()
        
        try:
            return_character = cp.get_character(self.name, self.realm, self.site, \
                cached=False)
        except Exception, e:
            log.warning("Couldn't find character again")
            
        return return_character
        
    @property
    def last_modified_on_armory(self):    
        # cflewis | 2009-04-11 | It's safe to cache because there's no way
        # the lifetime of a character object will exceed that of an armory
        # refresh.
        downloader = XMLDownloader.XMLDownloader()
        source = downloader.download_url(self.url)

        try:
            if self._last_modified_on_armory != None:
                return self._last_modified_on_armory
        except AttributeError:        
            try:
                armory_date_string = re.search("lastModified=\"(.*?)\"", source).group(1)
            except Exception, e:
                log.debug("Couldn't find last modified, returning what I had")
                return self.last_modified
            else:
                self._last_modified_on_armory = \
                    WoWSpyderLib.convert_last_modified_to_datetime(armory_date_string)
                log.debug("Saved last modified on armory as " + str(self._last_modified_on_armory))
                return self._last_modified_on_armory
        
    def is_updated_on_armory(self):
        if self.last_modified_on_armory > self.last_modified:
            log.debug("Character has been updated on the armory")
            return True
            
        log.debug("Character is not updated on the armory")
        return False

class CharacterParserTests(unittest.TestCase):
    def setUp(self):
        self.cp = CharacterParser()
        self.c = self.cp.get_character(u"Moulin", u"Ravenholdt", u"us")
    def testCharacterModifiedDate(self):
        self.assertFalse(self.c.is_updated_on_armory())
    
        
class GuildParser(Parser):
    """A parser to return guilds. By default, returning a guild will
    also fill out the characters within it.
    
    """
    def __init__(self, downloader=None):
        '''Initialize the guild parser.'''
        Parser.__init__(self, downloader=downloader)
        Base.metadata.create_all(Database.engine)
        
    def _check_download(self, source, exception):
        if exception:
            log.error("Unable to download file for guild")
            raise exception
            
        if re.search("guildInfo/", source):
            log.error("Guild was invalid or not returned")
            raise IOError("Guild requested was invalid or not returned")
            
        return source

    def get_guild(self, name, realm, site, get_characters=False, cached=False):
        """Get a guild. Setting get_characters=False will disable the
        behavior that causes the guild characters to also be created. You
        may want to do this for speed increases.
        
        """
        if name is None or name == "": 
            return None

        guild = self._session.query(Guild).get((name, realm, site))

        if cached and guild:
            return guild

        # cflewis | 2009-04-02 | If the downloading fails, the whole guild
        # couldn't be found, so the exception should propagate up.
        source = self._download_url(\
            WoWSpyderLib.get_guild_url(name, realm, site))
        guild = self._parse_guild(StringIO.StringIO(source), site, get_characters=get_characters)

        return guild
        

    def _parse_guild(self, xml_file_object, site, get_characters=False):
        """Parse a guild page."""
        xml = minidom.parse(xml_file_object)
        guild_nodes = xml.getElementsByTagName("guildHeader")
        guild_node = guild_nodes[0]

        name = guild_node.attributes["name"].value
        realm = guild_node.attributes["realm"].value
        site = site
        guild = Guild(name, realm, site)
        log.info("Creating guild " + unicode(guild).encode("utf-8"))
        Database.insert(guild)

        # cflewis | 2009-03-28 | Now need to put in guild's characters
        if get_characters:
            log.debug("Parsing guild character")
            characters = self._parse_guild_characters(name, realm, site)
            #guild.characters = characters
        else:
            log.debug("Not parsing guild characters")

        # cflewis | 2009-03-28 | SQLAlchemy wasn't actually committing,
        # so I'm merging twice, and it seems to bite now.
        Database.insert(guild)

        return guild

    def _parse_guild_characters(self, name, realm, site):
        """Page through a guild, creating characters."""
        character_list = []

        log.debug(name + " " + realm + ": Downloading guild page")

        source = self._download_url( \
            WoWSpyderLib.get_guild_url(name, realm, site, page=1))

        character_list.append(self._parse_guild_file(StringIO.StringIO(source), site))

        return WoWSpyderLib.merge(character_list)

    def _parse_guild_file(self, xml_file_object, site):
        """Create characters from a single guild page."""
        xml = minidom.parse(xml_file_object)
        guild_nodes = xml.getElementsByTagName("guildHeader")
        guild_node = guild_nodes[0]
        cp = CharacterParser(downloader=self._downloader)
        
        realm = guild_node.attributes["realm"].value
        
        character_nodes = xml.getElementsByTagName("character")
        characters = []
        
        for character_node in character_nodes:
            name = character_node.attributes["name"].value
            
            try:
                character = cp.get_character(name, realm, site)
            except Exception, e:
                log.warning("Couldn't get character " + name + ", continuing. ERROR: " + str(e))
                continue
            else:
                characters.append(character)
            
        return characters

    def get_guild_rank_from_character(self, character):
        """Returns the rank of a character in a guild. Deconstructs
        the object and passes it to get_guild_rank.
        
        """
        return self.get_guild_rank(character.guild, character.realm, \
            character.site, character.name)

    def get_guild_rank(self, guild_name, realm, site, character_name):
        """Returns the rank of a character (not specified by object)
        in a guild.
        
        """
        source = self._download_url( \
            WoWSpyderLib.get_guild_url(guild_name, realm, site, page=1))

        guild_rank_search = re.search("name=\"" + character_name + \
            "\".*rank=\"(\d*)\"", unicode(source, "utf-8"))
        if guild_rank_search:
            return int(guild_rank_search.group(1))

        raise IOError("No character in that guild")


class Guild(Base):
    """A guild."""
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
        
    def refresh(self, get_characters=False):
        gp = GuildParser()
        # cflewis | 2009-03-31 | Get guild could actually return None if this
        # guild was disbanded. I don't feel like dealing with this right now.
        return_guild = gp.get_guild(self.name, self.realm, self.site, \
            get_characters=get_characters, cached=False)
        
        if return_guild is not None:
            return return_guild
            
        return self
        

class GuildParserTests(unittest.TestCase):
    def setUp(self):
        self.gp = GuildParser()

    def testGuildRank(self):
        self.assertEquals(self.gp.get_guild_rank(u"Meow", u"Cenarius", u"us", "Snicker"), 1)
    
    def testGuildRank2(self):
        self.assertEquals(self.gp.get_guild_rank(u"Meow", u"Cenarius", u"us", "Snoozer"), 4)

    def testGuildRankUnicode(self):
        try:
            result = self.gp.get_guild_rank(u"Beasts of Unusual Size", u"Ravenholdt", u"us", u"Nìghtmare")
        except Exception, e:
            print "Exception got " + str(e)
        self.assertEquals(self.gp.get_guild_rank(u"Beasts of Unusual Size", u"Ravenholdt", u"us", u"Nìghtmare"), 4)
    
    def testInsertGuildNoCharacters(self):
        self.gp.get_guild(u"Meow", u"Cenarius", u"us", get_characters=False)
    
    def testInsertGuildCharacters(self):
        self.gp.get_guild(u"Beasts of Unusual Size", u"Ravenholdt", u"us", \
            get_characters=True)
            
    # def testRefresh(self):
    #     print "Getting guild without characters"
    #     guild1 = self.gp.get_guild(u"The Muffin Club", u"Ravenholdt", u"us", get_characters=False)
    #     print "Refreshing guild characters"
    #     guild2 = guild1.refresh()
    #     
    #     self.assertEqual(guild1, guild2)
        
if __name__ == '__main__':
    unittest.main()
