# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

#Script to clean up the given app data, scrap play store and get the relevant app information.
#17/4/2014
#hihari777@gmail.com

# <codecell>

#Open File in read mode.
file = open("/home/rage/Desktop/set_of_comma_seperated_app_names.txt", "r")

# <codecell>

#Reading everything into a string.
for apps in file:
    print apps

# <codecell>

#Removing some common punctuation.
clean_apps = apps.translate(None, "$&'.!@#%^*:/[];-`~(){\"}")

# <codecell>

clean_apps = clean_apps.replace("Android", "").replace("iOS", "").replace("iPad", "").replace("iPhone", "")

# <codecell>

#Something I noticed is that many app names which are given together should actually be split up.
#eg. "Android SkypeLovers" should actually be "Skype Lovers". 
#Thankfully easy to solve using regular expressions.
import re
clean_apps = re.sub(r"(\w)([A-Z])", r"\1 \2", clean_apps)

# <codecell>

#Unfortunately the above step seperates some initials in a bad way. eg. "Caller I D Block" must be "Caller ID Block".
#We solve this easily by means of a regular expression.
clean_apps = re.sub(r"([A-Z]) ([A-Z])", r"\1\2", clean_apps)
#Yay I learn to use regular expressions. Damn they are incredibly usefull :)

# <codecell>

#We still have mixed case characters. Convert them all to lower case.
clean_apps = clean_apps.lower()

# <codecell>

#Removing extra spaces in string.
clean_apps = " ".join(clean_apps.split())

# <codecell>

#Splitting our clean input into individual apps using comma as the seperator.
app = clean_apps.split(",")

# <codecell>

#We now need to remove exact duplicates.
#We use set to easily remove them. Convert to set and back to list.
final_app = list(set(app))

# <codecell>

#Removed first space in every app name.
final_app = [s[1:] for s in final_app]

# <codecell>

#General cleaning up done.
#We now face two problems:
#1. Same apps but difference in names. eg. Skout and Skout iOS refer to the same app. The iOS and Android extensions can be rectified by just removing them on found instances because I dont find platform as an important attribute for this task. eg. It doesnt matter if I search Truecaller on iOS or Android as the attributes I require are the same on both.
#2. Spelling Errors. eg. Skout and Scout may come up. I find the SequenceMatcher in Pythons difflib library to be good for this purpose. Names whose ratio's are above a certain threshold maybe considered as the same app. Anything above that maybe considered similar.
#Various approaches I took will be discussed later.
#Also the first word in each string in the list will be taken as the main word(ref Pycon 2013 talk).

# <codecell>

#Removing the Android, iOS instances.
final_app_clean = [s.replace("android", "").replace("ios", "").replace("ipad", "").replace("iphone", "") for s in final_app]

# <codecell>

#Removing spelling duplicates. This step can be used to remove the Android and iOS instances too as the 70 threshold holds on those instances too.
#eg. Instances where Android is mispelled as ndroid needs to be removed. eg. 'ndroid skout new' and 'skout' and 'skout' new are the same. 
#My logic is the eliminate the long string and maintain the short string. Maintaining the shorter string would work well for this data set but I think maintaining the longer set would be better in some datasets.
#Above logic may have to be corrected.
#Logic done properly below. These comments can be ignored.

# <codecell>

#Sorting the list. This step is unnecessary.
final_app_clean.sort()

# <codecell>

#We need to decode the list so that we can remove garbage values in string.
final_app_clean = [s.decode('string_escape') for s in final_app_clean]

# <codecell>

#Need to remove some garbage data from string. eg. eather\xc2\xb0 needs to be eather.
final_app_clean = [filter(lambda x: ord(x) < 128, s) for s in final_app_clean]
print final_app_clean

# <codecell>

