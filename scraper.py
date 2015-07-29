#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import mechanize 
import lxml.html
import scraperwiki
import requests
import traceback
import urllib
from twython import Twython, TwythonError
import time
from datetime import datetime
import os


dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')

def scrapeDonations():
 
    annDonorsurl = "http://periodicdisclosures.aec.gov.au/Party.aspx"
    scraperwiki.sqlite.save_var('startTime', datetime.now())

    periods = [
    {"year":"1998-1999","id":"1"},
    {"year":"1999-2000","id":"2"},
    {"year":"2000-2001","id":"3"},
    {"year":"2001-2002","id":"4"},
    {"year":"2002-2003","id":"5"},
    {"year":"2003-2004","id":"6"},
    {"year":"2004-2005","id":"7"},
    {"year":"2005-2006","id":"8"},
    {"year":"2006-2007","id":"9"},
    {"year":"2007-2008","id":"10"},
    {"year":"2008-2009","id":"23"},
    {"year":"2009-2010","id":"24"},
    {"year":"2010-2011","id":"48"},
    {"year":"2011-2012","id":"49"},
    {"year":"2012-2013","id":"51"},
    {"year":"2013-2014","id":"55"}
    ]

    for period in periods:
        br = mechanize.Browser()
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        response = br.open(annDonorsurl)
        print "Loading data for "+period['year']
        year = period['year']
        #for form in br.forms():
            #print form

        #print br.forms()    

        #print "All forms:", [ form.name  for form in br.forms() ]
     
        br.select_form(nr=0)

        # print br.form
        # print periods[x]['id']
        
        br['ctl00$dropDownListPeriod']=[period['id']]
        response = br.submit("ctl00$buttonGo")

        response = br.open(annDonorsurl)
        br.select_form(nr=0)
        #print br.form.controls
        items = br.form.controls[10].get_items()

        for item in items:
            partyID = item.name
            print partyID
            partyName = item.attrs['label']
            print "Entity:", item.attrs['label']
            response = br.open(annDonorsurl)
            br.select_form(nr=0)
            br['ctl00$ContentPlaceHolderBody$dropDownListParties']=[item.name]
            br.select_form(nr=0)
            response = br.submit("ctl00$ContentPlaceHolderBody$buttonSearch")
            html = response.read()  
            #print html
            root = lxml.html.fromstring(html)
            trs = root.cssselect("#ContentPlaceHolderBody_gridViewCurrent tr")
            if trs:
                tds = trs[-1].cssselect("td")
                dateFiled = tds[1].text
                #print "dateFiled", dateFiled
                returnUrl = "http://periodicdisclosures.aec.gov.au/" + lxml.html.tostring(tds[0]).split('<a href="')[1].split('">')[0]
                #print "returnUrl", returnUrl

            data = {}
            data['partyID'] = partyID
            data['year'] = year
            data['partyName'] = partyName
            data['dateFiled'] = dateFiled
            data['returnUrl'] = returnUrl
            data['dateScraped'] = dateScraped

            #print data
            
            #if running for the first time set firstRun to true

            firstRun = False

            if firstRun == True:
                scraperwiki.sqlite.save(unique_keys=["partyID","partyName","year"], table_name="donationTable", data=data)

            elif firstRun == False:
                #check if it has been scraped before

                queryString = "* from donationTable where partyID='" + partyID + "' and year='" + year + "'"
                queryResult = scraperwiki.sqlite.select(queryString)
                
                #if it hasn't been scraped before, save the values

                #scraperwiki.sqlite.save(unique_keys=["partyID","partyName","year"], table_name="donationTable", data=data)

                if not queryResult:
                    print "new data, saving"
                    scraperwiki.sqlite.save(unique_keys=["partyID","partyName","year"], table_name="donationTable", data=data)

                #if it has been saved before, check if it has been updated
                
                else:
                    if data['dateFiled'] != queryResult[0]['dateFiled']:

                        #it has been updated, so save the new values in the main database table

                        print data['partyName'], "has filed an update for", data['year']

                        scraperwiki.sqlite.save(unique_keys=["partyID","partyName","year"], table_name="donationTable", data=data)

                        #and save the update details in the update table

                        scraperwiki.sqlite.save(unique_keys=["partyID","partyName","year","dateFiled"], table_name="donationUpdateTable", data=data)
                    else:
                        print "no updates"

        print "Completed "+period['year']
                        
    scraperwiki.sqlite.save_var('endTime', datetime.now())
                        
#end scrapeDonations

