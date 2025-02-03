from datastore import BusServices, BusRoutes, BusStops, db_uri
import networkx as nx
import itertools
import json
from heapq import heappush, heappop
from algorithms import insertionsort
from tqdm import tqdm
from multiprocessing.pool import Pool


class PriorityQueue:
    """
    Implementation of a priority queue.

    Based on https://docs.python.org/3/library/heapq.html.
    """

    def __init__(self):
        self.pq = []  # list of entries arranged in a heap
        self.entry_finder = {}  # mapping of routes to entries
        self.removed = "<removed-route>"  # placeholder for a removed route
        self.counter = itertools.count()  # unique sequence count

    def add_route(self, route, priority: int = 0):
        """
        Add a new route or update the priority of an existing route.
        """
        if route in self.entry_finder:
            self.remove_route(route)
        count = next(self.counter)
        entry = [priority, count, route]
        self.entry_finder[route] = entry
        heappush(self.pq, entry)

    def remove_route(self, route):
        """
        Mark an existing route as REMOVED. Raise KeyError if not found.
        """
        entry = self.entry_finder.pop(route)
        entry[-1] = self.removed

    def pop_route(self):
        """
        Remove and return the lowest priority route. Raise KeyError if empty.
        """
        while self.pq:
            _, _, route = heappop(self.pq)
            if route is not self.removed:
                del self.entry_finder[route]
                return route
        raise KeyError("Pop from an empty priority queue")

    def is_empty(self):
        """
        Returns True if priority queue is empty, else returns false.
        """
        return not bool(self.entry_finder)


