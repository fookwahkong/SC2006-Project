from math import sqrt


def distance(x1: float, y1: float, x2: float, y2: float, unit="deg"):
    """
    Calculates the distance between two points on Earth,
    where y1, x1, y2, x2 is the longitude and latitude of the first point and second point respectively.
    unit must be "deg": degrees, "km": kilometres or "m": metres.
    """
    # Uses Pythagoras Theorem to calculate distance
    distindeg = sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
    if unit == "deg":
        return distindeg
    elif unit == "km":
        return distindeg * 111  # approximate estimation for degrees to km
    elif unit == "m":
        return distindeg * 111000  # approximate estimation for degrees to m
    else:
        raise ValueError(f"Invalid unit: {unit}, unit must be 'deg', 'km' or 'm'.")


def insertionsort(lst, criteria, order="asc"):
    """
    Takes lst, a list of dicts, and sorts it by the criteria
    specified which is present in each dict, using insertionsort algorithm.
    """
    for i in range(1, len(lst)):
        # For each unsorted index
        for j in range(i):
            # For each sorted index
            if lst[i][criteria] < lst[j][criteria]:
                # If unsorted element's criteria < sorted element's criteria
                lst.insert(j, lst.pop(i))
                break
    # Returns lst in order
    if order == "asc":
        return lst
    else:
        return lst[::-1]


def binarysearchroute(lst, target):
    """
    Searches lst, a list of dicts of each route, for target,
    where target is a dict containing values of direction and stopsequence.
    Returns the index of the target if the target is found,
    else returns None.
    """
    start = 0
    end = len(lst) - 1
    mid = (start + end) // 2
    while (start != end) and not (
        target["Direction"] == lst[mid]["Direction"]
        and target["StopSequence"] == lst[mid]["StopSequence"]
    ):
        # While start != end and target element not a proper subset of middle elemtent
        if target["Direction"] < lst[mid]["Direction"]:
            # Search for direction
            end = mid
        elif (target["Direction"] == lst[mid]["Direction"]) and (
            target["StopSequence"] < lst[mid]["StopSequence"]
        ):
            # Search for stopsequence once direction is found
            end = mid
        else:
            start = mid + 1
        mid = (start + end) // 2
    return mid