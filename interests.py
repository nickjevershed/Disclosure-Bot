#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraperwiki
import requests
import urllib
import lxml.html
from datetime import datetime

testing = False
excludes = [
'/~/media/03 Senators and Members/32 Members/Register/45p/AB/AlexanderJ_45P.pdf',
'/~/media/03 Senators and Members/32 Members/Register/45p/GJ/JoyceB_45P.pdf'
]

def cleanNames(name):
    titles = ['The Hon ','Mr ','Mrs ','Dr ', ' OAM','Ms ', ' AO', ' AM','The  Hon ','the Hon ']
    for title in titles:
        name = name.replace(title,'')
    if "(" in name:
        name = name.split("(")[1].replace(")","")
    nameList = name.split(" ")
    name = nameList[0] + " " + nameList[-1]
    return name.strip().replace(u'\xa0', u' ')   


def scrapeInterests():
    dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')
    membersUrl = "http://www.aph.gov.au/Senators_and_Members/Members/Register"
    senatorsUrl = "http://www.aph.gov.au/Parliamentary_Business/Committees/Senate/Senators_Interests/CurrentRegister"
    #if running for the first time set firstRun to true
    firstRun = False

    #get members interests
    print "Scraping members interests"
    r = requests.get(membersUrl)
    root = lxml.html.fromstring(r.content)

    # Get former members

    trs = root.cssselect(".documents tr")

    for tr in trs:
        tds = tr.cssselect("td")
        if tds:
            dateUpdated = tds[0].text
            #print dateUpdated
            if "<a" in lxml.html.tostring(tds[2]):
                if tds[2].cssselect("a")[0].attrib['href'] not in excludes:
                    print tds[2].cssselect("a")[0].attrib['href']
                    interestsUrl = "http://www.aph.gov.au/" + urllib.quote(tds[2].cssselect("a")[0].attrib['href'])
                    print interestsUrl
                    politicianName = tds[1].text.split(",")[1].strip() + " " + tds[1].text.split(",")[0].strip()
                    politicianName = cleanNames(politicianName)

                    data = {}
                    data['politicianName'] = politicianName
                    data['dateUpdated'] = dateUpdated
                    data['interestsUrl'] = interestsUrl
                    data['dateScraped'] = dateScraped
                    data['house'] = 'lower'

                    #print data

                    if firstRun == True:
                        if not testing:
                            scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

                    elif firstRun == False:
                        queryString = "* from interestsTable where politicianName='{name}'".format(name=politicianName.replace("'","''"))
                        queryResult = scraperwiki.sqlite.select(queryString)

                        #if it hasn't been scraped before, save the values

                        if not queryResult:
                            print "new data, saving"
                            if not testing:
                                scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

                        #if it has been saved before, check if it has been updated
                        
                        else:
                            if data['dateUpdated'] != queryResult[0]['dateUpdated']:

                                # it has been updated, so save the new values in the main database table

                                print data['politicianName'], " has amended their interests register"
                                if not testing:
                                    scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

                                # and save the update details in the update table

                                if not testing:
                                    scraperwiki.sqlite.save(unique_keys=["politicianName","dateUpdated"], table_name="interestsUpdateTable", data=data)

    print "Members interests complete"
                        
    print "Scraping senators interests"                    
    r = requests.get(senatorsUrl)
    root = lxml.html.fromstring(r.content)
    tds = root.cssselect(".columns tr td")
    
    for td in tds:
        if td.cssselect("ul"):
            interestsUrl = "http://www.aph.gov.au" + urllib.quote(td.cssselect("a")[0].attrib['href'].replace("?la=en",""))
            print interestsUrl
            
            politicianName = td.cssselect("a")[0].text.split(",")[1].replace("Senator","").strip() + " " + td.cssselect("a")[0].text.split(",")[0].strip()
            politicianName = cleanNames(politicianName)

            # if politicianName.encode("utf-8") == "James  –  for Queensland McGrath":
            #     politicianName = "James McGrath"
            #     print "fixed James"
            
            try:
                dateUpdated = lxml.html.tostring(td.cssselect("li")[0]).split("Last updated")[1].replace("&#160;"," ").replace("<em>","").replace("</em>","").replace("</li>","").strip()
            except:
                dateUpdated = lxml.html.tostring(td.cssselect("em")[0]).split("Last updated")[1].replace("&#160;"," ").replace("<em>","").replace("</em>","").replace("</li>","").strip()

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
                scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

            elif firstRun == False:
                print politicianName
                queryString = "* from interestsTable where politicianName='{name}'".format(name=politicianName.replace("'","''"))
                queryResult = scraperwiki.sqlite.select(queryString)
                #print queryResult
                #print data    
                #if it hasn't been scraped before, save the values

                if not queryResult:
                    print "new data, saving"
                    if not testing:
                        scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

                #if it has been saved before, check if it has been updated
                
                else:
                    if data['dateUpdated'] != queryResult[0]['dateUpdated']:

                        #it has been updated, so save the new values in the main database table

                    
                        print data['politicianName'].decode('ascii', 'ignore'), " has updated the interests register"
                        
                        if not testing:
                            scraperwiki.sqlite.save(unique_keys=["politicianName"], table_name="interestsTable", data=data)

                        #and save the update details in the update table
                        if not testing:
                            scraperwiki.sqlite.save(unique_keys=["politicianName","dateUpdated"], table_name="interestsUpdateTable", data=data)

                    else:
                        print "no updates"                         
    
    print "Senators interests complete"


# scrapeInterests()   