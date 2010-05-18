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
#from shove import Shove
#import signal
import gc

log = Logger.log()

# cflewis | 2009-04-08 | I think storing this in memory is causing
# memory exhaustion, which is what could be contributing to scaling issues.
cache = {}

def refresh_cache(signum, frame):
    cache.clear()
    gc.collect()
    log.debug("Refreshed cache")
    # signal.signal(signal.SIGALRM, refresh_cache)
    # signal.alarm(300)
    t = threading.Timer(300, refresh_cache)
    t.start()

log.debug("Setting alarm")
t = threading.Timer(300, refresh_cache)
t.start()

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
        
    def __del__(self):
        pass
        
    def refresh_login(self):
        """Refresh the login, getting a new session cookie from the Armory."""
        # cflewis | 2009-03-13 | Get the cookie saved.
        self.download_url("http://www.wowarmory.com/login-status.xml", cached=False)
        log.debug("Got cookie " + str(self._cj))
        
    def download_url(self, url, backoffs_allowed=None, backoff_time=None, cached=True):
        """Download a URL and return the source. Specifying
        backoffs_allowed and backoff_time allows the downloader to retry
        downloading URLs on failure.
        
        """
        if cached:
            try:
                cached_source = cache[url]
            except Exception, e:
                log.debug("Retrieving " + url)
            else:
                log.debug("Returning cached version of " + url)
                source = self.decompress_gzip(cached_source)
                unicode_source = unicode(source, "utf-8").encode("utf-8")
                return unicode_source
        
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
                log.debug("couldn't find page")
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
        
        gzipped_source = datastream.read()
        source = self.decompress_gzip(gzipped_source)
        self._opener.close()
        log.debug("Downloaded %s" % url)
        unicode_source = unicode(source, "utf-8").encode("utf-8")
        if cached: cache[url] = gzipped_source
        
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
    def __init__(self, number_of_threads=20, sleep_time=10):
        self.threads = []
        self.request_queue = Queue.Queue()
        self.sleep_time = sleep_time
    
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
        result = response_queue.get()
        
        if isinstance(result, Exception):
            log.debug("Got exception, starting up new thread in it's place")
            thread = XMLDownloaderThread(self.request_queue, sleep_time=self.sleep_time)
            self.threads.append(thread)
            raise result
        else:
            return result
    
    def close(self):
        """Close the object, ending the threads."""
        for _ in self.threads:
            self.request_queue.put((None, None))


class XMLDownloaderThread(threading.Thread):
    """A thread to the XMLDownloader."""
    def __init__(self, request_queue, sleep_time=10):
        threading.Thread.__init__(self)
        self.downloader = XMLDownloader()
        self.request_queue = request_queue
        self.sleep_time = sleep_time
        
        log.debug("Sleep time is set to " + str(self.sleep_time))
        
    def run(self):
        while 1:
            url, response_queue = self.request_queue.get()
            if url is None:
                break
            else:
                try:
                    result = self.downloader.download_url(url)
                except Exception, e:
                    log.debug("Got exception from downloader, putting it on queue")
                    result = e
                
                response_queue.put(result)
                    
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
        self.assertRaises(Exception, self.dt.download_url, \
            "http://chris.to/fakeurl")
        
    def testThreadedException(self):
        self.dt = XMLDownloaderThreaded()
        source = self.dt.download_url(self.moulin)
         
        
    def testCacheRefresh(self):
        log.debug("TESTING cache refresh, watch...")
        source = self.downloader.download_url(self.moulin)
        refresh_cache(None, None)
        source = self.downloader.download_url(self.moulin)

        
if __name__ == '__main__':
    unittest.main()
    