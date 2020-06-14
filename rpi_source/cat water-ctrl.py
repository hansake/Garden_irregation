#!/usr/bin/python

"""
	Irregation water control
	Logs water consumption to an SQLite database, based on the number
	of pulses from a flow meter.

	Handling three flow meter pulse inputs
	and publish values via MQTT to Domoticz

"""

import RPi.GPIO as GPIO, sqlite3 as sqlite, time, os
import paho.mqtt.client as mqtt

# Debug flag for printing, 0: false, 1: true
Debug = 1

# Configuration for MQTT broker and Domoticz
broker_address="localhost"
# The device indexes are assigned by Domoticz and must be changed here
idx1 = 4
idx2 = 5
idx3 = 6

# The flow meter pulse counters
# there will be 450 pulses for each liter of water
pulsecounter1 = 0
pulsecounter2 = 0
pulsecounter3 = 0


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite.connect(db_file)
        return conn
    except sqlite.Error as e:
        print(e)
 
    return None

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite.Error as e:
        print(e)

def InsertCounters(db_file, timestamp, cntr1, cntr2, cntr3):
	try:
		dbconn=sqlite.connect(db_file)
		dbdata=dbconn.cursor()
		dbdata.execute("INSERT INTO Wcounters VALUES(?, ?, ?, ?)", (timestamp, cntr1, cntr2, cntr3))
		dbconn.commit()
	except sqlite.Error,e:
		print e
		if dbconn:
			dbconn.rollback()
	finally:
		if dbconn:
			dbconn.close()

def UpdateCurrCounters(db_file, timestamp, cntr1, cntr2, cntr3):
	try:
		dbconn=sqlite.connect(db_file)
		dbdata=dbconn.cursor()
                dbdata.execute("UPDATE Lwcounters SET timestamp=?, lwcounter1=?, lwcounter2=?, lwcounter3=? WHERE id=1", (timestamp, cntr1, cntr2, cntr3))
		dbconn.commit()
	except sqlite.Error,e:
		print e
		if dbconn:
			dbconn.rollback()
	finally:
		if dbconn:
			dbconn.close()

def InitCurrCounters(db_file, timestamp):
	try:
		dbconn=sqlite.connect(db_file)
		dbdata=dbconn.cursor()
                dbdata.execute("INSERT INTO Lwcounters VALUES(?, ?, ?, ?, ?)", (1, timestamp, 0, 0, 0))
		dbconn.commit()
	except sqlite.Error,e:
#                print e
#                print("Opening existing database: {0}".format(db_file))
		if dbconn:
			dbconn.rollback()
	finally:
		if dbconn:
			dbconn.close()

def GetCurrCounters(db_file):
        global pulsecounter1
        global pulsecounter2
        global pulsecounter3
	try:
		dbconn=sqlite.connect(db_file)
		dbdata=dbconn.cursor()
                dbdata.execute("SELECT * FROM Lwcounters")
	except sqlite.Error,e:
		print e
        row = dbdata.fetchone()
        pulsecounter1 = row[2]
        pulsecounter2 = row[3]
        pulsecounter3 = row[4]
	if dbconn:
		dbconn.close()

def pulse1_callback(pin):
        global pulsecounter1
#        print("pulse on pin: {0}".format(pin))
        pulsecounter1+=1

def pulse2_callback(pin):
        global pulsecounter2
#        print("pulse on pin: {0}".format(pin))
        pulsecounter2+=1

def pulse3_callback(pin):
        global pulsecounter3
#        print("pulse on pin: {0}".format(pin))
        pulsecounter3+=1

def main():
    GPIO.setmode(GPIO.BCM)

    pulsepin1 = 13
    GPIO.setup(pulsepin1, GPIO.IN)

    pulsepin2 = 19
    GPIO.setup(pulsepin2, GPIO.IN)

    pulsepin3 = 26
    GPIO.setup(pulsepin3, GPIO.IN)

    GPIO.add_event_detect(pulsepin1, GPIO.RISING, callback=pulse1_callback)
    GPIO.add_event_detect(pulsepin2, GPIO.RISING, callback=pulse2_callback)
    GPIO.add_event_detect(pulsepin3, GPIO.RISING, callback=pulse3_callback)

    database = "/var/db/watermon.db"

    sql_create_wcounters_table = """CREATE TABLE IF NOT EXISTS Wcounters (
                                    timestamp INTEGER PRIMARY KEY,
                                    wcounter1 INTEGER,
                                    wcounter2 INTEGER,
                                    wcounter3 INTEGER
                                );"""
 
    sql_create_lwcounters_table = """CREATE TABLE IF NOT EXISTS Lwcounters (
                                    id INTEGER PRIMARY KEY,
                                    timestamp INTEGER,
                                    lwcounter1 INTEGER,
                                    lwcounter2 INTEGER,
                                    lwcounter3 INTEGER
                                );"""
 
    # create a database connection
    conn = create_connection(database)
    if conn is not None:
        # create water counters table
        create_table(conn, sql_create_wcounters_table)
        # create latest water counters table
        create_table(conn, sql_create_lwcounters_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

    timenow = int(time.time())
    InitCurrCounters(database, timenow)

    GetCurrCounters(database)

    # Connect to the MQTT broker
    client = mqtt.Client("Wcnt1") # create new instance
    client.connect(broker_address) # connect to broker

    while True:
        # Update SQLite database with counter values
        print("Water: 1: {0} pulses, 2: {1} pulses, 3: {2} pulses".format(pulsecounter1, pulsecounter2, pulsecounter3))
        timenow = int(time.time())
        InsertCounters(database, timenow, pulsecounter1, pulsecounter2, pulsecounter3)
        timenow = int(time.time())
        UpdateCurrCounters(database, timenow, pulsecounter1, pulsecounter2, pulsecounter3)

        # Publish the liter values to Domoticz
        wliter1 = int(pulsecounter1/450)
        wliter2 = int(pulsecounter2/450)
        wliter3 = int(pulsecounter3/450)
        print("Water: 1: {0} L, 2: {1} L, 3: {2} L".format(wliter1, wliter2, wliter3))
        # Format and publish first water meter
        mqttbuffer = "{ \"idx\" : %d, \"nvalue\" : 0, \"svalue\" : \"%d\" }" % (idx1, wliter1)
        if Debug == 1:
            print(mqttbuffer)
        client.publish("domoticz/in", mqttbuffer)
        time.sleep(1) # wait a while between messages

        # Format and publish second counter
        mqttbuffer = "{ \"idx\" : %d, \"nvalue\" : 0, \"svalue\" : \"%d\" }" % (idx2, wliter2)
        if Debug == 1:
            print(mqttbuffer)
        client.publish("domoticz/in", mqttbuffer)
        time.sleep(1) # wait a while between messages

        # Format and publish third counter
        mqttbuffer = "{ \"idx\" : %d, \"nvalue\" : 0, \"svalue\" : \"%d\" }" % (idx3, wliter3)
        if Debug == 1:
            print(mqttbuffer)
        client.publish("domoticz/in", mqttbuffer)

        # Wait a while before next update
        time.sleep(20)

if __name__ == '__main__':
    main()
