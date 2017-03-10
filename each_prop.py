from bs4 import BeautifulSoup
import unicodedata
import re
import urllib2
import time
import sys
import random
import dataset

import sqlite3 as lite

#set the delay max for the url call
delay_for_request = 10

#datebase stuff
con = lite.connect('properties.db')
cur = con.cursor()
#create the table
#cur.execute("CREATE TABLE properties(street TEXT, city TEXT, state TEXT, zip INT, sq_ft INT, price INT, bedrooms INT, bathrooms INT, link text)")

#set all of them as not active to start
cur.execute("UPDATE properties SET active = 'no'")
con.commit()

#set up data set db stuff, hopefully using this in the future
db = dataset.connect('sqlite:///properties.db')
table = db['properties']


#this spilts the string based on seps and returns a list
def split(txt, seps):
    default_sep = seps[0]

    # we skip seps[0] because that's the default seperator
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]

#read the active property list url to query
with open('active_links_old.txt') as f:
    active_links = f.read().splitlines()

for link in active_links:
    detail_list = []    #the details of each property

    #load the beautifulsoup from the url html
    content = urllib2.urlopen(link).read()
    soup = BeautifulSoup(content, 'html.parser')


    #get the property address
    for ultag in soup.find_all('ul', {'class': 'list-inline list-inline--large'}):
        for litag in ultag.find_all('li'):
            temp = (split(litag.text, ('\n',)))
    for each in temp:
        if each is not u'' or '':
            each = str(each).replace(',','')       #remove commas
            detail_list.append(each)

    #get the cost, size and rooms
    non_decimal = re.compile(r'[^\d]+')
    for ultag in soup.find_all('ul', {'class': 'list-inline list-inline--with-delimiters list-inline--large'}):     #find the tag in the html
        for litag in ultag.find_all('li'):
            number_with_newlines =  non_decimal.sub('', str(litag.text))        #removes the junk from the results, leaving the numbers
            numbers = number_with_newlines.replace('\\n','')
            detail_list.append(numbers)

    #assign all values to the dictionary from the list
    property_details = {'street': detail_list[0] , 'city': detail_list[1], 'state' : detail_list[2], 'zip' : detail_list[3], 'price': detail_list[4], 'bedrooms': detail_list[5], 'bathrooms': detail_list[6], 'sq_ft': detail_list[7] }

    #fix the . in bathrooms like 2.5
    if len(property_details['bathrooms']) > 1:
        bathroom_characters =  list(property_details['bathrooms'])
        bathrooms = bathroom_characters[0]+'.' + bathroom_characters[1]
        property_details['bathrooms'] = bathrooms

    print property_details

    if table.find_one(street=property_details['street']) != None:
        print 'Already found it'
        continue
    else:
        print 'New Property!'

        #insert the property into the db
        cur.execute('''INSERT INTO properties(street, city, state, zip, sq_ft, price, bedrooms, bathrooms, link, active)
                   VALUES(?,?,?,?,?,?,?,?,?,?)''', (property_details['street'],property_details['city'],property_details['state'],property_details['zip'],property_details['sq_ft'],property_details['price'],property_details['bedrooms'],property_details['bathrooms'],link, 'yes'))


        #check to see if it is already in the database

        #write to the db
        con.commit()

    #makes it look more human, delays a random amount
    time.sleep(random.randint(1,delay_for_request))