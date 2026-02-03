# ===============================================================
# charging_integration.py
# Charging station model + EAFO integration for Germany
# Used for Hamburg → Munich EV Truck Routing
# ===============================================================

import pandas as pd
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
import osmnx as ox


class ChargingStationManager:
    """
    Manages heavy-duty fast-charging stations for electric trucks.
    Data source: EAFO (European Alternative Fuels Observatory)
    """

    def __init__(self, graph):
        """
        Parameters:
        - graph: OSMnx road network graph for Germany
        """
        self.graph = graph
        self.stations = None     # will become a GeoDataFrame

        # MAN/Mercedes compatible fast-charging levels
        self.valid_power_levels_kw = [150, 300, 350, 750]  # HPC + MCS

        # Battery parameters
        self.battery_capacity_kwh = 600                      # truck battery
        self.max_charge_power_kw = 750                       # MCS peak
        self.cc_cutoff_soc = 0.80                            # CC phase limit
        self.cc_efficiency = 0.93
        self.cv_efficiency = 0.88

    # ===============================================================
    # LOAD EAFO DATASET
    # ===============================================================

    def load_eafo_dataset(self, csv_path):
        """
        Load EAFO alternative fuels infrastructure dataset.

        Expected columns:
        - Country
        - Power_kW
        - Latitude
        - Longitude
        - StationName / Operator (optional)
        """

        df = pd.read_csv(csv_path)

        # Filter Germany only
        df = df[df["Country"].str.contains("Germany", case=False, na=False)]

        # Filter heavy-duty suitable power levels
        df = df[df["Power_kW"] >= 150]

        df = df[df["Power_kW"].isin(self.valid_power_levels_kw)]

        # Drop missing coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
            crs="EPSG:4326"
        )

        self.stations = gdf
        return self.stations

    # ===============================================================
    # SNAP STATIONS TO OSMNX NODES
    # ===============================================================

    def snap_stations_to_graph(self):
        """
        Finds nearest graph node for each charging station.
        Adds a 'node_id' column.
        """
        if self.stations is None:
            raise ValueError("Stations not loaded. Run load_eafo_dataset() first.")

        station_nodes = []
        for _, row in self.stations.iterrows():
            node_id = ox.nearest_nodes(
                self.graph, row.geometry.x, row.geometry.y
            )
            station_nodes.append(node_id)

        self.stations["node_id"] = station_nodes
        return self.stations

    # ===============================================================
    # CHARGING TIME MODEL (CC–CV CURVE)
    # ===============================================================

    def charging_time_minutes(self, soc_initial, soc_target, charger_power_kw):
        """
        Compute charging time using a simplified CC–CV charging model.

        Parameters:
            soc_initial : starting SOC [0–1]
            soc_target  : ending SOC [0–1]
            charger_power_kw : charger rating (kW)

        Returns:
            charging time in minutes
        """

        if soc_target <= soc_initial:
            return 0.0

        soc1 = soc_initial
        soc2 = soc_target

        # ----- PHASE 1: Constant Current (fast charging) -----
        cc_limit = self.cc_cutoff_soc

        if soc1 < cc_limit:
            soc_cc_end = min(soc2, cc_limit)

            energy_added_kwh = (soc_cc_end - soc1) * self.battery_capacity_kwh

            time_hours_cc = energy_added_kwh / (charger_power_kw * self.cc_efficiency)
        else:
            time_hours_cc = 0

        # ----- PHASE 2: Constant Voltage (tapering) -----
        if soc2 > cc_limit:
            soc2_cv = soc2
            soc1_cv = max(soc1, cc_limit)

            # CV phase much slower (current tapers linearly)
            energy_added_kwh_cv = (soc2_cv - soc1_cv) * self.battery_capacity_kwh

            # Approximate average power = 40% of charger rating
            average_cv_power = charger_power_kw * 0.40

            time_hours_cv = energy_added_kwh_cv / (average_cv_power * self.cv_efficiency)
        else:
            time_hours_cv = 0

        total_hours = time_hours_cc + time_hours_cv
        total_minutes = total_hours * 60

        return total_minutes

    # ===============================================================
    # VALID STATIONS QUERY
    # ===============================================================

    def get_candidate_stations_near_route(self, path_nodes, buffer_km=5):
        """
        Return charging stations close to the computed route.
        """

        if self.stations is None:
            raise ValueError("Stations not loaded.")

        # Route → GeoSeries of points
        route_lats = []
        route_lons = []
        for node in path_nodes:
            lat = self.graph.nodes[node]["y"]
            lon = self.graph.nodes[node]["x"]
            route_lats.append(lat)
            route_lons.append(lon)

        route_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(route_lons, route_lats),
            crs="EPSG:4326"
        )

        # Route buffer
        route_buffer = route_gdf.unary_union.buffer(buffer_km / 111)  # deg ~ km

        # Spatial filter
        nearby = self.stations[self.stations.geometry.within(route_buffer)]

        return nearby

    # ===============================================================
    # CHARGING EVENT SIMULATION
    # ===============================================================

    def simulate_charging_event(self, soc_initial, target_soc, station_power_kw):
        """
        Simulate charging session and return:
        - final SOC
        - time spent charging
        - energy delivered
        """

        time_min = self.charging_time_minutes(soc_initial, target_soc, station_power_kw)

        energy_kwh = (target_soc - soc_initial) * self.battery_capacity_kwh

        return {
            "soc_final": target_soc,
            "charging_minutes": time_min,
            "energy_added_kwh": energy_kwh
        }
