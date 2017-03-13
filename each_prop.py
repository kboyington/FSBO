from bs4 import BeautifulSoup
import unicodedata
import re
import urllib2
import time
import os
import random
import dataset
import zillow

#get zillow key
with open("zillow_key.conf", 'r') as f:
    key = f.readline().replace("\n", "")

#set the delay max for the url call
delay_for_request = 10

#datebase stuff
#set up data set db stuff, hopefully using this in the future
db = dataset.connect('sqlite:///properties.db')

#create the table if it doesnt exist
if db.tables == []:
    db.query("CREATE TABLE properties(street TEXT, city TEXT, state TEXT, zip INT, sq_ft INT, price INT, bedrooms INT, bathrooms INT, link text, active text, zestimate INT, percentage_of_zestimate INT, price_per_foot INT)")

table = db['properties']


#set all of them as not active to start
db.query("UPDATE properties SET active = 'no'")

#get zestimate provided the address and zip
def get_zestimate(address, zip):
    try:
        api = zillow.ValuationApi()
        data = api.GetSearchResults(key, address, zip)
        return data
    except zillow.ZillowError as ze:
        #print ze
        return None


#this spilts the string based on seps and returns a list
def split(txt, seps):
    default_sep = seps[0]

    # we skip seps[0] because that's the default seperator
    for sep in seps[1:]:
        txt = txt.replace(sep, default_sep)
    return [i.strip() for i in txt.split(default_sep)]

#make a csv of the sqlite db for uploading to Google in the future
def make_csv():
    result = table.all()
    dataset.freeze(result, format='csv', filename='properties.csv')


#read the active property list url to query
with open('active_links.txt') as f:
    active_links = f.read().splitlines()

for link in active_links:
    #makes it look more human, delays a random amount
    time.sleep(random.randint(1,delay_for_request))

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

    print detail_list
    #get the cost, size and rooms
    non_decimal = re.compile(r'[^\d]+')
    for ultag in soup.find_all('ul', {'class': 'list-inline list-inline--with-delimiters list-inline--large'}):     #find the tag in the html
        for litag in ultag.find_all('li'):
            number_with_newlines =  non_decimal.sub('', str(litag.text))        #removes the junk from the results, leaving the numbers
            numbers = number_with_newlines.replace('\\n','')
            detail_list.append(numbers)

    #assign all values to the dictionary from the list
    property_details = {'street': detail_list[0] , 'city': detail_list[1], 'state' : detail_list[2], 'zip' : detail_list[3], 'price': detail_list[4], 'bedrooms': detail_list[5], 'bathrooms': detail_list[6], 'sq_ft': detail_list[7] }

    #get the price/sqft
    price_per_foot = (int(property_details['price'])/int(property_details['sq_ft']))
    print price_per_foot

    #get the full address of the property
    full_address = '{}, {}, {}'.format(property_details['street'],property_details['city'],property_details['state'])

    #get the zestimate for the property
    zestimate = get_zestimate(full_address, property_details['zip'])

    #make sure that it returns a real number
    if zestimate is not None:
        zest_price = zestimate.zestiamte.amount
        #dont know why but sometimes it is None, I think it is actually returned by zillow estimate as None
        if zest_price == None:
            zest_price = 0
            percentage_of_zestimate = 0
        else:
            #calculate the percentage of zestimate
            percentage_of_zestimate = int(float((float(property_details['price'])/float(zest_price)))*100)
    else:
        zest_price = 0
        percentage_of_zestimate = 0

    #fix the . in bathrooms like 2.5
    if len(property_details['bathrooms']) > 1:
        bathroom_characters =  list(property_details['bathrooms'])
        bathrooms = bathroom_characters[0]+'.' + bathroom_characters[1]
        property_details['bathrooms'] = bathrooms

    #print property_details

    if table.find_one(street=property_details['street']) != None:
        print 'Already found it'
        #update the table to reflect that it is active
        table.update(dict(street=property_details['street'], active='yes'), ['street'])
    else:
        print 'New Property!'
        #insert the property into the db
        table.insert(dict(street=property_details['street'], city=property_details['city'], state=property_details['state'] , zip= property_details['zip'], sq_ft=property_details['sq_ft'], price=property_details['price'], bedrooms=property_details['bedrooms'], bathrooms=property_details['bathrooms'], link=link, active='yes', zestimate=zest_price, percentage_of_zestimate=percentage_of_zestimate, price_per_foot=price_per_foot))


make_csv()
