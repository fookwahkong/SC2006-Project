import sqlite3
from algorithms import insertionsort, distance

# Table names
stopname = "Bus_Stops"
routename = "Bus_Routes"
servicename = "Bus_Services"

# Database relative path
db_uri = "main.db"

# Dict for SQL commands
SQL = {
    "busstop_select": "SELECT * FROM " + stopname + " WHERE BusStopCode=?",
    "all_data": "SELECT * FROM ",
    "route_select": "SELECT * FROM " + routename + " WHERE id=?",
    "route_selectByServiceNo": "SELECT * FROM " + routename + " WHERE ServiceNo=?",
    "route_selectByServiceNoDir": "SELECT * FROM "
    + routename
    + " WHERE ServiceNo=? AND Direction=?",
    "route_selectByBusStop": "SELECT * FROM " + routename + " WHERE BusStopCode=?",
    "route_selectServiceNoToStop": "SELECT DISTINCT ServiceNo, Direction FROM "
    + routename
    + " WHERE BusStopCode=?",
    "service_selectByServiceNo": "SELECT * FROM " + servicename + " WHERE ServiceNo=?",
}


class DataStore:
    """
    Base class for accessing data from sqlite database.
    Initialized by supplying parameter
    uri: The path of the sqlite3 database
    """

    tbname = ""

    def __init__(self, uri):
        self.uri = uri

    def __repr__(self):
        return f"DataStore('{self.uri}')"

    def get_conn(self):
        """
        Creates and return an sqlite3 connection object
        """
        conn = sqlite3.connect(self.uri)
        conn.row_factory = sqlite3.Row
        return conn

    def get_data(self):
        """
        Returns all data in the table in a list of dicts
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["all_data"] + self.tbname)
        data = cur.fetchall()
        cur.close()
        conn.close()
        # Converts sqlite3.Row objects to python Dict
        data = [dict(x) for x in data]
        return data


class BusStops(DataStore):
    """
    Class inheriting DataStore with methods specifically for Bus Stops
    """

    tbname = stopname

    def __repr__(self):
        return f"BusStops('{self.uri}')"

    def distfrom(self, x1: float, y1: float, n: int = None):
        """
        Calculates the distance of a point x1, y1, where x1 is latitude and y1 is longitude from each bus stop,
        then returns a list of of length n of Bus Stop dicts sorted
        in ascending order by distance from that point. Returns all bus stops if n is not specified.

        Example:
        >>> self.distfrom(1.23, 103.2, 2)
        [{'BusStopCode': '25751', 'RoadName': 'Tuas Sth Ave 5', 'Description': 'BEF TUAS STH AVE 14',
        'Latitude': 1.27637, 'Longitude': 103.621508, 'Distance': 47070},
        {'BusStopCode': '25761', 'RoadName': 'Tuas Sth Ave 14', 'Description': "OPP REC S'PORE",
        'Latitude': 1.275062, 'Longitude': 103.624222, 'Distance': 47354}]
        """
        data = self.get_data()
        if n is None:
            n = len(data)
        for bus_stop in data:
            # Calculates distance of each bus stop from the point
            distinm = distance(x1, y1, bus_stop["Latitude"], bus_stop["Longitude"], "m")
            bus_stop["Distance"] = int(round(distinm, 0))  # Distance to 0 d.p.
        sorteddata = insertionsort(data, "Distance")
        return sorteddata[:n]

    def byBusStop(self, busStopCode: str):
        """
        Retrieves the data of a bus stop by busStopCode. Returns the data of the bus stop in a dict

        Example:
        >>> self.byBusStop("59009")
        {'BusStopCode': '59009', 'RoadName': 'Yishun Ave 2', 'Description': 'Yishun Int', 'Latitude': 1.4284, 'Longitude': 103.8360975}
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["busstop_select"], (busStopCode,))
        data = cur.fetchone()
        cur.close()
        conn.close()
        if data is None:
            return data
        else:
            return dict(data)

    def distbetweenstops(self, stop1: str, stop2: str):
        """
        Calculates the straight line distance between two bus stops in kilometres to 1 decimal place.

        Example:
        >>> self.distbetweenstops("59009", "25751")
        29.2
        """
        stop1data = self.byBusStop(stop1)
        stop2data = self.byBusStop(stop2)
        stop1lat, stop1long = stop1data["Latitude"], stop1data["Longitude"]
        stop2lat, stop2long = stop2data["Latitude"], stop2data["Longitude"]
        dist = distance(stop1long, stop1lat, stop2long, stop2lat, unit="km")
        return round(dist, 1)


