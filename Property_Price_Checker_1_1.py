#!/usr/bin/env python
# coding: utf-8

# # Property Price Guide Fetcher
# This script allows you to find the price range for a given property listed on [Domain.com.au](https://www.domain.com.au/) where there is no price provided by the agent.
# It does this by retrieving a property's details then performing a series of searches for different price ranges until it finds the upper and lower limits.
# 
# See [Medium post](https://medium.com/@alexdambra/how-to-get-aussie-property-price-guides-using-python-the-domain-api-afe871efac96).
# 
# *Developed by [Alex D'Ambra](https://www.linkedin.com/in/alexdambra/)*
# *Updated by [Chris Bashall](https://bashallc.github.io/home/)*
# 
# ---

# Import required libraries

# In[16]:


import json
import requests # this library is awesome: http://docs.python-requests.org/en/master/
import re, string, timeit
import time
import datetime
import csv


# **Setup your parameters**
# 
# 1.   Set your property ID. You can grab from end of the listing's URL.
#       *eg. https://www.domain.com.au/132a-prince-edward-avenue-earlwood-nsw-2206-2014925785*
# 2.   Set your starting lower bound eg. 500k starting max price. The starting min price will default to your lower bound plus 400k, or you can set this manually. This will reduce the amount of API calls required.
# 3.   Set your increment value. This will increase/decrease the starting prices by this amount until a hit is made. eg. 50k. Smaller increments might be more accurate but increase API calls. Most agents would probably set guides in $50-100k increments one would assume anyway (can you tell I live in Sydney...)
# 
# 
# 
# 
# 
# 
# 
# 
# 

# In[30]:


# setup
property_id="2016191506"
starting_max_price=1000000
increment=10000
# when starting min price is zero we'll just use the lower bound plus 400k later on
starting_min_price=0


# Provide your client credentials as per your [Domain](https://developer.domain.com.au) developer account.
# 
# Required: `client_id` and `client_secret`
# 
# Make a POST request to receive token.

# In[31]:


# POST request for token
response = requests.post('https://auth.domain.com.au/v1/connect/token', data = {'client_id':<yourclientiD>,"client_secret":<clientSecret>,"grant_type":"client_credentials","scope":"api_listings_read","Content-Type":"text/json"})
token=response.json()
access_token=token["access_token"]
access_token


# Make a GET request to the listings endpoint to retrieve listing info for your selected property.

# In[32]:


# GET Request for ID
url = "https://api.domain.com.au/v1/listings/"+property_id
auth = {"Authorization":"Bearer "+ access_token}
request = requests.get(url,headers=auth)
print(request)
r=request.json()


# Extract property details

# In[33]:


#get details
da=r['addressParts']
postcode=da['postcode']
suburb=da['suburb']
bathrooms=r['bathrooms']
bedrooms=r['bedrooms']
dateListed =r['dateListed']
date = datetime.datetime.today().strftime('%Y-%m-%d')
last_updated = r['dateUpdated']
agent = r['advertiserIdentifiers']

try:
    carspaces=r['carspaces']
except Exception:
    print("car spaces not provided")
    carspaces=-1
    pass

property_type=r['propertyTypes']
try:
    size=r['landAreaSqm']
except Exception:
    print("size not provided")
    size=-1
    pass

try:
    print(property_type,postcode, suburb, bedrooms, bathrooms,  carspaces)
except Exception:
    pass
# the below puts all relevant property types into a single string. eg. a property listing can be a 'house' and a 'townhouse'
n=0
property_type_str=""
for p in r['propertyTypes']:
  property_type_str=property_type_str+(r['propertyTypes'][int(n)])
  n=n+1
    
status = r['status']
lat = (r['geoLocation'].get('latitude')) 
long = (r['geoLocation'].get('longitude')) 
    


# Now loop through a series of POST requests that search for your property starting with your starting max price, increasing by your increment each time until you get a result. 
# 
# We achieve this by using a `do while` loop. After receiving a response we put the list of property IDs into a Python list and then check if our original property_id is in that list. 

# In[34]:


max_price=starting_max_price
searching_for_price=True


# In[35]:


# Start your loop
while searching_for_price:
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here
    post_fields ={
      "listingType":"Sale",
        "maxPrice":max_price,
        "pageSize":100,
      "propertyTypes":property_type,
      "minBedrooms":bedrooms,
        "maxBedrooms":bedrooms,
      "minBathrooms":bathrooms,
        "maxBathrooms":bathrooms,
      "locations":[
        {
          "state":"",
          "region":"",
          "area":"",
          "suburb":suburb,
          "postCode":postcode,
          "includeSurroundingSuburbs":False
        }
      ]
    }

    request = requests.post(url,headers=auth,json=post_fields)

    l=request.json()
    listings = []
    for listing in l:
        listings.append(listing["listing"]["id"])
    listings

    if int(property_id) in listings:
            max_price=max_price-increment
            print("Lower bound found: ", max_price)
            searching_for_price=False
    else:
        max_price=max_price+increment
        print("Not found. Increasing max price to ",max_price)
        time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly  
        if max_price > 1200000:
            break


# Now do the same but from the upper end begining with your starting min price and decreasing by your increment. This will get us an upper bound.

# In[36]:


searching_for_price=True
if starting_min_price>0:
  min_price=starting_min_price
else:  
  min_price=max_price+200000  


# In[37]:


while searching_for_price:
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here
    post_fields ={
      "listingType":"Sale",
        "minPrice":min_price,
        "pageSize":100,
      "propertyTypes":property_type,
      "minBedrooms":bedrooms,
        "maxBedrooms":bedrooms,
      "minBathrooms":bathrooms,
        "maxBathrooms":bathrooms,
      "locations":[
        {
          "state":"",
          "region":"",
          "area":"",
          "suburb":suburb,
          "postCode":postcode,
          "includeSurroundingSuburbs":False
        }
      ]
    }

    request = requests.post(url,headers=auth,json=post_fields)

    l=request.json()
    listings = []
    for listing in l:
        listings.append(listing["listing"]["id"])
    listings

    if int(property_id) in listings:
            min_price=min_price+increment
            print("Upper bound found: ", min_price)
            searching_for_price=False
    else:
        min_price=min_price-increment
        print("Not found. Decreasing min price to ",min_price)
        time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly     
       


# Format your numbers for your final string.

# In[38]:


if max_price<1000000:
  lower=max_price
  upper=min_price
  denom="k"
else: 
  lower=max_price/1000000
  upper=min_price/1000000
  denom="m"


# Print your results!

# In[39]:


# Print the results
print(da['displayAddress'])
print(r['headline'])
print("Property Type:",property_type_str)
print("Details: ",int(bedrooms),"bedroom,",int(bathrooms),"bathroom",int(carspaces),"carspace")
print("Display price:",r['priceDetails']['displayPrice'])      
if max_price==min_price:
  print("Price guide:","$",lower)
  print("$",int(lower/size))
else:
  print("Price range:","$",lower,"-","$",upper)
  print("$",int(lower/size)," - ","$",int(upper/size))
print("URL:",r['seoUrl'])
print("total size  :",size," sqm")


# In[40]:


## add to csv file




fields=[property_id,date,r['seoUrl'],da['displayAddress'],r['priceDetails']['displayPrice'],
        lower,upper,lower/size,upper/size,size,bedrooms,bathrooms,dateListed,last_updated,status,lat,long]
with open(r'results.csv', 'a') as f:
  writer = csv.writer(f)
  writer.writerow(fields)


# In[41]:


####suburb details


# In[42]:


r


# In[ ]:




