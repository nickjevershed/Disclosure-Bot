#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraperwiki
import mechanize 
import lxml.html
from datetime import datetime

def scrapeDonations():
    dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')
    annDonorsurl = "https://periodicdisclosures.aec.gov.au/Updates.aspx"
    scraperwiki.sqlite.save_var('startTime', datetime.now())

    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    response = br.open(annDonorsurl)
    br.select_form(nr=0)
    html = response.read()
    root = lxml.html.fromstring(html)
    formOptions = root.cssselect('#dropDownListPeriod option')

    periods = []
    for option in formOptions:
        year = option.text
        if len(option.text) == 7:
            year = option.text.split("-")[0] + "-20" + option.text.split("-")[1]
        periods.append({"year":year, "id":option.attrib['value']})
    print periods

    for period in periods:
        response = br.open(annDonorsurl)
        print "Loading data for "+period['year']
        year = period['year']
        # for form in br.forms():
        #     print "###############"
        #     print form

        # print br.forms()    

        #print "All forms:", [ form.name  for form in br.forms() ]
     
        br.select_form(nr=2)

        # print br.form
        # print periods[x]['id']
        
        br['ctl00$dropDownListPeriod']=[period['id']]
        response = br.submit("ctl00$buttonGo")

        response = br.open(annDonorsurl)
        
        # print br.form.controls
        if 'There have been no updates reported' not in response.read():
            br.select_form(nr=2)

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
                print(entityName)
                entityID = tds[1].cssselect("a")[0].attrib['href'].split("&ClientId=")[1]
                
                if "<a href" in lxml.html.tostring(tds[2]):
                    returnUrl = "http://periodicdisclosures.aec.gov.au/" + tds[2].cssselect("a")[0].attrib['href']                    
                    returnText = tds[2].cssselect("a")[0].text
                else:
                    returnUrl = ""
                    returnText = tds[2].text    

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
                data['entityType'] = entityType
                data['returnText'] = returnText

                #if running for the first time set firstRun to true

                firstRun = False

                if firstRun == True:
                    scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year"], table_name="donationTable", data=data)

                elif firstRun == False:
                    #check if it has been scraped before

                    queryString = "* from donationTable where entityID='" + entityID + "' and year='" + year + "' and dateFiled='" + dateFiled + "'"
                    queryResult = scraperwiki.sqlite.select(queryString)
                    #print queryResult
                    #if it hasn't been scraped before, save the values in the main table and table for tweeting

                    if not queryResult:
                        print data['entityName'], "has filed an update for", data['year']
                        scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year"], table_name="donationTable", data=data)
                        scraperwiki.sqlite.save(unique_keys=["entityID","entityName","returnText","year","dateFiled"], table_name="donationUpdateTable", data=data)
                    
                    else:
                        print "No updates"

            print "Completed "+period['year']        
        else:
            print "No updates"                
            print "Completed "+period['year']
                        
    scraperwiki.sqlite.save_var('endTime', datetime.now())

