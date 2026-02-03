# ==========================================================
# Electric Truck Routing Model: Hamburg → Munich
# Full Germany OSM Routing + Battery Constraints + Charging
# Multi-objective optimization using Pyomo
# ==========================================================
# Required pip installs:
# pip install osmnx pyomo networkx numpy pandas shapely matplotlib geopy
# ==========================================================

import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# ==========================================================
# 1. INPUTS & ASSUMPTIONS (Imagined / Realistic)
# ==========================================================

ORIGIN = "Hamburg, Germany"
DESTINATION = "Munich, Germany"

# Truck technical data (based on MAN eTruck / Mercedes eActros)
BATTERY_KWH = 600
CONSUMPTION_KWH_PER_KM = 1.45
MAX_CHARGE_POWER_KW = 350
SOC_MIN = 0.10 * BATTERY_KWH
SOC_MAX = BATTERY_KWH

# German electricity & CO2 (OPSD - MOCKED)
GERMAN_GRID_CO2 = 0.42      # kg CO2 per kWh
ELECTRICITY_PRICE = 0.32    # €/kWh

# Charging stations (EAFO - MOCKED)
# Format: [(lat, lon, power_kW), ...]
CHARGING_STATIONS = [
    (52.3759, 9.7320, 350),   # Hannover
    (51.0504, 13.7373, 350),  # Dresden (not on direct path but valid)
    (50.1109, 8.6821, 350),   # Frankfurt
    (49.4521, 11.0767, 350),  # Nuremberg
]


# ==========================================================
# 2. DOWNLOAD GERMANY ROAD NETWORK USING OSMnx
# ==========================================================

print("Downloading Germany road network (major roads only)...")

G = ox.graph_from_place(
    "Germany",
    network_type="drive",
    simplify=True
)

# Convert to undirected for easier path search
G = ox.utils_graph.get_undirected(G)


# ==========================================================
# 3. GET ORIGIN/DESTINATION NODES
# ==========================================================

print(f"Locating origin ({ORIGIN}) and destination ({DESTINATION})...")

origin_point = ox.geocode(ORIGIN)
destination_point = ox.geocode(DESTINATION)

origin_node = ox.nearest_nodes(G, origin_point[1], origin_point[0])
destination_node = ox.nearest_nodes(G, destination_point[1], destination_point[0])


# ==========================================================
# 4. SHORTEST PATH (BASELINE)
# ==========================================================

print("Computing baseline shortest path...")
baseline_route = nx.shortest_path(G, origin_node, destination_node, weight="length")
baseline_length_km = sum(
    ox.utils_graph.get_route_edge_attributes(G, baseline_route, "length")
) / 1000

print(f"Baseline distance: {baseline_length_km:.1f} km")


# ==========================================================
# 5. PREPROCESS ROUTE FOR OPTIMIZATION NODES
# ==========================================================

# Extract coordinates of baseline route
route_coords = ox.utils_graph.get_route_edge_attributes(G, baseline_route, "geometry")

route_points = []
for geom in route_coords:
    if geom is None:
        continue
    for x, y in geom.coords:
        route_points.append((y, x))  # (lat, lon)

# Reduce points for computational feasibility
ROUTE_STEP = 20
route_points = route_points[::ROUTE_STEP]

N = len(route_points)
print(f"Optimized routing will use {N} discretized waypoints.")


# ==========================================================
# 6. BUILD OPTIMIZATION MODEL
# ==========================================================

model = pyo.ConcreteModel()

# Sets
model.N = pyo.RangeSet(0, N - 1)

# SOC at each waypoint
model.soc = pyo.Var(model.N, bounds=(SOC_MIN, SOC_MAX))

# Charging decision variable (kWh charged)
model.charge = pyo.Var(model.N, domain=pyo.NonNegativeReals)

# Objective weights (multi-objective scalarization)
w_energy = 0.40
w_time = 0.30
w_emissions = 0.30

# ----------------------------------------------------------
# ENERGY CONSUMPTION ON ROUTE
# ----------------------------------------------------------

distances = []
for i in range(N - 1):
    distances.append(
        geodesic(route_points[i], route_points[i+1]).km
    )
distances.append(0)

energy_use = [d * CONSUMPtiON_KWH_PER_KM for d in distances]


# ----------------------------------------------------------
# OBJECTIVE FUNCTION
# ----------------------------------------------------------

def objective_rule(model):
    total_energy = sum(energy_use[i] for i in model.N)
    total_charging_cost = sum(model.charge[i] * ELECTRICITY_PRICE for i in model.N)
    total_co2 = sum(model.charge[i] * GERMAN_GRID_CO2 for i in model.N)

    return (w_energy * total_energy +
            w_time * sum(model.charge[i] / MAX_CHARGE_POWER_KW for i in model.N) +
            w_emissions * total_co2)

model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

# ----------------------------------------------------------
# CONSTRAINTS
# ----------------------------------------------------------

# SOC dynamics
def soc_rule(model, i):
    if i == 0:
        return model.soc[i] == SOC_MAX
    return model.soc[i] == model.soc[i-1] - energy_use[i-1] + model.charge[i-1]

model.soc_constraint = pyo.Constraint(model.N, rule=soc_rule)

# Charging only at station coordinates (mock rule)
def charging_station_rule(model, i):
    lat, lon = route_points[i]
    dmin = min(
        geodesic((lat, lon), (cs[0], cs[1])).km
        for cs in CHARGING_STATIONS
    )
    if dmin > 5:  # must be within 5 km of station
        return model.charge[i] == 0
    return pyo.Constraint.Skip

model.charging_station_constraints = pyo.Constraint(model.N, rule=charging_station_rule)


# ==========================================================
# 7. SOLVE MODEL
# ==========================================================

solver = pyo.SolverFactory("glpk")
result = solver.solve(model, tee=True)


# ==========================================================
# 8. PRINT RESULTS
# ==========================================================

print("\n=== OPTIMIZED ROUTE RESULTS ===")
total_energy = sum(energy_use)
total_charging = sum(model.charge[i]() for i in model.N)

print(f"Trip distance: {baseline_length_km:.2f} km")
print(f"Total driving energy required: {total_energy:.1f} kWh")
print(f"Total charging energy added: {total_charging:.1f} kWh")

print("\nCharging stops:")
for i in model.N:
    if model.charge[i]() > 1:
        lat, lon = route_points[i]
        print(f"- Stop at ({lat:.4f}, {lon:.4f}) → charge {model.charge[i]():.1f} kWh")

# ==========================================================
# 9. PLOT SOC CURVE
# ==========================================================

soc_vals = [model.soc[i]() for i in model.N]

plt.plot(soc_vals)
plt.title("State of Charge Along Route")
plt.xlabel("Waypoint index")
plt.ylabel("SOC (kWh)")
plt.grid(True)
plt.show()
