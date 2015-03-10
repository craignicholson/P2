"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "Alaska.xml"

'''
street_type_re

Regex which scans for the following items listed below to determine
if we have a match for a street name which is shortened, abbriviated and
is only comparing the last word at the end of the string.

https://docs.python.org/2/library/re.html

\b assert position at a word boundary (^\w|\w$|\W\w|\w\W)
\S+ match any non-white space character [^\r\n\t\f ]
Quantifier: + Between one and unlimited times, as many times as possible, giving back as needed [greedy]
\.? matches the character . literally
Quantifier: ? Between zero and one time, as many times as possible, giving back as needed [greedy]
$ assert position at end of the string
https://www.regex101.com/#python
'''
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# The expected street names
expected_street_names = ["Avenue", "Boulevard", "Circle", "Commons", "Court", "Drive", "Highway", "Lane", "Loop", "Parkway", "Place", "Road",
             "Sqaure", "Street", "Trail"]

'''
map_old_to_new
Create Dictionary to map abreiviations to full street's suffix
'''
map_old_to_new = { 
            "Ave" : "Avenue",
            "Ave." : "Avenue",
            "Blvd" : "Boulevard",
            "Blvd." : "Boulevard",
            "Cir" : "Circle",
            "Cmn" : "Commons",
            "Crt" : "Court",
            "Crt." : "Court",
            "Dr" : "Drive",
            "Dr." : "Drive",
            "Hwy" : "Highway",
            "Ln" : "Lane",
            "Ln." : "Lane",
            "LN" : "Lane",
            "Lp" : "Loop",
            "PARK":"Park",
            "Pk" : "Parkway",
            "Pk." : "Parkway",                     
            "Pl" : "Place",
            "Pl." : "Place",                     
            "Rd.": "Road",
            "Rd" : "Road",                      
            "Sq": "Sqaure",
            "Sq.": "Sqaure",                       
            "St": "Street",
            "St.": "Street",
            "Tr": "Trail",
            "Tr.": "Trail",
            "Ashwood": "Ashwood Street"
            }
            
def audit(osmfile):
    '''
    Audit the addresses in the file and return a list of street_types
    A street_type being Road, Drive, Lane, Highway etc...
    '''
    osm_file = open(osmfile, "r")

    #Create collection to hold the streets we find
    street_types = defaultdict(set)
    
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        #We are expecting the nodes and way to contain an address
        #check only these for address attributes
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

    return street_types

def is_street_name(elem):
    '''Checks if element is a street name, returns True or False'''
    return (elem.attrib['k'] == "addr:street")
    

def audit_street_type(street_types, street_name):
    '''
    Audit the street name for inconsistencies
    '''
    #re.search checks for a match anywhere in the string
    #store this value in a match object
    m = street_type_re.search(street_name)
    #We have found a match in our search, we have a match object
    #the map object will have the output which matched the regex
    if m:
        #fetch the match into street_type
        street_type = m.group()
        
        #street type should represent the last word in the address
        #of street_type does not match any of the expected names
        #add these to the street_types list
        if street_type not in expected_street_names:
            street_types[street_type].add(street_name)

def update_name(name, map_old_to_new):
    '''
    Update name compares current name to the map of bad values to good values
    and provides the updated name back to the method    
    '''
    for iName in map_old_to_new.keys():
        #Check to see if we find a match for a bad value in our map        
        match = re.search(iName, name)
        #if match is found then remap the old value with new value        
        if match:
            name = re.sub(iName+'$', map_old_to_new[iName], name)
    return name

def test():
    st_types = audit(OSMFILE)
    #assert len(st_types) == 3
    print '\nStreet Types'
    pprint.pprint(dict(st_types))

    print '\nFixed Examples'
    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, map_old_to_new)
            print name, "=>", better_name
            #if name == "West Lexington St.":
            #    assert better_name == "West Lexington Street"
            #if name == "Baldwin Rd.":
            #    assert better_name == "Baldwin Road"


if __name__ == '__main__':
    test()