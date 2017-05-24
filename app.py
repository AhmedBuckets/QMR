from flask import Flask, render_template, request
import requests, urllib, json, openpyxl, forecastio, datetime, math, decimal
from sklearn import tree
from sklearn import svm
from datetime import timedelta


dec = decimal.Decimal

''' function to find the date of the next new moon '''

def nextNewMoon(dude): 
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

''' function to fetch data via Dark Sky API call '''

def NewMoonDate (lat, longo, vis, bruh, count):
    api_key = 'insert key here'
    date = nextNewMoon (dude=0) 
    d = date + timedelta(days=count) # increment 2 days to datetime fetched by nextNewMoon
    forecast = forecastio.load_forecast(api_key, lat, longo, time=d)
    count += 1
    daily = forecast.daily()

    if daily.data: # if daily data exists, perform loop, else call function for nearby coordinates until daily data is found
        for i in daily.data: # for each value in daily data
            try:    # Try retrieving values, else if errors are found, perform exception handling
                vis = float (i.visibility)
                bruh = float (i.cloudCover)
                return vis, bruh
            except Exception:
                vis, bruh = NewMoonDate (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, bruh, count)
                return vis, bruh
    else:
        vis, bruh = NewMoonDate (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, bruh, count)
        return vis,bruh


''' Exporting the data from our workbook '''

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

clf = svm.SVC() # function is mostly the same as naive bayes
clf.fit(biglist, ylist)


app = Flask(__name__)

@app.route("/apixu", methods = ['POST'])
def main():
    # declare some variables to use for our prediction
    bruh = 0.0 # our cloud cover xD
    vis = 0.0 # visbility
    locale = request.form["location"]
    r = requests.get('https://api.apixu.com/v1/forecast.json?key=insert key here &q='+str(locale)+'&days=10')
    jobj = r.json()

    lat = jobj['location']['lat'] # get latitude numbers
    longo = jobj['location']['lon'] # get longitude numbers

    dateobj = nextNewMoon(dude=0) # fetch datetime obj for date of next appearance of new moon
    increDate = dateobj + timedelta(days=3) # increment fetched datetime by 2 days
    strDate = str(increDate) # cast inreDate as string
    date = strDate.split(" ")

    forecast = jobj['forecast']['forecastday']
    for i in forecast:
        # if the data is available in the JSON response from apixu API
        if i['date'] == date[0]: # Date of New Moon 2017
            for a in i['hour']: # get our cloud cover and visibility data based on coordinates  
                cloud = float(a['cloud'])
                bruh += cloud
                visi = float(a['vis_miles'])
                vis += visi

            bruh = bruh/24
            bruh = (round(bruh))/100  # cloudCover from 1.00 to 0.00 per Dark Sky's specifications
            vis = vis/24
            vis = round(vis) # visibility in miles
    
    if vis == 0.0 and bruh == 0.0:
        vis, bruh = NewMoonDate (lat, longo, vis, bruh, count = 2)
    
            
    # get our elevation
    google_elevationURL = "https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," + str(longo) + "&key=insert key here"
    with urllib.request.urlopen(google_elevationURL) as f:
        response = json.loads(f.read().decode())
    status = response["status"]
    result = response["results"][0]
    elevation = float (result["elevation"])

    prediction = str(clf.predict([[lat, longo, int(vis), bruh, elevation]])) # our prediction
    prediction = prediction[2:-2]



    '''get the date of the astronomical new moon'''
    increDate2 = dateobj + timedelta(days=2)
    strDate2 = str(increDate2)
    date2 = strDate2.split(" ")
    
    astronomicalNewMoon = date2[0]

    roundElev = round(elevation, 2)

    return render_template('apixu.html', predict = prediction, lat=lat, longo=longo, elevation=roundElev, bruh=bruh, vis=vis, date=date[0], astronomicalNewMoon=astronomicalNewMoon, location=locale)



@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()