#!/usr/bin/env python
# encoding: utf-8
"""
XMLDownloader.py

Created by Chris Lewis on 2009-03-11.

Copyright (c) 2009, Regents of the University of California
All rights reserved.

"""

import sys
import os
import unittest
import re
from xml.dom import minidom
import urllib2
import Logger
import StringIO
import gzip
import cookielib
import time
import random
import threading
import Queue

log = Logger.log()
cache = {}

class XMLDownloader(object):
    ''' A class that creates a session with the WoW Armory, saving a cookie
    and using it whenever this object is asked to download from the Armory.
    
    '''
    def __init__(self, backoff_attempts=3, backoff_initial_time=30, \
            backoff_increment = 60):
        self._cj = cookielib.CookieJar()
        h = urllib2.HTTPHandler(debuglevel=0)
        self._opener = urllib2.build_opener(h, urllib2.HTTPCookieProcessor(self._cj))
        
        self.backoff_attempts = backoff_attempts
        self.backoff_initial_time = backoff_initial_time
        self.backoff_increment = backoff_increment
        
        self.refresh_login()
        
    def refresh_login(self):
        """Refresh the login, getting a new session cookie from the Armory."""
        # cflewis | 2009-03-13 | Get the cookie saved.
        self.download_url("http://www.wowarmory.com/login-status.xml")
        log.debug("Got cookie " + str(self._cj))
        
    def download_url(self, url, backoffs_allowed=None, backoff_time=None):
        """Download a URL and return the source. Specifying
        backoffs_allowed and backoff_time allows the downloader to retry
        downloading URLs on failure.
        
        """
        if cache.has_key(url):
            log.debug("Returning cached version of " + url)
            return cache[url]
        
        log.debug("Downloading " + url)
        if backoffs_allowed is None: backoffs_allowed = self.backoff_attempts
        if backoff_time is None: backoff_time = self.backoff_initial_time
                
        request = urllib2.Request(url)
        request.add_header("User-Agent", "WoWSpyder 0.1, \
like Mozilla/5.0 Gecko/20081201 Firefox/3.1b2. \
http://github.com/Lewisham/wowspyder")
        request.add_header('Accept-encoding', 'gzip')

        try:
            datastream = self._opener.open(request)
        except urllib2.HTTPError, error:
            warning = "Download URL failed, got HTTP %d. URL: %s" % (error.code, url)
            log.warning(warning)
            
            self._opener.close()
            
            if error.code == 404:
                # cflewis | 2009-03-15 | Can't do anything about this
                raise
            else:
                # cflewis | 2009-03-15 | Blizzard blocked us. Back off.
                if backoffs_allowed > 0:
                    log.warning("Sleeping for: %d" % (backoff_time))
                    time.sleep(backoff_time)
                    return self.download_url(url, \
                    backoffs_allowed=backoffs_allowed - 1, \
                    backoff_time=(backoff_time + (self.backoff_increment * random.uniform(1, 1.5))))
                else:
                    raise
        except urllib2.URLError, error:
            log.warning("Time out")
            self._opener.close
            return self.download_url(url, backoffs_allowed=backoffs_allowed, \
                backoff_time=backoff_time)
        
        source = self.decompress_gzip(datastream.read())
        self._opener.close()
        log.debug("Downloaded %s" % url)
        unicode_source = unicode(source, "utf-8").encode("utf-8")
        cache[url] = unicode_source
        
        return unicode_source
        
    def decompress_gzip(self, compressed_data):
        """Decompress gzipped data."""
        compressed_stream = StringIO.StringIO(compressed_data)
        gzipper = gzip.GzipFile(fileobj = compressed_stream)
        return gzipper.read()

        
class XMLDownloaderThreaded(object):
    '''A class to mediate threaded downloading of URLs.
    
    Calling close() when this object is no longer needed would be nice,
    but it closes threads when the object is destroyed.
    '''
    def __init__(self, number_of_threads = 20, sleep_time = 10):
        self.threads = []
        self.request_queue = Queue.Queue()
    
        for x in xrange(number_of_threads):
            thread = XMLDownloaderThread(self.request_queue, sleep_time=sleep_time)
            self.threads.append(thread)
            thread.start()
            
    def __del__(self):
        self.close()
        
    def download_url(self, url):
        """Download a URL from one of the threads."""
        response_queue = Queue.Queue()
        self.request_queue.put((url, response_queue))
        return response_queue.get()
    
    def close(self):
        """Close the object, ending the threads."""
        for _ in self.threads:
            self.request_queue.put((None, None))


class XMLDownloaderThread(threading.Thread):
    """A thread to the XMLDownloader."""
    def __init__(self, request_queue, sleep_time=2):
        threading.Thread.__init__(self)
        self.downloader = XMLDownloader()
        self.request_queue = request_queue
        self.sleep_time = sleep_time
        
    def run(self):        
        while 1:
            url, response_queue = self.request_queue.get()
            if url is None:
                break
            else:
                response_queue.put(self.downloader.download_url(url))
                time.sleep(self.sleep_time * random.uniform(1, 1.5))    


class XMLDownloaderTests(unittest.TestCase):
    def setUp(self):
        self.downloader = XMLDownloader()
        self.moulin = "http://www.wowarmory.com/character-sheet.xml?r=Ravenholdt&n=Moulin&p=1"
        self.shirley = "http://www.wowarmory.com/character-sheet.xml?r=Ravenholdt&n=Shirley&p=1"

    def testDownloadSomething(self):
        source = self.downloader.download_url(self.moulin)
        log.debug(source.decode("ascii", "ignore"))
        self.assertTrue(source)

    def testDownloadXMLSource(self):
        source = self.downloader.download_url(self.moulin)
        self.assertTrue(re.search("<?xml", source), "Didn't get XML")

    def testDownloadFakeSource(self):
        self.assertRaises(urllib2.HTTPError, self.downloader.download_url, \
            "http://chris.to/fakeurl")

    def testDownloadHTMLSource(self):
        source = self.downloader.download_url(self.moulin)
        self.assertFalse(re.search("</?html>", source), \
            "Downloaded HTML, not XML")

    def testDecompressGzip(self):
        filename = "file.txt.gz"
        start_string = "Test string"
        f = gzip.open(filename, 'wb')
        f.write(start_string)
        f.close()
        
        data = open(filename, 'r').read()
        unzipped_string = self.downloader.decompress_gzip(data)
        os.remove(filename)
        self.assertEqual(start_string, unzipped_string)
        

    def testCookies(self):
        source = self.downloader.download_url(self.moulin)
        source = self.downloader.download_url(self.shirley)

        # cflewis | 2009-03-14 | Getting anything but one cookie means
        # something went wrong.
        self.assertEqual(len(self.downloader._cj), 1)
        
    def testThreaded(self):
        self.dt = XMLDownloaderThreaded()
        source = self.dt.download_url(self.moulin)
        self.assertTrue(source)

        
if __name__ == '__main__':
    unittest.main()
    