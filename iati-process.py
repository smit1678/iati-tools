#!/usr/bin/python

# Import Python Modules 
import os
import sys
import time
import traceback
import csv
import simplejson as json
from datetime import datetime
from lxml import etree
from itertools import groupby

# Global variables
globalJSON = []
globalCountries = []

activityTop = {}
activityTopArray = []
activitySub = {}
activitySubArray = []

ctryIndex = {}

currentYear = '2013'

def iatiProcess1(fn):
    global activityTop
    global currentYear

    context = iter(etree.iterparse(fn,tag='iati-activity'))
    for event, p in context:		
    	hierarchy = p.attrib['hierarchy']
    	if hierarchy == '1':
            iatiID = p.find("./iati-identifier").text
            activityTop[iatiID] = {
                    "reporting": "",
                    "implementer": "",
                    "sector": [],
                    "country": "",
                    "location": 0,
                    "locations": [],
                    "budget": 0,
                    "expenditure": 0,
                    "title": "",
                    "description": "",
                    "contact": { "person": "", "site": "", "email": "" }
                    }
            try: 
            	ctryShort = p.find("./recipient-country").attrib
            	ctryName = p.find("./recipient-country").text
            	ctryIndex[ctryName] = ctryShort.get('code')
            except:
            	pass
            try:
            	activityTop[iatiID]['reporting'] = p.find("./reporting-org").text
            except:
            	activityTop[iatiID]['reporting'] = ""
            try: 
            	activityTop[iatiID]['implementer'] = p.find("./participating-org[@role='Implementing']").text
            except:
            	activityTop[iatiID]['implementer'] = ""
            try: 
            	country = p.find("./recipient-country").attrib
            	activityTop[iatiID]['country'] = country.get('code')
            except:
            	activityTop[iatiID]['country'] = ""
    # try to get sector and locations if in hierarchy = 1
            try:
                sector = p.find("./sector[@vocabulary='DAC']")
                activityTop[iatiID]['sector'] = sector.text
            except:
                pass
            try:
                locations = p.findall('location')
                locCount = 0
                for location in locations:
                    locCount = locCount + 1
                    activityLoc = getLocations(location)
                    activityTop[iatiID]['locations'].append(activityLoc)
                activityTop[iatiID]['location'] = locCount
            except:
                pass
            # get budget and expenditure
            try:
                budgets = p.findall("./budget")
                for budget in budgets:
                    for b in budget.iterchildren(tag='value'):
                        date = b.get('value-date').split('-', 3)
                        if date[0] == currentYear:
                            amt = b.text
                            activityTop[iatiID]['budget'] = float(amt)
                transactions = p.findall('transaction')
                for tx in transactions:
                    for expen in tx.findall("./transaction-type[@code='E']"):
                        for sib in expen.itersiblings():
                            if sib.tag == 'value':
                                date = sib.get('value-date').split('-', 3)
                                if date[0] == currentYear:
                                    amt = sib.text
                                    activityTop[iatiID]['expenditure'] = float(amt)
            except:
                pass
        if hierarchy == '2':
            iatiProcess2(p)

def iatiProcess2(p):
    global activitySub

    iatiID = p.find("./iati-identifier").text
    try: 
        related = p.findall("./related-activity[@type='1']")
        for r in related:
            topID = r.get('ref')
            activityLink = topID + "-" + iatiID
            activitySub[activityLink] = {
            		"topID": topID,
            		"subID": iatiID,
            		"sector": "",
            		"location": [],
                    "budget": 0,
                    "expenditure": 0
                    }			
    except: 
        activitySub[activityLink]['topID'] = ""
    try:
        sector = p.find("./sector[@vocabulary='DAC']")
        activitySub[activityLink]['sector'] = sector.text
    except:
        pass
    locations = p.findall('location')
    for location in locations:
        activityLoc = getLocations(location)
        activitySub[activityLink]['location'].append(activityLoc)
    activitySubArray.append(activitySub)
    try:
        budgets = p.findall("./budget")
        for budget in budgets:
            for b in budget.iterchildren(tag='value'):
                date = b.get('value-date').split('-', 3)
                if date[0] == currentYear:
                    amt = b.text
                    activitySub[activityLink]['budget'] = float(amt)
        transactions = p.findall('transaction')
        for tx in transactions:
            for expen in tx.findall("./transaction-type[@code='E']"):
                for sib in expen.itersiblings():
                    if sib.tag == 'value':
                        date = sib.get('value-date').split('-', 3)
                        if date[0] == currentYear:
                            amt = sib.text
                            activitySub[activityLink]['expenditure'] = float(amt)
    except:
        pass

