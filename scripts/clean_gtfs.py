"""Reduce the raw TTC GTFS feed to the small tables needed for the venue-proximity analysis.

Outputs (data/processed/):
  gtfs_routes.csv       one row per route (bus/streetcar/subway), key = route_short_name
  gtfs_stops.csv        one row per physical stop actually served by a bus/streetcar route, with lat/lon
  gtfs_route_stops.csv  route_short_name <-> stop_id (which stops each route serves)
"""
import pandas as pd

RAW = "data/raw/Merged GTFS - TTC Routes and Schedules/"
OUT = "data/processed/"

routes = pd.read_csv(RAW + "routes.txt", dtype=str)
routes = routes[routes.route_type.isin(["3", "0"])]  # bus + streetcar; subway has no road traffic
routes = routes[["route_id", "route_short_name", "route_long_name", "route_type"]]
routes["mode"] = routes.route_type.map({"3": "bus", "0": "streetcar"})
routes = routes.drop(columns="route_type")

trips = pd.read_csv(RAW + "trips.txt", dtype=str, usecols=["trip_id", "route_id"])
trips = trips[trips.route_id.isin(routes.route_id)]

st = pd.read_csv(RAW + "stop_times.txt", dtype=str, usecols=["trip_id", "stop_id"])
st = st[st.trip_id.isin(trips.trip_id)].merge(trips, on="trip_id")
route_stops = (st[["route_id", "stop_id"]].drop_duplicates()
               .merge(routes[["route_id", "route_short_name"]], on="route_id")
               [["route_short_name", "stop_id"]])

stops = pd.read_csv(RAW + "stops.txt", dtype=str,
                    usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
stops = stops[stops.stop_id.isin(route_stops.stop_id)].dropna(subset=["stop_lat", "stop_lon"])
stops[["stop_lat", "stop_lon"]] = stops[["stop_lat", "stop_lon"]].astype(float)
route_stops = route_stops[route_stops.stop_id.isin(stops.stop_id)]
routes = routes[routes.route_short_name.isin(route_stops.route_short_name)]

routes.drop(columns="route_id").to_csv(OUT + "gtfs_routes.csv", index=False)
stops.to_csv(OUT + "gtfs_stops.csv", index=False)
route_stops.to_csv(OUT + "gtfs_route_stops.csv", index=False)
print(len(routes), "routes;", len(stops), "stops;", len(route_stops), "route-stop pairs")
