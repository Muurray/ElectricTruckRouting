# ===============================================================
# route_energy.py
# Compute energy and SOC profile for a given route
# ===============================================================

import numpy as np


class RouteEnergyEvaluator:

    def __init__(self, graph, truck_model, charger_mgr):
        self.graph = graph
        self.truck = truck_model
        self.charger_mgr = charger_mgr

    # -----------------------------------------------------------
    # COMPUTE TOTAL ROUTE ENERGY
    # -----------------------------------------------------------

    def compute_route_energy(self, path_nodes, initial_soc=0.90):
        """
        Compute energy & SOC evolution for a path.
        """

        soc = initial_soc
        total_energy_kwh = 0.0
        segments = []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            edge = self.graph.get_edge_data(u, v)[0]

            length_m = edge["length"]
            speed = edge["speed_kph"] * (1000/3600)
            gradient = edge.get("grade", 0.0)

            energy_kwh = self.truck.compute_edge_energy(length_m, speed, gradient)

            # Update SOC
            soc_new = self.truck.soc_after_segment(soc, energy_kwh)

            segments.append({
                "u": u,
                "v": v,
                "length_m": length_m,
                "energy_kwh": energy_kwh,
                "soc_before": soc,
                "soc_after": soc_new,
                "speed_mps": speed,
                "gradient": gradient
            })

            soc = soc_new
            total_energy_kwh += energy_kwh

        return segments, total_energy_kwh
