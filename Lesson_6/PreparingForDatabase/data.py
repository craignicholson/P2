#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json

"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. You could also do some cleaning
before doing that, like in the previous exercise, but for this exercise you just have to
shape the structure.

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""

# REGEX to check for all lower case characters in a string
lower = re.compile(r'^([a-z]|_)*$')

# REGEX to check for colon values
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')

# REGEX to check for mongodb specific characters
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


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
                print "Ingnore tag it is invalid" , tag.attrib['k'], tag.attrib['v']
        
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
    

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('Alaska.xml', False)
    #pprint.pprint(data)
    print 'DONE'
    '''
    assert data[0] == {
                        "id": "261114295", 
                        "visible": "true", 
                        "type": "node", 
                        "pos": [
                          41.9730791, 
                          -87.6866303
                        ], 
                        "created": {
                          "changeset": "11129782", 
                          "user": "bbmiller", 
                          "version": "7", 
                          "uid": "451048", 
                          "timestamp": "2012-03-28T18:31:23Z"
                        }
                      }
    assert data[-1]["address"] == {
                                    "street": "West Lexington St.", 
                                    "housenumber": "1412"
                                      }
    assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
                                    "2199822370", "2199822284", "2199822281"]
   '''
   
if __name__ == "__main__":
    test()