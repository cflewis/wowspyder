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
    server = "www"
    if site == "eu": server = "eu"
        
    return "http://" + server + ".wowarmory.com/"
    
def get_arena_url(battlegroup, realm, site, ladder_number=2, page=1):
    log.debug("Returning Arena URL: " + battlegroup + "," + realm + ", " + site)
    return get_site_url(site) + "arena-ladder.xml?b=" \
        + quote(battlegroup.encode("utf-8")) + "&ts=" + str(ladder_number) + "&fv=" \
        + quote(realm.encode("utf-8")) + "&ff=realm&p=" + str(page)
        
def get_team_url(name, realm, site, size):
    log.debug("Returning Team URL")
    return get_site_url(site) + "team-info.xml?" + \
        "r=" + quote(realm.encode("utf-8")) + \
        "&ts=" + str(size) + \
        "&t=" + quote(name.encode("utf-8"))
        
def get_character_sheet_url(name, realm, site):
    log.debug("Returning character sheet URL")
    return get_site_url(site) + "character-sheet.xml?" + \
        "r=" + quote(realm.encode("utf-8")) + \
        "&n=" + quote(name.encode("utf-8"))
        
def get_guild_url(name, realm, site, page=1):
    log.debug("Returning guild URL")
    return get_site_url(site) + "guild-info.xml?" + \
    "r=" + quote(realm.encode("utf-8")) + \
    "&n=" + quote(name.encode("utf-8")) + \
    "&p=" + str(page)
    
def get_max_pages(source):
    return int(re.search("maxPage=\"(\d*)\"", source).group(1))

def merge(seq):
    merged = []
    for s in seq:
        for x in s:
            merged.append(x)
    return merged

def main():
    pass


if __name__ == '__main__':
    main()

