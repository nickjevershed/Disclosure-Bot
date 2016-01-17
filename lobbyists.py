#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraperwiki
import requests
import urllib
import lxml.html
from datetime import datetime
import json

def scrapeLobbyists():
    dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')
    lobbyistUrl = "http://lobbyists.pmc.gov.au/who_register.cfm"

    #if running for the first time set firstRun to true
    firstRun = True

    #check if any new lobbyists have been added

    print "Scraping lobbyist agencies"
    html = requests.get(lobbyistUrl)
    # print html.content
    root = lxml.html.fromstring(html.content)
    trs = root.cssselect("#lobbyisytsResults tr")

    for tr in trs[1:]:
        tds = tr.cssselect("td")
        if tds:
            dateUpdated = tds[4].text.strip()
            print dateUpdated

            agencyName = tds[2].cssselect("a")[0].text.strip()
            print agencyName

            agencyAbn = tds[3].text.strip().replace(" ","")

            agencyUrl = "http://lobbyists.pmc.gov.au/" + tds[2].cssselect("a")[0].attrib['href']
            print agencyUrl

            agencyID = tds[2].cssselect("a")[0].attrib['href'].split("?id=")[1]

            clientHtml = requests.get(agencyUrl)
            clientRoot = lxml.html.fromstring(clientHtml.content)
            clientTrs = clientRoot.cssselect("#clientDetails tr")

            clients = []
            
            for clientTr in clientTrs[1:]:
                clients.append(clientTr.cssselect("td")[1].text)

            print clients 

            data = {}
            data['dateUpdated'] = dateUpdated
            data['agencyName'] = agencyName
            data['agencyAbn'] = agencyAbn
            data['agencyID'] = agencyID
            data['agencyUrl'] = agencyUrl
            data['clients'] = clients

            print data

            #save data the first time around so it can be checked for changes

            if firstRun == True:
                scraperwiki.sqlite.save(unique_keys=["agencyID","agencyUrl"], table_name="lobbyistsTable", data=data)

            #if it's not the first run then check for new lobbyists   

            elif firstRun == False:
                queryString = "* from lobbyistsTable where agencyID='" + agencyID + "'"
                queryResult = scraperwiki.sqlite.select(queryString)

                #if it hasn't been scraped before, save the values to the base database table and the table of lobbyists updates

                if not queryResult:
                    print "new lobbyist, saving"
                    scraperwiki.sqlite.save(unique_keys=["agencyID","agencyUrl"], table_name="lobbyistsTable", data=data)
                    scraperwiki.sqlite.save(unique_keys=["agencyID","agencyUrl"], table_name="lobbyistsUpdateTable", data=data)


                #if it has been saved before, check if it has been updated
                
                else:
                    if data['dateUpdated'] != queryResult[0]['dateUpdated']:

                        #it has been updated, so save the new values in the main database table

                        print data['agencyName'], " has updated the lobbyists register"

                        #check if they added or removed a client

                        oldClients = json.loads(queryResult[0]['dateUpdated'])

                        if set(oldClients) != set(clients):

                            # check if new clients have been added

                            if len(clients) > len(oldClients):

                                changedClients = list(set(clients) - set(oldClients))
                                clientType = 'addition'

                            # check if old clients have been removed    

                            elif len(oldClients) > len(clients): 

                                changedClients = list(set(clients) - set(oldClients))
                                clientType = 'removal'

                            # else added a new client and dropped an old client
                            
                            else:
                                



                        scraperwiki.sqlite.save(unique_keys=["agencyID","agencyUrl"], table_name="lobbyistsTable", data=data)

                        #and save the update details in the update table

                        scraperwiki.sqlite.save(unique_keys=["politicianName","interestsUrl","dateUpdated"], table_name="interestsUpdateTable", data=data)

    print "Lobbyists register complete"

scrapeLobbyists()