class BusRouteGraph(nx.MultiDiGraph):
    """
    Custom graph object inheriting NetworkX MultiDiGraph.
    """

    routedata = BusRoutes(db_uri)

    def extended_dijkstra_path(self, source: tuple, target: tuple, transfercost: int):
        """
        Implementation of Dijkstra's algorithm for graph with transfercost for transferring bus services.
        Returns a dict of {"path": list of shortest path taken, "distance": distance of path taken}
        source and target are tuples in the format (BusStopCode, (ServiceNo, Direction)).

        Based on:
        http://www.rhydlewis.eu/papers/spalg.pdf

        Example:
        >>> self.extended_dijkstra_path(("66399", ("58", 2)), ("53231", ("58", 2)), 3)
        {'path': [('66399', ('58', 2)), ('66099', ('58', 2)), ('54109', ('58', 2)),
        ('54531', ('58', 2)), ('53241', ('58', 2)), ('53231', ('58', 2))], 'distance': 3.1}
        """

        # Stores the length to each vertex
        lengths = {}

        # Tracks if vertices have been visited
        distinguished = {}

        # Stores the predecessor of each vertex
        prev = {}

        # Priority queue to track nearest vertices
        priorityqueue = PriorityQueue()

        # Sets each vertex, servicedir combination's distance to infinite,
        # not visited, and no predecessors
        for vertex in self:
            for predecessor in self.predecessors(vertex):
                services = self[predecessor]
                for value in services.values():
                    for directn in value.values():
                        servicedir = directn["servicedir"]
                        lengths[(vertex, servicedir)] = float("inf")
                        distinguished[(vertex, servicedir)] = False
                        prev[(vertex, servicedir)] = None

        # If there is no possible path to the target
        if lengths.get(target) is None:
            return {"path": [], "distance": float("inf")}
        lengths[source] = 0
        priorityqueue.add_route(source, lengths[source])
        while not priorityqueue.is_empty():
            # Pops the nearest vertex
            vtxservice = priorityqueue.pop_route()
            if vtxservice == target:
                # Stops after shortest path to the target is found
                break
            distinguished[vtxservice] = True
            for vtx in self[vtxservice[0]]:
                # For each adjacent vertex of the nearest vertex
                for edge in self[vtxservice[0]][vtx]:
                    # For each edge to the adjacent vertex
                    serviceused = self[vtxservice[0]][vtx][edge]["servicedir"]
                    weight = self[vtxservice[0]][vtx][edge]["weight"]
                    if not distinguished[(vtx, serviceused)]:
                        # If the adjacent vertex is not visited with the particular servicedir
                        if serviceused == "foot":
                            # Weight is doubled if travelling on foot
                            weight *= 2
                        elif serviceused != vtxservice[1]:
                            # Weight transfercost is added for a transfer
                            trfcost = transfercost
                        else:
                            trfcost = 0
                        if (
                            lengths[vtxservice] + trfcost + weight
                            < lengths[(vtx, serviceused)]
                        ):
                            # If the length to the adjacent vertex is shorter
                            # than the previously stored length
                            # Stores the new length
                            lengths[(vtx, serviceused)] = round(
                                lengths[vtxservice] + trfcost + weight, 1
                            )
                            # Updates the priorityqueue with the new length
                            priorityqueue.add_route(
                                (vtx, serviceused), lengths[(vtx, serviceused)]
                            )
                            # Stores the predecessor of the adjacent vertex
                            prev[(vtx, serviceused)] = vtxservice
        pathdist = lengths[target]

        # Retrieves the path to the target by its predecessors
        pathlist = []
        if prev[target] is not None:
            while target is not None:
                pathlist.insert(0, target)
                # Sets the next target to the predecessor
                target = prev.get(target)

        return {"path": pathlist, "distance": pathdist}

    def find_shortest_route(self, sourceStop: str, targetStop: str, transfercost: int):
        """
        Finds the shortest paths from sourceStop to targetStop.
        Returns a list of dicts of {"path": list of shortest path taken, "distance": distance of path taken}.

        Example:
        >>> self.find_shortest_route("59009", "59149", 3)
        [{'path': [('59009', '811'), ('59169', 'travelling'),57119',
        ...
        ('59149', 'end')], 'distance': 5.0},
        {'path': [('59009', '811A'), ('59169', 'travelling'),
        ...
        ('59149', 'end')], 'distance': 5.0}]
        """

        targetStopServices = [
            (targetStop, tuple(x.values()))
            for x in self.routedata.serviceNoToStop(targetStop)
        ]  # list of services serving targetStop
        possiblepaths = []
        for stops in self[
            sourceStop
        ]:  # finds routes of all buses originating from source and all buses going to target
            for edges in self[sourceStop][stops]:
                servicedir = self[sourceStop][stops][edges]["servicedir"]
                source = (sourceStop, servicedir)
                possiblepaths.extend(
                    [(source, x, transfercost) for x in targetStopServices]
                )
        pool = Pool()
        routes = pool.starmap(
            self.extended_dijkstra_path, tqdm(possiblepaths)
        )  # finds the shortest routes in possiblepaths using multiprocessing

        # Sorts routes by ascending distance and find the shortest distance
        sortedroutes = insertionsort(routes, "distance")
        lowestdist = sortedroutes[0]["distance"]

        # Finds all other routes with the lowest distance and appends it to bestpaths
        bestpaths = []
        for path in sortedroutes:
            if path["distance"] == lowestdist:
                pathdata = path["path"]
                transfers = 0
                for idx, subpath in enumerate(pathdata):
                    # Sets the correct starting mode of transport from each stop since the
                    # mode of transport for each stop shows the mode from the previous stop
                    if idx == 0:
                        if pathdata[idx + 1][1] == "foot":
                            pathdata[idx] = (subpath[0], "foot")
                        else:
                            pathdata[idx] = (subpath[0], subpath[1][0])
                    elif idx == len(pathdata) - 1:
                        pathdata[idx] = (subpath[0], "end")
                    elif subpath[1] != pathdata[idx + 1][1]:
                        if pathdata[idx + 1][1] == "foot":
                            pathdata[idx] = (subpath[0], "foot")
                        else:
                            transfers += 1
                            pathdata[idx] = (subpath[0], pathdata[idx + 1][1][0])
                    else:
                        pathdata[idx] = (subpath[0], "travelling")

                path["distance"] = round(
                    path["distance"] - transfers * transfercost, 1
                )  # finds the actual distance without transfercosts
                bestpaths.append(path)
        return bestpaths

    def to_json(self, path: str):
        """
        Saves graph as json file at the specified path.
        """
        data = nx.node_link_data(self)
        with open(path, "w") as f:
            json.dump(data, f)

    @classmethod
    def from_json(cls, path: str):
        """
        Returns an instance of the class from a json file at the specified path.
        """
        with open(path, "r") as f:
            data = json.load(f)
            for path in data["links"]:
                # Converts servicedir from list to tuple
                servicedir = path["servicedir"]
                if type(servicedir) == list:
                    path["servicedir"] = tuple(servicedir)
            busroutegraph = cls(nx.node_link_graph(data))
        return busroutegraph