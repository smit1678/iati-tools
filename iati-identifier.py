# IATI Identifer and matching activities search
# ---------------------------------------------
# To run: 
# python iati-identifier.py [ IATI XML filename ] [ project number or ID ]

import os, sys
from lxml import etree
from itertools import groupby

iati_file = sys.argv[1]
iati_identifier = sys.argv[2]

iati_data = iter(etree.iterparse(iati_file,tag='iati-activity'))

for event, p in iati_data:
    # Searches each iati-activity
    iatiID = p.find("./iati-identifier").text
    if iatiID.find(iati_identifier) >= 0:
    	print iatiID
    	outputMatch = p.findall("./related-activity")
    	for o in outputMatch:
    		print '-- %s' % o.get('ref')
