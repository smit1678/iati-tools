#!/usr/bin/python

# Import Python Modules 
import os
import sys
import time
import traceback
import csv
import simplejson as json
from datetime import datetime
import requests

organizations = ['undp','unops']

iatiOrgURL = 'http://www.iatiregistry.org/api/rest/dataset'

iatiBaseURL = 'http://www.iatiregistry.org/api/rest/dataset/'

# http://www.iatiregistry.org/api/rest/dataset/undp-afg2013
# http://www.undp.org/content/dam/undp/documents/iati_xml/CO_2013/Afghanistan_projects.xml

def download():
	iatiOrgs = requests.get(iatiOrgURL)
	iatiOrgsData = json.loads(iatiOrgs.text, encoding="utf-8")
	for org in iatiOrgsData:
		if org.split("-")[0] in organizations:
			if org.split("-")[1] != 'org':
				orgGet = requests.get(iatiBaseURL + org)
				orgMeta = json.loads(orgGet.text, encoding="utf-8")
				with open('tmp/%s.xml' % org, "wb") as content:
					getFile = requests.get(orgMeta['download_url'])
					getData = getFile.text
					content.write(getData.encode('ascii','ignore'))

if __name__ == "__main__":
	download()