def getLocations(location):
    activityLoc = {
            "coordinates": [],
            "location-type": ""
            }
    for loc in location.iterchildren():
        if loc.tag == 'coordinates':
            lat = loc.get('latitude')
            activityLoc['coordinates'].append(lat)
            lon = loc.get('longitude')
            activityLoc['coordinates'].append(lon)
        if loc.tag == 'location-type':
            locType = loc.get('code')
            activityLoc['location-type'] = locType
    return activityLoc

def linkSubActivities():
    global activityTop
    global activitySub
    global globalCountries

    project_count = 0 
    for i,a in activityTop.items():
        project_count = project_count + 1
        if a['country'] not in globalCountries:
            globalCountries.append(a['country'])
        for s,b in activitySub.items():
            if i == "-".join(s.split("-")[0:3]):
                locCount = 0
                for loc in b['location']:
                    locCount = locCount + 1
                    a['locations'].append(loc)
                a['location'] = locCount
                if b['sector'] not in a['sector']:
                    a['sector'].append(b['sector'])
                a['budget'] = a['budget'] + b['budget']
                a['expenditure'] = a['expenditure'] + b['expenditure']
        globalJSON.append(a)

    print project_count	

def countryIndex():
    global ctryIndex

    geo = csv.DictReader(open('../country_coords.csv', 'rU'), delimiter = ',', quotechar = '"')
    country_sort = sorted(geo, key = lambda x: x['iso3'])

    country_index = []

    for n,c in ctryIndex.items():
        ctryJson = {
                "country-full": "",
                "country": "",
                "country-coord": []
                }
        for ctry in country_sort:
            if ctry['name'].decode('utf-8') == n:
                ctryJson['country-full'] = n
                ctryJson['country'] = c 
                ctryJson['country-coord'].append(ctry['lon'])
                ctryJson['country-coord'].append(ctry['lat'])
                country_index.append(ctryJson)

    writeout = json.dumps(country_index, sort_keys=True, separators=(',',':'))
    f_out = open('../../api/country-index.json', 'wb')
    f_out.writelines(writeout)
    f_out.close()

def countryObjects():
    global globalJSON
    global globalCountries

    for ctry in globalCountries:
        ctryOutput = []
        for g in globalJSON:
            if g['country'] == ctry:
                ctryOutput.append(g)
        writeout = json.dumps(ctryOutput, sort_keys=True, separators=(',',':'))
        f_out = open('../../api/countries/%s.json' % ctry.lower(), 'wb')
        f_out.writelines(writeout)
        f_out.close()

def globalOutput():
    global globalJSON

    for g in globalJSON:
        del g['budget']
        del g['expenditure']
        del g['locations']
        del g['description']
        del g['title']
        del g['contact']

    writeout = json.dumps(globalJSON, sort_keys=True, separators=(',',':'))
    f_out = open('../../api/global.json', 'wb')
    f_out.writelines(writeout)
    f_out.close()

if __name__ == "__main__":
    os.chdir("tmp/")
    for fn in os.listdir('.'):
        if fn.endswith(".xml"):
            #print fn
            iatiProcess1(fn)
            # iatiProcess1('Afghanistan_projects.xml')
    countryIndex()
    linkSubActivities()
    countryObjects()
    globalOutput()
