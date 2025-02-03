from flask import Flask, render_template, request, redirect, url_for
import datastore
from graph import BusRouteGraph
import os
from algorithms import binarysearchroute

# Initialize graph objects
busroutegraph = BusRouteGraph.from_json("graph_nowalking.json")
busroutegraphwalking = BusRouteGraph.from_json("graph_walking.json")

# Initialize database objects
busstops = datastore.BusStops("main.db")
busroutes = datastore.BusRoutes("main.db")
busservices = datastore.BusServices("main.db")

# Set Google API key
google_api_key = os.environ.get(
    "MAPS_API_KEY", "AIzaSyAkH00iMTCBzkyiyjktbOWPoMbMe6F78f0"
)

app = Flask(__name__)


@app.route("/")
def root():
    return render_template("index.html")


@app.route("/nearest_stop")
def nearest_stop():
    return render_template("nearest_stop.html", google_api_key=google_api_key)


@app.route("/nearest_stop/result")
def nearest_stop_result():
    # Retrieve and separate form inputs to latitude and longitude values
    location = request.args.get("loc").replace(" ", "").strip("()")
    lat, long = location.split(",")

    # Finds the closest bus stop to the specified location
    bus_stop = busstops.distfrom(float(lat), float(long), 1)[0]
    routes = busroutes.byBusStop(bus_stop["BusStopCode"])

    return render_template(
        "nearest_stop-result.html",
        bus_stop=bus_stop,
        lat=lat,
        long=long,
        routes=routes,
        google_api_key=google_api_key,
    )


@app.route("/pathfinder")
def pathfinder():
    # Retrieves data for <select> inputs
    busstopdata = busstops.get_data()
    return render_template("pathfinder.html", stopdata=busstopdata)


@app.route("/pathfinder/result", methods=["GET", "POST"])
def pathfinder_result():
    # Retrieves form inputs and sets graphused
    source = request.form.get("source")
    target = request.form.get("target")
    transfercost = int(request.form.get("t", "3"))
    walking = int(request.form.get("walking", "0"))
    if walking:
        graphused = busroutegraphwalking
    else:
        graphused = busroutegraph

    # Finds all shortest routes
    routes = graphused.find_shortest_route(source, target, transfercost)

    # Finds the proper rowspan value for each data (stop in route) in table and adds bus stop data
    for route in routes:
        # Rowspan list for each route
        spanlist = []
        for idx in range(len(route["path"])):
            if idx == 0:
                spanlist.append(1)
                firsttravel = True
            elif firsttravel and route["path"][idx][1] == "travelling":
                # elif the first stop travelled to after taking a new bus
                firsttravel = False
                travelcount = 1
                # sets index of first stop travelled after taking a new bus
                spanidx = idx
            elif not firsttravel and route["path"][idx][1] == "travelling":
                # elif subsequent travelling stops
                travelcount += 1
                spanlist.append(0)
            elif not firsttravel:
                # elif stops travelling on the same bus
                # insert the number of stops travelled at the index of first stop travelled
                spanlist.insert(spanidx, travelcount)
                travelcount = 0
                spanlist.append(1)
                firsttravel = True
            else:
                # Rowspan is 1 for other cases
                spanlist.append(1)

            # Obtain the bus stop data for each stop on the route and adds it to the route dict
            stop = route["path"][idx][0]
            data = busstops.byBusStop(stop)
            route["path"][idx] = (data, route["path"][idx][1])

            # Adds the spanlist to the route dict
            route["span"] = spanlist
    return render_template("pathfinder-result.html", routes=routes)


@app.route("/stop_info")
def stop_info():
    # Retrieves data for <select> inputs
    busstopdata = busstops.get_data()
    return render_template("stop_info.html", stopdata=busstopdata)


@app.route("/stop_info/result")
def stop_info_result():
    # Retrieves the user input stopcode and obtains details of the bus stop
    stopcode = request.args.get("stopcode")
    bus_stop = busstops.byBusStop(stopcode)

    # Retrieves the routes that pass through the bus stop
    routes = busroutes.byBusStop(bus_stop["BusStopCode"])
    return render_template(
        "stop_info-result.html",
        bus_stop=bus_stop,
        routes=routes,
        google_api_key=google_api_key,
    )


@app.route("/service_info")
def service_info():
    # Retrieves data for <select> inputs
    busservicedata = busservices.get_data()
    return render_template("service_info.html", servicedata=busservicedata)


@app.route("/service_info/result")
def service_info_result():
    # Retrieves service number input and obetains data of that service
    serviceno = request.args.get("serviceno")
    services = busservices.byServiceNo(serviceno)

    # Get the number of directions the service has
    directions = services[-1]["Direction"]

    # Cleans up key names and unnecessary service info
    service = services[0]
    service["Service Number"] = service["ServiceNo"]
    del service["ServiceNo"]
    del service["Direction"]

    # Finds the routes served by the service
    routes = busroutes.byServiceNo(serviceno)
    if directions == 2:
        # Finds the index where the route in the seconds direction starts
        index = binarysearchroute(routes, {"Direction": 2, "StopSequence": 1})
        # List of 2 routes for the 2 directions
        routes = [routes[:index], routes[index:]]
    else:
        routes = [routes]

    # Obtains bus stop information for each stop in route
    for route in routes:
        for idx in range(len(route)):
            stop = route[idx]["BusStopCode"]
            data = busstops.byBusStop(stop)
            route[idx] = {"stopdata": data, "Distance": route[idx]["Distance"]}
    return render_template(
        "service_info-result.html",
        service=service,
        routes=routes,
        directions=directions,
    )


@app.route("/usage_guide")
def usage_guide():
    return render_template("usage_guide.html")


if __name__ == "__main__":
    app.run()