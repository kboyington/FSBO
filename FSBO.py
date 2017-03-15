from bs4 import BeautifulSoup
import random
import re
import urllib2
import time

number_of_pages = 15
current_page = 1
delay_for_request = 10   #sets the max time to wait


link_list = []  # create a list of all the links

while current_page <= number_of_pages:
    time.sleep(random.randint(1,delay_for_request))
    url = 'http://www.forsalebyowner.com/search/list/Indiana/fsbo-source/:150000-price/{}-page/proximity,desc-sort'.format(current_page)
    content = urllib2.urlopen(url).read()
    current_page = current_page+1
    soup = BeautifulSoup(content, "html.parser")

    #find all the links
    for a in soup.findAll('a',href=True):
        if re.findall('/listing/', a['href']):
            if a['href'] not in link_list:
                link_list.append(a['href'])

    time.sleep(5)

#wite all results to file
with open('active_links.txt', 'w') as results:
    for each in link_list:
        print each
        results.write(each+'\n')
