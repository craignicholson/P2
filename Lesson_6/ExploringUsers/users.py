#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint

"""
Your task is to explore the data a bit more.
The first task is a fun one - find out how many unique users
have contributed to the map in this particular area!

The function process_map should return a set of unique user IDs ("uid")
"""

#Get the user id from the element
def get_user(element):
    uid = element.attrib["uid"]
    return uid

# Read file and count the users
def process_map(filename):
    
    #Create a users collection to hold the all of the users
    #the collection will only contain unique users ("uid")    
    users = set() 

    #Create error collection to capture those elements with no uuid
    errors = set()
    users_in_node_way_elements = set()

    #iterate over the file and each element   
    for _, element in ET.iterparse(filename):
        key = element.tag
        
        #For each tag iterate over the records and attempt to reteive the uuid
        for tag in element.iter(key):
            #attempt to get the uuid, 
            #error out the elements which do not have uuid
            try:
                uid = get_user(element)
                users.add(uid)
                # Check code added to review the data in mongodb
                if key == "node" or key == "way":
                    users_in_node_way_elements.add(uid)   
            except:
                errors.add(key)
    
    #print out the elements with no uuid              
    #pprint.pprint("Has no uuid :", str(errors)
    pprint.pprint(len(users_in_node_way_elements))
    pprint.pprint(users_in_node_way_elements)
    
    return users

# Test
def test():

    users = process_map('Alaska.xml')
    pprint.pprint(len(users))
    #pprint.pprint(len(users))
    #pprint.pprint(users)
    #assert len(users) == 6



if __name__ == "__main__":
    test()