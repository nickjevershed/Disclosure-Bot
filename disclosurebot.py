#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twython import Twython, TwythonError
import time
from datetime import datetime
import os
import donations
import interests
import scraperwiki

dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')

print "dateScraped", dateScraped 

#Check donations updates

donations.scrapeDonations()
 
#Check interests updates

interests.scrapeInterests()
  
#twitterbot http://geekswipe.net/2014/10/code-python-twitter-bot-in-ten-minutes/

def twitterBot():

    APP_KEY = os.environ['APP_KEY']
    APP_SECRET = os.environ['APP_SECRET']
    OAUTH_TOKEN = os.environ['OAUTH_TOKEN']
    OAUTH_TOKEN_SECRET = os.environ['OAUTH_TOKEN_SECRET']

    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    #check the database for today's updates entries and tweet them

    queryString = "* from interestsUpdateTable where dateScraped='" + dateScraped + "'"
    queryResult = scraperwiki.sqlite.select(queryString)

    #tweet the interests results

    try:
        if queryResult:
            for result in queryResult:
                newTweet = result['politicianName'] + " has updated the interests register" + ". " + result['interestsUrl']
                print "Tweeting: " + newTweet
                twitter.update_status(status=newTweet)
                time.sleep(60)
        if not queryResult:
            print "No interests results, tweeting update"
            twitter.update_status(status="Pecuniary interests register checked. No updates!")
            time.sleep(60)
                    
    except Exception, e:
        print str(e)

    #tweet the donations results            

    #print scraperwiki.sqlite.show_tables()

    queryString = "* from donationUpdateTable where dateScraped='" + dateScraped + "'"
    
    if "donationUpdateTable" in scraperwiki.sqlite.show_tables():
        queryResult = scraperwiki.sqlite.select(queryString)
        if queryResult:
            for result in queryResult:
                newTweet = result['entityName'] + " has updated donation declarations for " + result['year'] + ": " + result['returnUrl']
                print "Tweeting: " + newTweet
                try:
                    twitter.update_status(status=newTweet)
                    time.sleep(60)
                except Exception, e:
                    print str(e)
                    
        if not queryResult:
            print "No donations results, tweeting update"
            try:
                twitter.update_status(status="Donation declarations checked. No updates!")
                time.sleep(60)
            except Exception, e:
                print str(e)          
    else:
        print "No donations results, tweeting update"
        try:
            twitter.update_status(status="Donation declarations checked. No updates!")
            time.sleep(60)    
        except Exception, e:
            print str(e)    
twitterBot()




