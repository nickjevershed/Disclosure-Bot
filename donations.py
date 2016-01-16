#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraperwiki
import mechanize 
import lxml.html
from datetime import datetime

def scrapeDonations():
    dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')
    annDonorsurl = "http://periodicdisclosures.aec.gov.au/Updates.aspx"
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
        
        br.select_form(nr=0)
        br['ctl00$ContentPlaceHolderBody$pagingControl$cboPageSize']=["500"]
        response = br.submit("ctl00$ContentPlaceHolderBody$pagingControl$buttonGo")
        html = response.read()
        
        #print html

        root = lxml.html.fromstring(html)
        trs = root.cssselect("#ContentPlaceHolderBody_gridViewUpdates tr")
        pages = root.cssselect(".pagingLink table td")
        noPages = len(pages)

        for tr in trs[1:]:
            tds = tr.cssselect("td")
            dateFiled = tds[0].text
            entityName = tds[1].cssselect("a")[0].text
            entityID = tds[1].cssselect("a")[0].attrib['href'].split("&ClientId=")[1]
            returnUrl = "http://periodicdisclosures.aec.gov.au/" + tds[2].cssselect("a")[0].attrib['href']
            returnText = tds[2].cssselect("a")[0].text
            returnType = ""
            if "Original" in returnText:
                returnType = 'original'
            elif "Amendment" in returnText:
                returnType = 'amendment'
            entityType = tds[3].text

            data = {}
            data['entityID'] = entityID
            data['year'] = year
            data['entityName'] = entityName
            data['dateFiled'] = dateFiled
            data['returnUrl'] = returnUrl
            data['dateScraped'] = dateScraped
            data['returnType'] = returnType
            data['entityType'] = returnType
            data['returnText'] = returnText

            print data
            
            #if running for the first time set firstRun to true

            firstRun = False

            if firstRun == True:
                scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year"], table_name="donationTable", data=data)

            elif firstRun == False:
                #check if it has been scraped before

                queryString = "* from donationTable where entityID='" + entityID + "' and year='" + year + "' and returnText='" + returnText + "'"
                queryResult = scraperwiki.sqlite.select(queryString)
                print queryResult
                #if it hasn't been scraped before, save the values in the main table and table for tweeting

                if not queryResult:
                    print data['partyName'], "has filed an update for", data['year']
                    scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year"], table_name="donationTable", data=data)
                    scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year","dateFiled"], table_name="donationUpdateTable", data=data)
                
                else:
                    print "No updates"

        print "Completed "+period['year']
                        
    scraperwiki.sqlite.save_var('endTime', datetime.now())
