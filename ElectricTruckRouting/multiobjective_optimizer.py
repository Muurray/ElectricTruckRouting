# ===============================================================
# multiobjective_optimizer.py
# Multi-objective optimization combining:
# - Travel time
# - Energy use
# - CO2 emissions (indirect from grid mix)
# ===============================================================

import numpy as np
import networkx as nx

class MultiObjectiveOptimizer:

    def __init__(self, graph, truck, energy_eval):
        self.graph = graph
        self.truck = truck
        self.energy_eval = energy_eval

        # German grid emission intensity (approx 2023)
        self.co2_intensity = 420  # gCO2/kWh

    # -----------------------------------------------------------
    # WEIGHTED OBJECTIVE FUNCTION
    # -----------------------------------------------------------

    def compute_weighted_cost(self, path_nodes, w_time, w_energy, w_emissions):
        """
        Returns weighted sum of:
        - travel time
        - energy
        - CO2
        """

        # Travel time
        total_time = 0.0
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            edge = self.graph.get_edge_data(u, v)[0]
            total_time += edge["travel_time_h"]

        # Energy use
        _, energy_kwh = self.energy_eval.compute_route_energy(path_nodes)

        # Emissions
        emissions = energy_kwh * self.co2_intensity / 1000  # kg CO2

        # Weighted sum
        cost = (
            w_time * total_time +
            w_energy * energy_kwh +
            w_emissions * emissions
        )

        return cost

    # -----------------------------------------------------------
    # FIND BEST ROUTE WITH WEIGHTS
    # -----------------------------------------------------------

    def optimize_route(self, origin_node, dest_node, w_time, w_energy, w_emissions):
        """
        Use Dijkstra with edge weights computed from energy, time, etc.
        """

        def edge_weight(u, v, data):
            dist_km = data["length"] / 1000
            speed_h = data["speed_kph"]
            time_h = dist_km / speed_h

            # Energy approx (simplified)
            energy_kwh = dist_km * 1.4  # fallback 1.4 kWh/km

            emission_kg = energy_kwh * self.co2_intensity / 1000

            # Weighted cost
            return (
                w_time * time_h +
                w_energy * energy_kwh +
                w_emissions * emission_kg
            )

        # Create weighted graph
        G2 = self.graph.copy()
        for u, v, k, data in G2.edges(keys=True, data=True):
            data["weight"] = edge_weight(u, v, data)

        # Compute shortest path on weighted graph
        path = nx.shortest_path(G2, origin_node, dest_node, weight="weight")

        return path