class BusRoutes(DataStore):
    """
    Class inheriting DataStore with methods specifically for Bus Routes
    """

    tbname = routename

    def __repr__(self):
        return f"BusRoutes('{self.uri}')"

    def byServiceNo(self, serviceNo: str):
        """
        Retrieves all bus routes served by a bus service by its serviceNo.
        Returns a list of dicts where each dict represents one route.

        Example:
        >>> self.byServiceNo("858")
        [{'id': 24161, 'ServiceNo': '970', 'Direction': 1, 'StopSequence': 1, 'BusStopCode': '45009', 'Distance': 0.0},
        ...
        {'id': 24290, 'ServiceNo': '970', 'Direction': 2, 'StopSequence': 66, 'BusStopCode': '45009', 'Distance': 24.6}]
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["route_selectByServiceNo"], (serviceNo,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data = [dict(x) for x in data]
        return data

    def byServiceNoDir(self, serviceNo: str, direction: int):
        """
        Retrieves all bus routes served by a bus service by its serviceNo and direction.
        Returns a list of dicts where each dict represents one route.

        >>> self.byServiceNoDir("858")
        [{'id': 24161, 'ServiceNo': '970', 'Direction': 1, 'StopSequence': 1, 'BusStopCode': '45009', 'Distance': 0.0},
        ...
        {'id': 24225, 'ServiceNo': '970', 'Direction': 1, 'StopSequence': 67, 'BusStopCode': '03218', 'Distance': 25.6}]
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["route_selectByServiceNoDir"], (serviceNo, direction))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data = [dict(x) for x in data]
        return data

    def byBusStop(self, busStopCode: str):
        """
        Retrieves all bus routes to a bus stop by busStopCode.
        Returns a list of dicts where each dict represents one route.

        Example:
        >>> self.byBusStop("99189")
        [{'id': 8504, 'ServiceNo': '19', 'Direction': 1, 'StopSequence': 39, 'BusStopCode': '99189', 'Distance': 14.5},
        ...
        {'id': 22001, 'ServiceNo': '9', 'Direction': 1, 'StopSequence': 54, 'BusStopCode': '99189', 'Distance': 20.1}]
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["route_selectByBusStop"], (busStopCode,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data = [dict(x) for x in data]
        return data

    def serviceNoToStop(self, busStopCode: str):
        """
        Retrieves all bus service and direction pairs to a bus stop by busStopCode.
        Returns a list of dicts where each dict represents one serviceNo, Direction pair.

        Example:
        >>> self.serviceNoToStop("99189")
        [{'ServiceNo': '19', 'Direction': 1}, {'ServiceNo': '89', 'Direction': 1},
        {'ServiceNo': '89e', 'Direction': 2}, {'ServiceNo': '9', 'Direction': 1}]
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["route_selectServiceNoToStop"], (busStopCode,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data = [dict(x) for x in data]
        return data


class BusServices(DataStore):
    """
    Class inheriting DataStore with methods specifically for Bus Services
    """

    tbname = servicename

    def __repr__(self):
        return f"BusServices('{self.uri}')"

    def byServiceNo(self, serviceNo: str):
        """
        Retrieves the information of all bus services by their serviceNo.
        Return a list of dicts of the bus service data.

        Example:
        >>> self.byServiceNo("970")
        [{'ServiceNo': '970', 'Direction': 1, 'Category': 'TRUNK', 'Operator': 'SMRT'},
        {'ServiceNo': '970', 'Direction': 2, 'Category': 'TRUNK', 'Operator': 'SMRT'}]
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(SQL["service_selectByServiceNo"], (serviceNo,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data = [dict(x) for x in data]
        return data