def scrapeInterests():
    membersUrl = "http://www.aph.gov.au/Senators_and_Members/Members/Register"
    senatorsUrl = "http://www.aph.gov.au/Parliamentary_Business/Committees/Senate/Senators_Interests/Register_4_August"
    #if running for the first time set firstRun to true
    firstRun = False

    #get members interests
    print "Scraping members interests"
    r = requests.get(membersUrl)
    root = lxml.html.fromstring(r.content)
    trs = root.cssselect(".documents tr")
    for tr in trs:
        tds = tr.cssselect("td")
        if tds:
            dateUpdated = tds[0].text
            #print dateUpdated
            interestsUrl = "http://www.aph.gov.au/" + urllib.quote(tds[2].cssselect("a")[0].attrib['href'])
            #print interestsUrl
            politicianName = tds[1].text.split(",")[1].strip() + " " + tds[1].text.split(",")[0].strip()
            #print politicianName

            data = {}
            data['politicianName'] = politicianName
            data['dateUpdated'] = dateUpdated
            data['interestsUrl'] = interestsUrl
            data['dateScraped'] = dateScraped
            data['house'] = 'lower'

            #print data

            if firstRun == True:
                scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

            elif firstRun == False:
                queryString = "* from interestsTable where politicianName='" + politicianName.replace("'","''") + "'"
                queryResult = scraperwiki.sqlite.select(queryString)

                #if it hasn't been scraped before, save the values

                if not queryResult:
                    print "new data, saving"
                    scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

                #if it has been saved before, check if it has been updated
                
                else:
                    if data['dateUpdated'] != queryResult[0]['dateUpdated']:

                        #it has been updated, so save the new values in the main database table

                        print data['politicianName'], " has amended their interests register"

                        scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

                        #and save the update details in the update table

                        scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl","dateUpdated"], table_name="interestsUpdateTable", data=data)

    print "Members interests complete"
                        
    print "Scraping senators interests"                    
    r = requests.get(senatorsUrl)
    root = lxml.html.fromstring(r.content)
    tds = root.cssselect(".narrow-content tr td")
    for td in tds:
        if td.cssselect("ul"):
            interestsUrl = "http://www.aph.gov.au" + td.cssselect("a")[0].attrib['href']
            #print interestsUrl
            
            politicianName = td.cssselect("a")[0].text.split(",")[1].replace("Senator","").strip() + " " + td.cssselect("a")[0].text.split(",")[0].strip()
            #print politicianName

            if politicianName.encode("utf-8") == "James  –  for Queensland McGrath":
                politicianName = "James McGrath"
                print "fixed James"
            dateUpdated = lxml.html.tostring(td.cssselect("li")[0]).split("Last updated")[1].replace("&#160;"," ").replace("<em>","").replace("</em>","").replace("</li>","").strip()
            
            dateUpdated.split()
            
            #print dateUpdated

            data = {}
            data['politicianName'] = politicianName
            data['dateUpdated'] = dateUpdated
            data['interestsUrl'] = interestsUrl
            data['dateScraped'] = dateScraped
            data['house'] = 'upper'

            #print data

            #if running for the first time set firstRun to true

            if firstRun == True:
                scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

            elif firstRun == False:
                queryString = "* from interestsTable where politicianName='" + politicianName.replace("'","''") + "'"
                queryResult = scraperwiki.sqlite.select(queryString)
                print queryResult
                print data    
                #if it hasn't been scraped before, save the values

                if not queryResult:
                    print "new data, saving"
                    scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

                #if it has been saved before, check if it has been updated
                
                else:
                    if data['dateUpdated'] != queryResult[0]['dateUpdated']:

                        #it has been updated, so save the new values in the main database table

                        print data['politicianName'], " has updated their interests register"

                        scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl"], table_name="interestsTable", data=data)

                        #and save the update details in the update table

                        scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl","dateUpdated"], table_name="interestsUpdateTable", data=data)

                    else:
                        print "no updates"                         
    
    print "Senators interests complete"
                         
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

    #print queryResult

    for result in queryResult:
        
        newTweet = result['politicianName'] + " has updated their interests register" + ". " + result['interestsUrl']
        print "Tweeting: " + newTweet
        twitter.update_status(status=newTweet)
        time.sleep(60)


    queryString = "* from donationUpdateTable where dateScraped='" + dateScraped + "'"
    
    try:           
        queryResult = scraperwiki.sqlite.select(queryString)
        for result in queryResult:
            newTweet = result['partyName'] + " has amended their donation declarations for " + result['year'] + ". " + result['returnUrl']
            print "Tweeting: " + newTweet
            twitter.update_status(status=newTweet)
            time.sleep(60)
    except Exception, e:
        print str(e)    

scrapeInterests()
scrapeDonations()
twitterBot()
