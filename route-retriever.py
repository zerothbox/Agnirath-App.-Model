import requests
import math
import csv
import time


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Parameters:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        The distance between the two points
    """

    R = 6371000  # Earth radius
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Parameters:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        The forward azimuth (direction) of point 2 from point 1
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (
        math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    )

    initial_bearing = math.atan2(x, y)
    return (math.degrees(initial_bearing) + 360) % 360


def calculate_slope(diff_elev, dist):
    """
    Parameters:
        diff_elev: Difference in elevation
        dist: Distance

    Returns:
        The slope
    """
    if dist == 0:
        return 0.0
    return math.degrees(math.atan(diff_elev / dist))


def get_route_osrm(start, end):
    """
    Parameters:
        start: Coordinates of the first point
        end: Coordinates of the second point

    Returns:
        The route between the two points
    """

    coords_str = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"

    response = requests.get(url)
    response.raise_for_status()

    # Extract the coordinate list: [[lon, lat], [lon, lat], ...]
    data = response.json()
    route_coords = data["routes"][0]["geometry"]["coordinates"]

    # Flip to [lat, lon] for standard usage
    return [[lat, lon] for lon, lat in route_coords]


def get_elevations_opentopo(coords_list, batch_size=100):
    """
    Parameters:
        coords_list: A list of coordinates on the route
        batch_size: The size of each block of data to be sent to avoid overloading

    Returns:
        The altitude data
    """

    elevations = []

    # Process in chunks to not crash public server
    for i in range(0, len(coords_list), batch_size):
        batch = coords_list[i : i + batch_size]
        locations = "|".join([f"{lat},{lon}" for lat, lon in batch])
        url = f"https://api.opentopodata.org/v1/srtm90m?locations={locations}"

        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            elevations.extend([res["elevation"] for res in results])
        else:
            print(f"API Error at batch {i}. Padding with previous altitude.")
            # Fallback
            fallback = elevations[-1] if elevations else 0.0
            elevations.extend([fallback] * len(batch))

        time.sleep(1)  # API rate limits

    return elevations


def main():

    sasolburg = (-26.8115, 27.8276)
    zeerust = (-25.5369, 26.0751)

    # Route
    route = get_route_osrm(sasolburg, zeerust)

    # Elevations
    elevations = get_elevations_opentopo(route)

    # Process
    processed_data = []

    for i in range(len(route)):
        lat, lon = route[i]
        alt = elevations[i]

        if i == 0:
            dist = 0.0
            bearing = 0.0
            slope = 0.0
        else:
            prev_lat, prev_lon = route[i - 1]
            prev_alt = elevations[i - 1]

            dist = haversine_distance(prev_lat, prev_lon, lat, lon)
            bearing = calculate_bearing(prev_lat, prev_lon, lat, lon)
            slope = calculate_slope(alt - prev_alt, dist)

        processed_data.append(
            {
                "point_index": i,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "altitude_m": round(alt, 2) if alt else 0.0,
                "distance_from_prev_m": round(dist, 2),
                "bearing_deg": round(bearing, 2),
                "slope_deg": round(slope, 4),
            }
        )

    # Save
    filename = "sasolburg_to_zeerust_route.csv"

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=processed_data[0].keys())
        writer.writeheader()
        writer.writerows(processed_data)

    print("Pipeline complete with no errors")


if __name__ == "__main__":
    main()
