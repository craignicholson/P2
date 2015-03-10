#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Craig Nicholson
January 31, 2015
OpenStreetMap Sample Project
Data Wrangling with MongoDB

Your task is to use the iterative parsing to process the map file and
find out not only what tags are there, but also how many, to get the
feeling on how much of which data you can expect to have in the map.
The output should be a dictionary with the tag name as the key
and number of times this tag can be encountered in the map as value.

Note that your code will be tested with a different data file than the 'example.osm'
"""
import xml.etree.ElementTree as ET
import pprint

def count_tags(filename):
        # YOUR CODE HERE
        # Key, Value {Key = element tag name, value is the # of occurances of tag
        # default_data['item3'] = 0, else 
        
        '''
        events = ("start",), is for iterparse
        
        The events option specify what events you want to see 
        (available events in this release are “start”, “end”, 
        “start-ns”, and “end-ns”, where the “ns” events are used 
        to get detailed namespace information). 
        
        If the option is omitted, only “end” events are returned.
        
        http://effbot.org/elementtree/iterparse.htm
        http://effbot.org/zone/element-iterparse.htm
        '''
        #Find only the start tags in the element in the XML doc     
        events = ("start",)
        
        #Initiaize the tags dictionary        
        tags={}
        
        #Search the start tags in each element in the XML file
        for event, elem in ET.iterparse(filename, events=events):
            # assign the tag found to key            
            key = elem.tag            
            #If we have already hve this key, increment the count by 1            
            if key in tags:
                tags[key] += 1
            #We have found a new key, set the count to 1
            else:
                tags[key] = 1            
        
        return tags
#Test                
def test():
    
    filename = "Alaska.xml"   
    tags = count_tags(filename)
    pprint.pprint(tags)
    
    '''
    assert tags == {'bounds': 1,
                     'member': 3,
                     'nd': 4,
                     'node': 20,
                     'osm': 1,
                     'relation': 1,
                     'tag': 7,
                     'way': 1}

    '''

if __name__ == "__main__":
    test()