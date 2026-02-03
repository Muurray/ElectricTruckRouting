# ===============================================================
# graph_processor.py
# Build & preprocess Germany road network for routing
# ===============================================================

import osmnx as ox
import networkx as nx
import numpy as np


class GraphProcessor:

    def __init__(self):
        self.graph = None

    # -----------------------------------------------------------
    # BUILD GERMANY GRAPH
    # -----------------------------------------------------------

    def load_germany_graph(self):
        """
        Loads the road network of Germany using OSMnx.
        Filters to major roads to ensure tractability.
        """

        print("Downloading Germany road graph...")

        G = ox.graph_from_place(
            "Germany",
            network_type="drive",
            simplify=True,
            retain_all=False
        )

        print("Graph downloaded. Simplifying...")

        G = ox.simplify_graph(G)

        # Keep only important highways for long-haul trucks
        highway_whitelist = [
            "motorway", "motorway_link",
            "trunk", "trunk_link",
            "primary", "primary_link"
        ]

        G2 = ox.utils_graph.graph_from_gdfs(
            *ox.graph_to_gdfs(G)
        )

        edges_to_keep = []
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = data.get("highway", "")
            if isinstance(hw, list):
                hw = hw[0]

            if hw in highway_whitelist:
                edges_to_keep.append((u, v, k))

        G = G.edge_subgraph(edges_to_keep).copy()

        print("Filtered graph size:", len(G.nodes), "nodes,", len(G.edges), "edges")

        self.graph = G
        return G

    # -----------------------------------------------------------
    # EDGE SPEEDS & GRADIENTS
    # -----------------------------------------------------------

    def add_speed_and_gradient(self):
        """
        Adds estimated speeds and gradient from elevation data.
        """

        print("Adding speed & elevation...")

        # Speed assignment based on highway type
        speed_map = {
            "motorway": 90,
            "motorway_link": 60,
            "trunk": 80,
            "trunk_link": 50,
            "primary": 70,
            "primary_link": 50,
        }

        for u, v, data in self.graph.edges(data=True):
            hw = data.get("highway", "primary")
            if isinstance(hw, list):
                hw = hw[0]
            data["speed_kph"] = speed_map.get(hw, 60)

        # Elevation using OSMnx + SRTM
        self.graph = ox.add_node_elevations_raster(
            self.graph, "https://github.com/GeoTIFF/SRTM/raw/master/srtm_38_03.tif"
        )
        self.graph = ox.add_edge_grades(self.graph)

        return self.graph

    # -----------------------------------------------------------
    # WEIGHT = DISTANCE / SPEED (TRAVEL TIME)
    # -----------------------------------------------------------

    def add_travel_time_weights(self):
        for u, v, data in self.graph.edges(data=True):
            dist_km = data.get("length", 1.0) / 1000
            speed_h = data["speed_kph"]
            time_h = dist_km / speed_h
            data["travel_time_h"] = time_h
        return self.graph

    # -----------------------------------------------------------
    # ORIGIN–DESTINATION NODE FINDER
    # -----------------------------------------------------------

    def get_route_endpoints(self, origin_lat, origin_lon, dest_lat, dest_lon):
        """
        Convert coordinates to graph nodes.
        """
        orig = ox.nearest_nodes(self.graph, origin_lon, origin_lat)
        dest = ox.nearest_nodes(self.graph, dest_lon, dest_lat)
        return orig, dest
