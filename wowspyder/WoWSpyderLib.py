#!/usr/bin/env python
# encoding: utf-8
"""
WoWSpyderLib.py

Created by Chris Lewis on 2009-03-24.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import Logger
from urllib2 import quote
import re
log = Logger.log()

def get_site_url(site):
    """Return the domain name for the relevant Armory."""
    server = "www"
    if site == "eu": server = "eu"
        
    return "http://" + server + ".wowarmory.com/"
    
def get_arena_url(battlegroup, realm, site, ladder_number=2, page=1):
    """Return the URL for an arena"""
    log.debug("Returning Arena URL: " + battlegroup + "," + realm + ", " + site)
    return get_site_url(site) + "arena-ladder.xml?b=" \
        + quote(battlegroup.encode("utf-8")) + "&ts=" + str(ladder_number) + "&fv=" \
        + quote(realm.encode("utf-8")) + "&ff=realm&p=" + str(page)
        
def get_team_url(name, realm, site, size):
    """Return the URL for a team"""
    team_url = get_site_url(site) + "team-info.xml?" + \
        "r=" + quote(realm.encode("utf-8")) + \
        "&ts=" + str(size) + \
        "&t=" + quote(name.encode("utf-8"))

    log.debug("Returning Team URL: " + team_url)
        
    return team_url
    
def get_item_url(item_id):
    """Return the URL for an item"""
    item_url = get_site_url(u"us") + "item-info.xml?" + \
        "i=" + str(item_id)

    log.debug("Returning Item URL: " + item_url)

    return item_url
        
def get_character_sheet_url(name, realm, site):
    """Return the URL for a character"""
    character_sheet_url = get_site_url(site) + "character-sheet.xml?" + \
        "r=" + quote(realm.encode("utf-8")) + \
        "&n=" + quote(name.encode("utf-8"))
        
    log.debug("Returning character sheet URL: " + character_sheet_url)
    return character_sheet_url
    
def get_character_talents_url(name, realm, site):
    """Return the talent URL for a character"""
    character_talents_url = get_site_url(site) + "character-talents.xml?" + \
        "r=" + quote(realm.encode("utf-8")) + \
        "&n=" + quote(name.encode("utf-8"))

    log.debug("Returning character talents URL: " + character_talents_url)
    return character_talents_url
    
        
def get_guild_url(name, realm, site, page=1):
    """Return the URL for a guild"""
    log.debug("Returning guild URL")
    return get_site_url(site) + "guild-info.xml?" + \
    "r=" + quote(realm.encode("utf-8")) + \
    "&n=" + quote(name.encode("utf-8")) + \
    "&p=" + str(page)
    
def get_max_pages(source):
    """Return the max pages for pages that paginate."""
    return int(re.search("maxPage=\"(\d*)\"", source).group(1))

def merge(seq):
    """Merge a list of lists into one big list."""
    merged = []
    for s in seq:
        for x in s:
            merged.append(x)
    return merged

def main():
    pass


if __name__ == '__main__':
    main()

