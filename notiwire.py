# -*- coding: utf-8 -*-

# Online Notiwire
# middlelayer between Online Notifier and OmegaV NotiPis
# appKom: appkom@online.ntnu.no
# author: michael@informatikk.org

# Test Notiwire by pretending to be a NotiPi:
# curl --data "light=on" http://online.ntnu.no/nabla/light
# curl --data "pots=5&datetime=5. March 2014 12:14:01" http://online.ntnu.no/solan/coffee

from flask import Flask, request
import os
import re

# Initialize the Flask application
app = Flask('Online Notiwire')

# Paths
morganPath = '/Users/michael/Dropbox/Desktop/'
# morganPath = '/var/websites/notifier' # christyo bytt til denne
lightPath = '/light'
coffeePath = '/coffee'

# Messages
msgError = "ERROR: nooo... nooo...misa superman no home...nooo...."
msgAffiliation = "ERROR: nooo....misa linjeforening no exist...nooo"
msgLightMissing = "ERROR: nooo....misa light no here....nooo"
msgLightMalformed = "ERROR: nooo....misa light no good....noooo"
msgPotsMissing = "ERROR: nooo....misa coffeepots no here...noooo"
msgPotsMalformed = "ERROR: nooo....misa coffeepots no good...noooo"
msgDatetimeMissing = "ERROR: nooo....misa datetime no here....noooo"
msgDatetimeMalformed = "ERROR: nooo....misa datetime no valid....noooo"

@app.route("/")
def hello():
    return '<pre> Hey, welcome to Online Notiwire,<br /> middlelayer for Online Notifier.<br /> It is an API for OmegaV NotiPis.<br /> <br /> Say hi at <a href="mailto:appkom@online.ntnu.no">appkom@online.ntnu.no</a>.<br /> </pre>'

def checkAffiliation(affiliation):
	# Affiliations must be updated once in a while.
	# A shell script for getting all affiliations is provided.
	affiliations = [
		"abakus","alf","berg","delta","emil","aarhonen","hybrida","leonardo","mannhullet","online","nabla","solan","spanskroeret","volvox","dhs","dionysos","erudio","eureka","geolf","gengangere","jump cut","ludimus","paideia","panoptikon","pareto","primetime","psi","sturm und drang","utopia","dion","esn","iaeste","isu","projeksjon","soma","symbiosis","fraktur","kom","logistikkstudentene","nutrix","tihlde","tim og shaenko","tjsf","vivas","dusken","universitetsavisa","gemini","adressa","samfundet","velferdstinget","studentparlamentet hist","studenttinget ntnu","ntnu","rektoratet ntnu","hist","dmmh",
	]
	return affiliation in affiliations

def checkLight(light):
	return light == "on" or light == "off"

def checkPots(pots):
	try:
		pots = int(pots)
		return 1 <= pots and pots <= 1000
	except ValueError:
		return False

def checkDatetime(datetime):
	# Regex it
	try:
		matches = re.match(r"^\d{1,2}\. \w+ \d{4} \d{2}:\d{2}:\d{2}$", datetime)
		# Error thrown here
		hit = matches.group(0)
		return True
	except AttributeError:
		return False

def datetimeTests():
	# Simple tests for confirming correct checking of datetime
	testfail = 'ERROR: datetime test failed, number '
	if checkDatetime('test') == True:
		print(testfail + str(1))
		return False
	if checkDatetime('101. March 2014 10:12:14') == True:
		print(testfail + str(2))
		return False
	if checkDatetime('10. March Test 2014 10:12:14') == True:
		print(testfail + str(3))
		return False
	if checkDatetime('10. March 201451 10:12:14') == True:
		print(testfail + str(4))
		return False
	if checkDatetime('10. March 2014 10::12:14') == True:
		print(testfail + str(5))
		return False
	if checkDatetime('10. March 2014 10:1222:14') == True:
		print(testfail + str(6))
		return False
	if checkDatetime('10..March 2014 10:1222:14') == True:
		print(testfail + str(7))
		return False
	if checkDatetime('10. March 2014 10:12:14123') == True:
		print(testfail + str(8))
		return False
	return True

def writeFile(filename, stringToWrite):
	try:
		if not os.path.exists(os.path.dirname(filename)):
		    print('Notiwire: New affiliation path created, ' + filename)
		    os.makedirs(os.path.dirname(filename))
		with open(filename, "w") as f:
			f.write(stringToWrite)
		return True
	except:
		print "Notiwire: Unexpected error:", sys.exc_info()[0]
		return False

# This route accepts POST requests
@app.route('/<string:affiliation>/light', methods=['POST'])
def postLight(affiliation):
	if not checkAffiliation(affiliation):
		return msgAffiliation

	# Retrieve light
	if not 'light' in request.form.keys():
		return msgLightMissing
	light = request.form['light']
	if not checkLight(light):
		return msgLightMalformed

	# Write to file
	filename = morganPath + affiliation + lightPath
	if writeFile(filename, light):
		return "CONFIRMED! READBACK:\nThe light at " + affiliation + "'s office is " + light
	else:
		return "DENIED! Unable to write"

# This route accepts POST requests
@app.route('/<string:affiliation>/coffee', methods=['POST'])
def postCoffee(affiliation):
	if not checkAffiliation(affiliation):
		return msgAffiliation

	# Retrieve pots
	if not 'pots' in request.form.keys():
		return msgPotsMissing
	pots = request.form['pots']
	if not checkPots(pots):
		return msgPotsMalformed

	# Retrieve datetime
	if not 'datetime' in request.form.keys():
		return msgDatetimeMissing
	datetime = request.form['datetime']
	if not checkDatetime(datetime):
		return msgDatetimeMalformed

	# Write to file
	filename = morganPath + affiliation + coffeePath
	if writeFile(filename, pots + '\n' + datetime):
		return "CONFIRMED! READBACK:\n" + pots + " pots at " + affiliation + "'s office, last one at " + datetime
	else:
		return "DENIED! An error occured, tell the people at appkom@online.ntnu.no"

# Run the app :)
if datetimeTests():
	if __name__ == "__main__":
	    app.run(
	    	host="localhost",
	    	port=int("5000")
	    )
else:
	print('ERROR: a test failed, fix it plz')
