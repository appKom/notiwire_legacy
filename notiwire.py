# -*- coding: utf-8 -*-

# Online Notiwire
# middlelayer between Online Notifier and OmegaV NotiPis
# appKom: appkom@online.ntnu.no

# Test Notiwire by pretending to be a NotiPi:
# curl --data "light=on" http://online.ntnu.no/nabla/light
# curl --data "pots=5&datetime=5. March 2014 12:14:01" http://online.ntnu.no/solan/coffee


import os
import re
import sqlite3
import sys

from flask import Flask, request, g
from utils import ReverseProxied


# import settings
if not os.path.exists(os.path.join(os.path.dirname(globals()['__file__']), 'settings.py')):
    sys.stderr.write("Failed to locate the settings file. Quitting.\n")
    sys.exit(1)
try:
    from settings import *
except ImportError:
    sys.stderr.write("Failed to import from the settings file. Quitting.\n")
    sys.exit(1)


# Initialize the Flask application
app = Flask('Online Notiwire')

# Paths
lightPath = '/light'
coffeePath = '/coffee'
databasePath= os.path.join(app.root_path, 'notiwire.db')

# Messages
msgError = "ERROR: nooo... nooo...misa superman no home...nooo...."
msgAffiliation = "ERROR: nooo....misa linjeforening no exist...nooo"
msgLightMissing = "ERROR: nooo....misa light no here....nooo"
msgLightMalformed = "ERROR: nooo....misa light no good....noooo"
msgPotsMissing = "ERROR: nooo....misa coffeepots no here...noooo"
msgPotsMalformed = "ERROR: nooo....misa coffeepots no good...noooo"
msgApiKeyMissing = "ERROR: nooo....misa api key no here...noooo"
msgApiKeyMalformed = "ERROR: nooo....misa api key no good...noooo"
msgDatetimeMissing = "ERROR: nooo....misa datetime no here....noooo"
msgDatetimeMalformed = "ERROR: nooo....misa datetime no valid....noooo"

@app.route("/")
def hello():
    return '<pre> Hey, welcome to Online Notiwire,<br /> middlelayer for Online Notifier.<br /> It is an API for OmegaV NotiPis.<br /> <br /> Say hi at <a href="mailto:appkom@online.ntnu.no">appkom@online.ntnu.no</a>.<br /> </pre>'

def connectDB():
    rv = sqlite3.connect(databasePath)
    rv.row_factory = sqlite3.Row
    return rv

def getDB():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connectDB()
    return g.sqlite_db

def closeDB():
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def initDB():
    with app.app_context():
        db = getDB()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def setApiKey(affiliation, apiKey):
    '''
    Adds/updates an api key for an affiliation
    '''
    if not checkAffiliation(affiliation):
        return msgAffiliation
    if not apiKey:
        return msgApiKeyMissing

    with app.app_context():
        db = getDB()
        try:
            db.execute('INSERT INTO affiliation_keys (affiliation, key) VALUES (?, ?)', [affiliation, apiKey])
            print('Added api key')
        except sqlite3.IntegrityError:
            # Key already exists, updating
            db.execute('UPDATE affiliation_keys SET key = ? WHERE affiliation = ?', [apiKey, affiliation])
            print('Updated api key')
        db.commit()


def checkAffiliation(affiliation):
    # Affiliations must be updated once in a while.
    # A shell script for getting all affiliations is provided.
    affiliations = [
        "DEBUG","abakus","alf","berg","delta","emil","aarhonen","hybrida","leonardo","mannhullet","online","nabla","solan","spanskroeret","volvox","de_folkevalgte","dhs","dionysos","erudio","eureka","geolf","gengangere","jump_cut","ludimus","paideia","panoptikon","pareto","primetime","psi","sturm_und_drang","utopia","dion","esn","iaeste","isu","projeksjon","signifikant","soma","symbiosis","fraktur","kom","logistikkstudentene","nutrix","tihlde","tim_og_shaenko","tjsf","vivas","dusken","universitetsavisa","gemini","adressa","samfundet","velferdstinget","studentparlamentet_hist","studenttinget_ntnu","ntnu","rektoratet_ntnu","hist","dmmh",
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

def checkApiKey(affiliation, apiKey):
    db = getDB()
    cur = db.execute('SELECT * FROM affiliation_keys WHERE affiliation = ? AND key = ?', [affiliation, apiKey])
    result = cur.fetchone()
    return result != None

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

    if not 'api_key' in request.form.keys():
        return msgApiKeyMissing
    apiKey = request.form['api_key']
    if not checkApiKey(affiliation, apiKey):
        return msgApiKeyMalformed

    # Retrieve light
    if not 'light' in request.form.keys():
        return msgLightMissing
    light = request.form['light']
    if not checkLight(light):
        return msgLightMalformed

    # Write to file
    filename = FILE_PATH + affiliation + lightPath
    if writeFile(filename, light):
        return "CONFIRMED! READBACK:\nThe light at " + affiliation + "'s office is " + light
    else:
        return "DENIED! Unable to write"

# This route accepts POST requests
@app.route('/<string:affiliation>/coffee', methods=['POST'])
def postCoffee(affiliation):
    if not checkAffiliation(affiliation):
        return msgAffiliation

    if not 'api_key' in request.form.keys():
        return msgApiKeyMissing
    apiKey = request.form['api_key']
    if not checkApiKey(affiliation, apiKey):
        return msgApiKeyMalformed

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
    filename = FILE_PATH + affiliation + coffeePath
    if writeFile(filename, pots + '\n' + datetime):
        return "CONFIRMED! READBACK:\n" + pots + " pots at " + affiliation + "'s office, last one at " + datetime
    else:
        return "DENIED! An error occured, tell the people at appkom@online.ntnu.no"

app.wsgi_app = ReverseProxied(app.wsgi_app)

# Run the app :)
if datetimeTests():
    if __name__ == "__main__":
        app.run()
else:
    print('ERROR: a test failed, fix it plz')
