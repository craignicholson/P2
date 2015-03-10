#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.

Before you process the data and add it into MongoDB, you should
check the "k" value for each "<tag>" and see if they can be valid keys in MongoDB,
as well as see if there are any other potential problems.

We have provided you with 3 regular expressions to check for certain patterns
in the tags. 

As we saw in the quiz earlier, we would like to change the data model
and expand the "addr:street" type of keys to a dictionary like this:
{"address": {"street": "Some value"}}
So, we have to see if we have such tags, and if we have any tags with problematic characters.

Please complete the function 'key_type'.
"""

#Check for all lower case characters in a string
lower = re.compile(r'^([a-z]|_)*$')

#check for colon values
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')

#check for mongodb specific characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


# Scan the element tag and count the occurances of the key type
# Increment the keys based on the results of the regular expression result
def key_type(element, keys):

    #Review only the xml element tag        
    if element.tag == "tag":
        k = element.attrib['k']
        if lower.search(k):
            keys['lower'] +=1 
        #check for lower case words with a colon eg. "source:name"   
        elif lower_colon.search(k):
             keys['lower_colon'] += 1    
        #check for reserved keywords for monogo db        
        elif problemchars.search(k):
             keys['problemchars'] += 1  
             print 'Problem Char: ' + k
        #count all the others
        else:
            keys['other'] += 1 
            
    return keys

#Read file and interate over the elements
def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys


# Test
def test():
    # You can use another testfile 'map.osm' to look at your solution
    # Note that the assertions will be incorrect then.
    keys = process_map('Alaska.xml')
    pprint.pprint(keys)
    #assert keys == {'lower': 5, 'lower_colon': 0, 'other': 1, 'problemchars': 1}


if __name__ == "__main__":
    test()