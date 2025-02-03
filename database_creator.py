# Script used for the creation of database
import sqlite3
import json

conn = sqlite3.connect("main.db")
conn.executescript(
    """ 
CREATE TABLE IF NOT EXISTS `Bus_Stops` (
	`BusStopCode`	TEXT,
	`RoadName`	TEXT,
	`Description`	TEXT,
	`Latitude` REAL,
	`Longitude` REAL,
	PRIMARY KEY(`BusStopCode`)
);
CREATE TABLE IF NOT EXISTS `Bus_Services` (
	`ServiceNo`	TEXT,
	`Direction`	INTEGER,
	`Category`	TEXT,
	`Operator` TEXT,
	PRIMARY KEY(`ServiceNo`,`Direction`)
);
CREATE TABLE IF NOT EXISTS `Bus_Routes` (
	`id`	INTEGER,
	`ServiceNo`	TEXT,
	`Direction`	INTEGER,
	`StopSequence`	INTEGER,
	`BusStopCode`	TEXT,
	`Distance` REAL,
	PRIMARY KEY(`id`),
	FOREIGN KEY(`ServiceNo`) REFERENCES `Bus_Services`(`ServiceNo`),
	FOREIGN KEY(`Direction`) REFERENCES `Bus_Services`(`Direction`),
	FOREIGN KEY(`BusStopCode`) REFERENCES `Bus_Stops`(`BusStopCode`)
);"""
)

# Load each json file
with open("bus_stops.json", "r") as f:
    bus_stops = json.load(f)

with open("bus_services.json", "r") as f:
    bus_services = json.load(f)

with open("bus_routes.json", "r") as f:
    bus_routes = json.load(f)

for i in bus_stops:
    # Inserts values into Bus_Stops table
    conn.execute(
        """INSERT INTO Bus_Stops VALUES(?,?,?,?,?)""",
        (
            i["BusStopCode"],
            i["RoadName"],
            i["Description"],
            i["Latitude"],
            i["Longitude"],
        ),
    )

for i in bus_services:
    # Inserts values into Bus_Services table
    conn.execute(
        """INSERT INTO Bus_Services VALUES(?,?,?,?)""",
        (i["ServiceNo"], i["Direction"], i["Category"], i["Operator"]),
    )


for i in bus_routes:
    # Inserts values into Bus_Routes table
    conn.execute(
        """INSERT INTO Bus_Routes ('ServiceNo', 'Direction', 'StopSequence', 'BusStopCode', 'Distance') VALUES(?,?,?,?,?)""",
        (
            i["ServiceNo"],
            i["Direction"],
            i["StopSequence"],
            i["BusStopCode"],
            i["Distance"],
        ),
    )

conn.commit()
conn.close()