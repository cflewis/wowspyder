#!/usr/bin/env python
# encoding: utf-8
"""
Item.py

Created by Chris Lewis on 2009-04-06.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
from Parser import Parser
from xml.dom import minidom
import Database
import Logger
import datetime
import WoWSpyderLib
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, \
    DateTime, Unicode, Integer
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref
from Enum import Enum
import urllib2
import StringIO
import re

log = Logger.log()

Base = Database.get_base()

class ItemParser(Parser):
    def __init__(self, downloader=None):
        '''Initialize the team parser.'''
        log.debug("Creating ItemParser with " + str(downloader))
        Parser.__init__(self, downloader=downloader)
        
    def _check_download(self, source, exception):
        if exception:
            log.error("Unable to download item file")
            raise exception
            
        if re.search("itemInfo/", source):
            log.error("Item was invalid or not returned")
            raise IOError("Item requested was invalid or not returned")
        
        return source
        
    def get_item(self, item_id, cached=True):
        """Returns an item object.
        
        Setting cached to True will return the cached version of the item, 
        if you're sure it's already in the database. This will fall through
        if the item wasn't found. Because items are immutable, caching
        is on by default.
        
        """
        item = self._session.query(Item).get(item_id)
        
        if cached and item:
            return item
            
        log.debug("Getting item...")
            
        # cflewis | 2009-04-02 | If downloading fails, the whole team
        # couldn't be found, so the exception should propagate up.
        source = self._download_url(WoWSpyderLib.get_item_url(item_id))
        item = self._parse_item(StringIO.StringIO(source))
        
        return item
        
    def _parse_item(self, xml_file_object):
        """Parse an item."""
        log.debug("Parsing item...")
        xml = minidom.parse(xml_file_object)
        item_nodes = xml.getElementsByTagName("item")
        item_node = item_nodes[0]
        
        item_id = int(item_node.attributes["id"].value)
        level = int(item_node.attributes["level"].value)
        name = item_node.attributes["name"].value
        quality = int(item_node.attributes["quality"].value)
        item_type = item_node.attributes["type"].value

        try:
            cost_nodes = item_node.getElementsByTagName("cost")
            cost_node = cost_nodes[0]
        
            sell_price = cost_node.attributes["sellPrice"].value
        except Exception, e:
            # cflewis | 2009-04-06 | No sell price available
            sell_price = None
        
        item = Item(item_id, name, level, quality, item_type, sell_price)
        log.info("Creating item " + unicode(item).encode("utf-8"))
        
        Database.insert(item)

        return item


class ItemParserTests(unittest.TestCase):
    def setUp(self):
        self.ip = ItemParser()
        
    def testGetItem(self):
        item = self.ip.get_item(38237)
        self.assertEqual("Axe of Frozen Death", item.name)
        
class Item(Base):
    """An item"""
    __table__ = Table("ITEM", Base.metadata,    
        Column("item_id", Integer(), primary_key=True),
        Column("name", Unicode(100), index=True),
        Column("level", Integer()),
        Column("quality", Integer()),
        Column("item_type", Unicode(100)),
        Column("sell_price", Integer()),
        Column("first_seen", DateTime(), default=datetime.datetime.now()),
        Column("last_refresh", DateTime()),
        mysql_charset="utf8",
        mysql_engine="InnoDB"
    )

    def __init__(self, item_id, name, level, quality, item_type, sell_price, last_refresh=None):
        self.item_id = item_id
        self.name = name
        self.level = level
        self.quality = quality
        self.item_type = item_type
        self.sell_price = sell_price
        self.last_refresh = last_refresh

    def __repr__(self):
        return unicode("<Item('%d','%s', '%s')>" % \
            (self.item_id, self.name, self.item_type))


if __name__ == '__main__':
    unittest.main()