#Now we use the FuzzyWuzzy(yeah funny name !) library to remove nearly matching app names.
#The library is available at https://github.com/seatgeek/fuzzywuzzy
#pip install fuzzywuzzy
#Excellent overview of its features available at http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
from fuzzywuzzy import fuzz
#Use the token_set_ratio for this purpose. It takes care of the "Out of Order" problem and does partial string matching.
#eg. fuzz.token_set_ratio("skout", "ndroid skout new") = 100 !! Perfect match !!
#I found 65 to be a good threshold.
for i in range(0, len(final_app_clean) - 1):
    for j in range((i+1), len(final_app_clean)):
        if(fuzz.token_set_ratio(final_app_clean[i], final_app_clean[j]) >= 65):
            if(len(final_app_clean[i]) < len(final_app_clean[j])):
                final_app_clean[j] = ""
            else:
                final_app_clean[i] = ""

# <codecell>

#Remove the added ''.
final_app_clean = filter(lambda x: len(x) > 0, final_app_clean)
final_app_clean = [s.strip() for s in final_app_clean]

# <codecell>

#Usually _ represents a space
final_app_clean = [s.replace("_", " ") for s in final_app_clean]
print final_app_clean

# <codecell>

#Copy of final cleaned result.
search_names = final_app_clean

# <codecell>

#Scraping starts. Doing only Android store now.
from bs4 import BeautifulSoup
from urllib2 import urlopen

BASE_URL = "https://play.google.com"

# <codecell>

#Getting search result links.
#Threshold set to 30. Google play search results are extremely accurate.
def get_search_links(section_url, name):
    html = urlopen(section_url).read()
    soup = BeautifulSoup(html, "lxml")
    a_tag = soup.find("a", "title")
    if a_tag is None:
        a_href = "No information found in the play store for " + name 
        return a_href
    a_title = a_tag.get('title')
    if(fuzz.token_set_ratio(a_title.lower(), name) >= 30):
        a_href = a_tag.get('href')
    else:
        a_href = "No information found in the play store for " + name
    return a_href
#print get_search_links("https://play.google.com/store/search?q=a%20kingdomtactics", "a kingdomtactics")

# <codecell>

#Creating a list of search url's for google play.
#My technique is to do an actual search for each app, scan the titles of the search results and do a string matching algorithm on them(eg. Levenshtein distance).
#If a match comes up, follow that url and extract app details.
#I'm trusting Google's first result to be correct. In any case I do string matching inc ase there are no correct results. The ideal way should be to return all links in the search result and do string matching on all of them and take the one with the best score. But from expeirence I found the search to be very accurate.
search_names_for_links = [s.replace(" ", "%20") for s in search_names]
search_links = ["https://play.google.com/store/search?q=" + s + "&c=apps" for s in search_names_for_links]

# <codecell>

#Will contain the app link.
app_result_page_links = []

# <codecell>

#Now we have to create a list containing the app links.
import itertools
for name, link in itertools.izip(search_names, search_links):
    app_result_page_links.append(get_search_links(link, name))
    print app_result_page_links[-1]

# <codecell>

#appending domain.
app_result_page_links_complete = ["https://play.google.com" + s for s in app_result_page_links]

# <codecell>

#Takes each app link found above and scraps the relevant information.
def get_app_details(app_link):
    if "No information found in the play store for" in app_link:
        return None
    html = urlopen(app_link).read()
    soup = BeautifulSoup(html, "lxml")
    name = soup.find("div", "document-title").div.string
    category = soup.find("a", "document-subtitle category").span.string
    rating =  soup.find("div", "score").text
    rating_number = soup.find("span", attrs = {"class" : "reviews-num"}).string
    downloads = soup.find("div", attrs = {"class" : "content", "itemprop" : "numDownloads"}).string
    return {"name" : name,
            "category" : category,
            "rating" : rating,
            "rating_number" : rating_number,
            "downloads" : downloads}

# <codecell>

#Calling the above function and storing it to a list. Result is a list of dicts.
final_app_details = []
for s in app_result_page_links_complete:
    final_app_details.append(get_app_details(s))
    print final_app_details[-1]

# <codecell>

#Removing dicts from list for which no information was found.
final_app_details = [s for s in final_app_details if s is not None]
print final_app_details

# <codecell>

#Woohoo it works :)

