from flask import Flask, render_template, request
import requests, urllib, json, openpyxl, forecastio, datetime, math, decimal
from sklearn import svm
from datetime import timedelta

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

''' Using sklearn to build classifier '''

clf = svm.SVC()
clf.fit(biglist, ylist)





''' function to find the date of the next new moon '''

dec = decimal.Decimal

def nextNewMoon(d): 
	now = datetime.datetime.now() # current datetime object
	date = now + timedelta(days=d) # current + incremented day; starts out day = 2
	d += 1 # increment
	diff = date - datetime.datetime(2001,1,1)
	days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
	lunations = dec("0.20439731") + (days * dec("0.03386319269"))
	pos = lunations % dec(1)
	index = (pos * dec(8)) + dec("0.5")
	index = math.floor(index) # end result

	if int(index) & 7 == 0: # if index == 0, return the date of the new moon; else recurse with incremented "d"
		return date # datetime is 1 or 2 days behind astronomical new moon but this is consistent
	else:
		date = nextNewMoon(d)
		return date



''' function to fetch cc and vis data via apixu API call '''

def apixu (locale):
	r = requests.get('https://api.apixu.com/v1/forecast.json?key=insert key here='+str(locale)+'&days=10')
	jobj = r.json()

	lat = jobj['location']['lat'] # get latitude numbers
	longo = jobj['location']['lon'] # get longitude numbers

	dateobj = nextNewMoon(d=0) # fetch datetime obj for date of next appearance of new moon
	increDate = dateobj + timedelta(days=2) # increment fetched datetime by 2 days
	strDate = str(increDate) # cast inreDate as string
	date = strDate.split(" ") # "split" based on whitespace

	cc = 0.0 # our cloud cover
	vis = 0.0 # visbility

	forecast = jobj['forecast']['forecastday']
	for i in forecast:
        # if the data is available in the JSON response from apixu API
		if i['date'] == date[0]: # Date of New Moon
			for a in i['hour']: # get our cloud cover and visibility data based on coordinates  
				cloud = float(a['cloud'])
				cc += cloud # because apixu returns "cloud" 24 times for each hour, we'll add to cc after every loop, and then divide by 24 later
				visi = float(a['vis_miles'])
				vis += visi # same deal, add, then divide by 24 later

			cc = cc/24 # get average cloudcover because apixu returns cloudcover for each and all 24 hours of that day
			cc = (round(cc))/100  # divide cloudCover by 100 to get range from 1.00 to 0.00 per Dark Sky's specifications
			vis = vis/24 # get average visibility because same deal as apixu
			vis = round(vis) # visibility in miles

	return vis, cc, lat, longo



''' function to fetch cc and vis data via Dark Sky API call '''

def DarkSky (lat, longo, vis, cc, count):
	api_key = 'insert key here'
	date = nextNewMoon (d=0) 
	d = date + timedelta(days=count) # needed for recursion, count 
	forecast = forecastio.load_forecast(api_key, lat, longo, time=d)
	count += 1 # increment count, this will happen every recursion
	daily = forecast.daily()
	cc = 0.0 # cloud cover
	vis = 0.0 # visbility

	if daily.data: # if daily data exists, perform loop, else execute recursive function call for nearby coordinates on the next concurrent day until daily data is found
		for i in daily.data: # for each value in daily data
			try:    # Try retrieving values, else if errors are found, perform exception handling
				vis = float (i.visibility)
				cc = float (i.cloudCover)
				return vis, cc
			except Exception:
				vis, cc = DarkSky (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, cc, count)
				return vis, cc
	else:
		vis, cc = DarkSky (str (float (lat) - 1.00), str (float (longo) - 1.00), vis, cc, count)
		return vis, cc



''' function to fetch elevation data via Google Maps Elevation API call '''

def fetch_elevation (lat, long):
	google_elevationURL = "https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," + str(long) + "&key=insert key here"
	# parsing through JSON response
	with urllib.request.urlopen(google_elevationURL) as f:
		response = json.loads(f.read().decode())
	status = response["status"]
	result = response["results"][0]
	elevation = float (result["elevation"]) # cast elevation data as float
	return round(elevation, 2) # return elevation at two decimal places





''' Flask implementation '''

app = Flask(__name__)

@app.route("/apixu", methods = ['POST'])
def main(): # think of this like in c++ int main function

	locale = request.form["location"] # user input
	vis, cc, lat, longo = apixu (locale) # fetch visibility, cloudcover, latitude, and longitude via Apixu API call

	if vis == 0.0 and cc == 0.0: # if no visibility and cloudcover data fetched by apixu function call, execute Dark Sky call
		vis, cc = DarkSky (lat, longo, vis, cc, count = 2) # count = 2 for timedelta because new moon algorithm is behind 2 days

	elevation = fetch_elevation(lat, longo) # fetch elevation data

	prediction = str(clf.predict([[lat, longo, int(vis), cc, elevation]])) # our prediction
	prediction = prediction[2:-2]

	''' get the date of the astronomical new moon and next following day '''
	dateobj = nextNewMoon(d=0) # fetch date of next upcoming new moon; 2 days behind so we'll use timedelta to add "days" to the "date"
	''' next following day '''
	increDate = dateobj + timedelta(days=3)
	strDate = str(increDate)
	date = strDate.split(" ") # have to "split" because datetime obj contains hours and seconds which we dont want
	''' astronomical new moon '''
	increDate2 = dateobj + timedelta(days=2)
	strDate2 = str(increDate2)
	date2 = strDate2.split(" ")

	return render_template('apixu.html', predict = prediction, lat=lat, longo=longo, elevation=elevation, bruh=cc, vis=vis, date=date[0], astronomicalNewMoon=date2[0], location=locale)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()