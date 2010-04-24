#!/usr/bin/env python
# encoding: utf-8
"""
wowwidow.py

Created by Chris Lewis on 2009-03-22.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import datetime
import QueueManager
import threading
from wowspyder import Arena, Database, XMLDownloader, \
    GuildCharacter, Team
import gc
import time
        
class Widow(threading.Thread):
    def __init__(self, site=None):
        threading.Thread.__init__(self)
        self.site = site
        self.qm = QueueManager.QueueManager(site=self.site)
        
    def run(self):
        ap = Arena.ArenaParser()
        
        realm = self.qm.get_next_realm()

        while realm:
            print u"Starting realm " + unicode(realm)

            # cflewis | 2009-03-29 | This will stub out the guilds
            teams = ap.get_arena_teams(realm.battlegroup, realm.name, \
                realm.site, get_characters=True)
            Database.session().expunge_all()
            # cflewis | 2009-03-29 | Now lets fill in the guilds.
            guild = self.qm.get_next_guild(realm)

            while guild:
                print u"Starting guild " + unicode(guild)
                guild.refresh(get_characters=True)
                #log.debug(u"Set last refresh date on " + unicode(guild))
                guild.last_refresh = datetime.datetime.now()
                Database.session().expunge_all()
                guild = self.qm.get_next_guild(realm)

            self.qm.finish_realm(realm)
            realm = self.qm.get_next_realm()
        

# cflewis | 2009-04-09 | Threading should probably be just for one guild
# at a time, so then a full object refresh can occur when it's finished.
def main():
    # us_thread = Widow(u"us")
    # us_thread.start()
    
    # time.sleep(5)
    #     
    #     eu_thread = Widow(u"eu")
    #     eu_thread.start()
    
    thread = Widow()
    thread.start()
    


if __name__ == '__main__':
    main()

