#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json

"""
   Clean, format the osm data into a JSON format for import into mongodb
"""

# REGEX to check for all lower case characters in a string
lower = re.compile(r'^([a-z]|_)*$')

# REGEX to check for colon values
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')

# REGEX to check for mongodb specific characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

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

'''
 Create the CREATED dictionary to store the a node's meta data
'''
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


'''
 Create the POSITION Dictionary, which contains the latititude and
 the longititued.   Lat is in the 0 position Lon is in the 1 position,
 This will be used as a lookup dictionary to determine if a key
 exits in an element
'''
POSITION = ["lat","lon"]

def shape_element(element):
    '''
        shape_element will peform the following tasks:
        - if second level tag "k" value contains problematic characters, it should be ignored
        - if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
        - if second level tag "k" value does not start with "addr:", but contains ":", you can process it
          same as any other tag.
        - if there is a second ":" that separates the type/direction of a street,
          the tag should be ignored, for example:
    '''
    # Create the node dictionary
    node = {}
    # Add the created object to the node dictionary
    node['created'] = {}

    # For Lat and Lon we will store these in a 'pos' (position)
    # we need lat, lon and in specific order (LAT, LON)
    node['pos'] =[0 for i in range(2)]

    # Search only through the node and way types
    if element.tag == "node" or element.tag == "way" :
        # add the type to the node, the tag of the element
        node['type'] = element.tag

        # Search through the node and way types
        # to build the CREATED and POSITION dictionaries
        for k,v in element.attrib.iteritems():
            # CREATE VALUES {"version", "changeset", "timestamp", "user", "uid"}
            if k in CREATED:
                node['created'][k] = v

            #TODO: make sure time is formated from string to date

            # Lat is in first position, Lon second position
            # In JSON and mongodb we need to represent the Lat and Lon as floats
            elif k in POSITION:
                if k=="lat":
                    node['pos'][0]=(float(v))
                else: # Lon
                    node['pos'][1]=(float(v))
            # Key was not in the CREATED or POSITION dictionary
            # Add a new key value pair
            else:
                node[k] = v
        '''
        Setup processing for the TAGS - Addresses and other meta data for the
        node and way objects
        '''
        # Instantiate the address dictionary
        address = {}

        '''
        Search all the subelements and prepare valid tags for processing
        Any ignored data will be emitted to the console
        '''
        for tag in element.iter("tag"):
            if is_valid_tag(tag) == True:
                # address attributes - create the dictionary object to hold
                # the attributes.
                # use a slice of the item from beginning for 5 characters
                if tag.attrib['k'][:5] == "addr:":
                    # Set the keyName to the text to the RIGHT of the colon, dropping "addr:"
                    newKey = tag.attrib['k'][5:]
                    # if there is a second ":" that separates the
                    # type/direction of a street ignore it - Per Assignment
                    if newKey.count(":")> 0:
                        print "found colon, and it's not address - ignoring it", newKey
                    else:
                        # Add new key to the address object, and assign the
                        # value to the key
                        address[newKey] = tag.attrib['v']
                        # Clean the Address
                        if newKey == "street":
                            clean_name = update_streetname(tag.attrib['v'], map_old_to_new)
                            address[newKey] = clean_name

                        # Clean the postcode
                        if newKey == "postcode":
                            clean_zip = update_zipcode(tag.attrib['v'] )
                            address[newKey] = clean_zip

                        # Clean the state, assume all states should be AK
                        if newKey == "state":
                            if  tag.attrib['v'] != "AK":
                                 address[newKey] = "AK"

                        # clean the city name
                        if newKey == "city":
                            clean_city = update_city(tag.attrib['v'])
                            address[newKey] = clean_city

                # we have a generic tag item with no colon, to be added root on the node/way object
                elif tag.attrib['k'].count(":") < 1:
                    plainKey = tag.attrib['k']
                    #print "Plain KEY", tag.attrib['k'], tag.attrib['v']
                    node[plainKey] = tag.attrib['v']

                # For keys similar to the "addr:" key process these keys like the generic keys
                elif tag.attrib['k'].count(":") == 1 and tag.attrib['k'][:5] != "addr:" and tag.attrib['k'][5:] != "created" :
                    # Get the length to the colon, and get the text from the
                    # right of colon to the end for the key.
                    # We are going to strip off the first text to the left of
                    # the colon, for readability and mongodb
                    keyIndex = tag.attrib['k'].find(":")
                    # increment by one so we start at the new key name
                    keyIndex += 1
                    # Get the key name and create a dictionary for this key and value
                    oddKey = tag.attrib['k'][keyIndex:]
                    node[oddKey] = tag.attrib['v']
            else:
                print "Ingnore tag - tag is invalid" , tag.attrib['k'], tag.attrib['v']

        # Search for any node_refs in the sub arrays - just for the way tag, per instructions
        node_refs = []
        if element.tag =="way":
            for ndref in element.iter("nd"):
                node_refs.append(ndref.attrib['ref'])

        # Check to see if we have any node_refs, if we do add the node_refs to the node
        if len(node_refs) > 0:
            node['node_refs'] = node_refs

        # Check to see if we have any addresses, if we have addresses add the addresses to the node
        if len(address)>0:
            node['address'] = address

        return node
    else:
        return None


def is_valid_tag(element):
    '''
    Check for Valid Tags and return true for valid tags false for invalid
    '''
    isValid = True
    if problemchars.search(element.attrib['k']):
        isValid = False

    else:  # Count all the others as valid
         isValid = True

    return isValid

def process_map(file_in, pretty = False):
    '''
    Process map reads in the OpenStreet Map file
    and writes out to file the JSON data structure
    file_in is the path and filename, pretty parameter formats the json
    '''

    # Keep the same filename and just append .json to the filename
    file_out = "{0}.2.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        # Go element by element to read the file
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)

            # If we have an element add it to the dictionary
            # and write the data to a file
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def update_streetname(name, map_old_to_new):
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


def update_zipcode(zipcode):
    '''
        Clean the zip code

        These are a few of the errors one might encounter
        { "_id" : "Homer, AK 99603", "count" : 2 }
        { "_id" : "AK", "count" : 1 }
        { "_id" : "Alaska", "count" : 1 }
        { "_id" : "AK 99501-2129", "count" : 1 }
        { "_id" : "AK 99501-2118", "count" : 1 }
    '''
    # use regex to remove all strings from zipcode, this
    # will leave us with a numeric number which should be
    # 5 or 9 characters long
    zipcode_clean = re.sub(r"\D", "", zipcode)

    return zipcode_clean


def update_city(cityname):
    '''
        TODO
        Scan the dictionary of city names and
        fix bad spellings, improve alogrithim over time
    '''
    if cityname == "Anchoage":
        cityname = "Anchorage"

    return cityname


def test():
    # NOTE: if you are running this code on your computer, with a larger dataset,
    # call the process_map procedure with pretty=False. The pretty=True option adds
    # additional spaces to the output, making it significantly larger.
    data = process_map('Alaska_Small.xml', False)
    pprint.pprint(len(data))
    print "DONE"

if __name__ == "__main__":
    test()
