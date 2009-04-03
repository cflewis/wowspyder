#!/usr/bin/env python
# encoding: utf-8
"""
Parser.py

Created by Chris Lewis on 2009-03-31.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

import sys
import os
import unittest
import Database
import XMLDownloader
import Preferences
import Logger

Base = Database.get_base()
log = Logger.log()

class Parser(object):
    def __init__(self, number_of_threads=20, sleep_time=10, downloader=None):
        self._downloader = downloader

        if self._downloader is None:
            log.debug("Creating new downloader...")
            self._downloader = XMLDownloader.XMLDownloaderThreaded( \
                number_of_threads=number_of_threads, sleep_time=sleep_time)

        self._session = Database.session
        Base.metadata.create_all(Database.engine)
        self._prefs = Preferences.Preferences()
        
    def __del__(self):
        self._downloader.close()
        
    def _refresh_downloader(self):
        log.debug("Refreshing downloader")
        self._downloader = XMLDownloader.XMLDownloaderThreaded( \
            number_of_threads=20, sleep_time=10)
        
    def _download_url(self, url):
        log.debug("Parser downloading " + url)
        source = None
        error = None
                
        try:
            source = self._downloader.download_url(url)
        except Exception, e:
            log.warning("Downloading returned an exception " + e)
            error = e
            
        log.debug("Parser returning download source...")
        return self._check_download(self._downloader.download_url(url), error)
        
    def _check_download(self, source, exception):
        """A virtual function that forces parsers to try and detect integrity
        errors with the XML early, separating out error checking from the
        logic when everything is fine. This should stop yucky exceptions
        propagating down to the logic, which they have a habit of doing,
        seeing how shaky the WoW Armory is.
        
        """
        raise NotImplementedError("This should be implemented by the subclass!")


class ParserTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()