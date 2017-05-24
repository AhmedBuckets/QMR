from flask import Flask, render_template, request
import requests, urllib, json, openpyxl, forecastio, datetime
from sklearn import tree
from datetime import timedelta
import math, decimal, datetime

dec = decimal.Decimal

def nextNewMoon(dude): # function to find the date of the next new moon
	now = datetime.datetime.now() # current datetime object
	date = now + timedelta(days=dude) # current + incremented day; starts out day = 1
	dude += 1 # increment
	diff = date - datetime.datetime(2001,1,1)
	days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
	lunations = dec("0.20439731") + (days * dec("0.03386319269"))
	pos = lunations % dec(1)
	index = (pos * dec(8)) + dec("0.5")
	index = math.floor(index) # end result

	if int(index) & 7 == 0: # if index == 0, return the date of the new moon; else recurse with incremented "dude"
		return date # datetime is 1 or 2 days behind astronomical new moon but this is consistent
	else:
		date = nextNewMoon(dude)
		return date



def NewMoonDate (lat, longo, vis, bruh, count):
    api_key = '6f09e93c28433f8f39de463b2a6d233d'
    date = nextNewMoon (dude=0) 
    d = date + timedelta(days=count) # increment 2 days (we started with count = 2) to datetime fetched by nextNewMoon
    forecast = forecastio.load_forecast(api_key, lat, longo, time=d)
    count += 1
    daily = forecast.daily()
    print(count)
    print(str(d))

    if daily.data: # if daily data exists, perform loop, else call function for nearby coordinates until daily data is found
        for i in daily.data: # for each value in daily data
            try:    # Try retrieving values, else if errors are found, perform exception handling
                vis = float (i.visibility)
                bruh = float (i.cloudCover)
                print(i.time) # print to make sure we're making api calls for the date we want
                return vis, bruh
            except Exception: 
                print("exception")
                vis, bruh = NewMoonDate (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, bruh, count)
                return vis, bruh
    else:
        vis, bruh = NewMoonDate (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, bruh, count)
        return vis,bruh

wb = openpyxl.load_workbook('finalML.xlsx')  # open the workbook

ws = wb.get_sheet_by_name("Sheet1")  # ws is a sheet object, this sets the active sheet to sheet1, the only sheet

biglist = []  # create a "master list" - this will be a list of lists

ylist = []  # another list- this will be a list of yes/no

for x in range(1, 1271):

    xlist = []  # list created for each row
    e = ws.cell(row=x, column=6).value  # get the value of the 7th column for each row, which contains the yes/no values
    ylist.append(e)  # append the yes/no value in ylist

    for y in range(1, 6):  # for every row, iterate through the 5 columns
        d = ws.cell(row=x, column=y).value  # get value at each column
        xlist.append(str(d))  # append the value to xlist

    biglist.append(xlist)  # append xlist to biglist

    x = biglist
    y = ylist


''' Decision Tree '''

clf = tree.DecisionTreeClassifier() # function is mostly the same as naive bayes
clf.fit(biglist, ylist)



# declare some variables to use for our prediction
bruh = 0.0 # our cloud cover xD
vis = 0.0 # visbility
locale = "Hunter College"
r = requests.get('https://api.apixu.com/v1/forecast.json?key=97c321a02a564f80b82173440171504&q='+str(locale)+'&days=10')
jobj = r.json()

lat = jobj['location']['lat'] # get latitude n2017umbers
longo = jobj['location']['lon'] # get longitude numbers
print(lat)
print(longo)

dateobj = nextNewMoon(dude=0) # fetch datetime obj for date of next appearance of new moon
increDate = dateobj + timedelta(days=2) #increment fetched datetime by 2 days
strDate = str(increDate) # cast inreDate as string
date = strDate.split(" ") # split off the whitespace cause only the first part of the string is needed
print(date[0]) #print to make sure


forecast = jobj['forecast']['forecastday']
for i in forecast:
    # if the data is available in the JSON response from apixu API    
    if i['date'] == date[0]: # if the date of the next appearance of the new moon is within 10 days, use apixu
        print(i['date'])
        for a in i['hour']: # get our cloud cover and visibility data based on coordinates  
            cloud = float(a['cloud'])
            bruh += cloud
            visi = float(a['vis_miles'])
            vis += visi

        bruh = bruh/24
        bruh = (round(bruh))/100  # cloudCover from 1.00 to 0.00 per Dark Sky's specifications
        vis = vis/24
        vis = round(vis) # visibility in miles
        print("hi")
  
if vis == 0.0 and bruh == 0.0:
    vis, bruh = NewMoonDate (lat, longo, vis, bruh, count=2)
            
    # get our elevation
google_elevationURL = "https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," + str(longo) + "&key=AIzaSyAGCPPwV4D057vO26zDhDZex6JodJBIKyA"
with urllib.request.urlopen(google_elevationURL) as f:
    response = json.loads(f.read().decode())
status = response["status"]
result = response["results"][0]
elevation = float (result["elevation"])

print(int(vis))
print(bruh)

print(clf.predict([[lat, longo, int(vis), bruh, elevation]])) # our prediction'''
