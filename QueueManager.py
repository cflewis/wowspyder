#!/usr/bin/env python
# encoding: utf-8
"""
QueueManager.py

Created by Chris Lewis on 2009-03-22.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import random
from wowspyder import Database
from wowspyder.Battlegroup import Realm
from wowspyder.GuildCharacter import Guild
from wowspyder import Logger
import datetime
import socket

log = Logger.log()

class QueueManager(object):
    """Manage a queue of work, based on the last_refresh field of the
    database. This works by handing a realm at a time to a client.
    
    This should really deal with locks to prevent other
    systems hitting each other. My proposed solution is to lock to an IP,
    handing the locked realm back to that IP when it comes alive again,
    under the assumption of a client restart. There would need to be
    a cleaning of locks after a certain period of time (so you'd have
    a LOCK_IP column and a LOCK_TIME column), the length of which dictated
    by how long it takes to do the work for a realm."""
    def __init__(self, site=None):
        self.session = Database.session()
        self.site = site
        
        if self.site is None:
            self.site = random.choice([u"us", u"eu"])
        
    def get_next_realm(self):
        """Returns the next realm to work on."""
        lock_id = self._get_lock_id
        realm = None
        realm = self.session.query(Realm).filter(Realm.lock_id == lock_id).first()
                
        if realm == None:
            log.debug("Didn't find a locked realm...")
            count = self.session.query(Realm).filter(Realm.last_refresh == None).filter(Realm.site == self.site).count()
        
            if count != 0:        
                row_number = random.randrange(0, count)
                realm = self.session.query(Realm).filter(Realm.last_refresh == None).filter(Realm.site == self.site)[row_number]
                log.debug("Locking realm")
                realm.lock_id = self._get_lock_id()
                realm.lock_time = datetime.datetime.now()
                Database.insert(realm)
            
        return realm
        
    def get_next_guild(self, realm):
        """Returns the next guild to work on in the realm"""
        count = self.session.query(Guild).filter(Guild.last_refresh == None).filter(Guild.realm == realm.name).filter(Guild.site == realm.site).count()
        
        if count != 0:        
            row_number = random.randrange(0, count)
            return self.session.query(Guild).filter(Guild.last_refresh == None).filter(Guild.realm == realm.name).filter(Guild.site == realm.site)[row_number]
            
        return None
        
    def finish_realm(self, realm):
        realm.last_refresh = datetime.datetime.now()
        realm.lock_id = None
        realm.lock_time = None
        Database.insert(realm)
        
        
    def _get_lock_id(self):
        return socket.gethostname()


class QueueManagerTests(unittest.TestCase):
    def setUp(self):
        self.qm = QueueManager()
        
    def testLockedRealm(self):
        first_realm = self.qm.get_next_realm()
        second_realm = self.qm.get_next_realm()
        
        print "Realm is " + str(first_realm)
        
        # cflewis | 2009-03-22 | This has a 1 in 485 chance of failing.
        # I'm willing to take those odds.
        self.assertEqual(first_realm, second_realm)
        self.qm.finish_realm(first_realm)
        self.qm.finish_realm(second_realm)
        first_realm.last_refresh = None
        Database.insert(first_realm)
        second_realm.last_refresh = None
        Database.insert(second_realm)
        
    def testUnlockRealm(self):
        realm1 = self.qm.get_next_realm()
        self.qm.finish_realm(realm1)
        realm2 = self.qm.get_next_realm()
        
        self.assertNotEqual(realm1, realm2)

        self.qm.finish_realm(realm1)
        self.qm.finish_realm(realm2)
        realm1.last_refresh = None
        Database.insert(realm1)
        realm2.last_refresh = None
        Database.insert(realm2)

if __name__ == '__main__':
    unittest.main()