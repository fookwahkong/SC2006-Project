# Script used for the creation of graph
from graph import *
from tqdm import tqdm
import algorithms
import itertools

routes = BusRoutes(db_uri)
services = BusServices(db_uri).get_data()
busstops = BusStops(db_uri)
stopdata = busstops.get_data()

G = BusRouteGraph()
for i in services:
    # For each bus service
    route = routes.byServiceNoDir(i["ServiceNo"], i["Direction"])  # Obtains its route
    servicedir = (i["ServiceNo"], i["Direction"])
    for idx, stop in enumerate(route):
        # For each stop in route
        if idx == 0:
            # If it is the first stop
            prevdist = stop["Distance"]
            prevstop = stop["BusStopCode"]
        else:
            currentdist = stop["Distance"]
            currentstop = stop["BusStopCode"]
            # Adds directed edge from previous stop to current stop
            G.add_edge(
                prevstop,
                currentstop,
                weight=(round(currentdist - prevdist, 1)),
                servicedir=servicedir,
            )
            # Sets the previous distance and stop to the current stop
            prevdist = currentdist
            prevstop = currentstop

# Writes graph of only bus routes to json file
G.to_json("graph_nowalking.json")

# List of all BusStopCodes
stoplist = [x["BusStopCode"] for x in stopdata]
# Get combinations of all pairs of Bus Stops
stoplist = [x for x in itertools.combinations(stoplist, 2)]
datadict = {}
for x in stopdata:
    # Stores data for each bus stop in datadict for more efficient retrieval compared to from database
    datadict[x["BusStopCode"]] = x

for pair in tqdm(stoplist):
    # For each combination pair of bus stops
    stop1, stop2 = pair
    stop1lat, stop1long = datadict[stop1]["Latitude"], datadict[stop1]["Longitude"]
    stop2lat, stop2long = datadict[stop2]["Latitude"], datadict[stop2]["Longitude"]
    # Calculates distance between the two stops
    dist = round(
        algorithms.distance(stop1long, stop1lat, stop2long, stop2lat, unit="km"), 2
    )
    if dist < 0.3:
        # Adds edges if distance between stops < 0.3km to the existing graph
        G.add_edge(stop1, stop2, weight=dist, servicedir="foot")
        G.add_edge(stop2, stop1, weight=dist, servicedir="foot")

# Writes graph of bus routes with walking to json file
G.to_json("graph_walking.json")
