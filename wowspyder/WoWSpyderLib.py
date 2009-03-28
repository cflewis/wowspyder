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
log = Logger.log()

def get_site_url(site):
    server = "www"
    if site == "eu": server = "eu"
        
    return "http://" + server + ".wowarmory.com/"
    
def get_arena_url(battlegroup, realm, site, ladder_number=2, page=1):
    log.debug("Returning URL for " + battlegroup + "," + realm + ", " + site)
    return get_site_url(site) + "arena-ladder.xml?b=" \
        + quote(battlegroup.encode("utf-8")) + "&ts=" + str(ladder_number) + "&fv=" \
        + quote(realm.encode("utf-8")) + "&ff=realm&p=" + str(page)


def main():
    pass


if __name__ == '__main__':
    main()

