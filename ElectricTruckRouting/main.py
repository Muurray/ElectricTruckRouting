import pandas as pd
from graph_builder import RoadNetwork
from energy_model import EnergyModel
from charging_module import ChargingManager
from optimization_model import MultiObjectiveOptimizer

# --------------------------------------------------------
# 1. Load EAFO Charging Data
# --------------------------------------------------------
charging_data_path = "data/eafo_germany_hdv_charging.csv"
df = pd.read_csv(charging_data_path)

charger_mgr = ChargingManager()
charger_mgr.load_eafo_dataset(charging_data_path)

# --------------------------------------------------------
# 2. Initialize Vehicle Energy Model
# --------------------------------------------------------
truck_energy = EnergyModel(
    mass_kg=42000,
    frontal_area_m2=10.2,
    drag_coeff=0.63,
    rolling_resistance=0.0065,
    battery_kwh=600,
    drivetrain_eff=0.92
)

# --------------------------------------------------------
# 3. Build Routing Graph (Hamburg → Munich)
# --------------------------------------------------------
graph = RoadNetwork()
graph.build_graph_with_chargers(df)

start_city = "Hamburg"
end_city = "Munich"

start_node = graph.get_city_coordinates(start_city)
end_node = graph.get_city_coordinates(end_city)

# Add start and end as nodes
graph.add_custom_point("start", start_node)
graph.add_custom_point("end", end_node)

# --------------------------------------------------------
# 4. Initialize Optimizer
# --------------------------------------------------------
optimizer = MultiObjectiveOptimizer(
    graph=graph,
    charger_mgr=charger_mgr,
    energy_model=truck_energy
)

# --------------------------------------------------------
# 5. Run Optimization (NSGA-II)
# --------------------------------------------------------
print("Running multi-objective optimization...")
pareto_solutions = optimizer.run_nsga(
    start="start",
    end="end",
    population=40,
    generations=20
)

# --------------------------------------------------------
# 6. Print Best Solutions
# Plot Pareto-optimal routes (visualization)
optimizer.plot_routes(pareto_solutions)
# --------------------------------------------------------
for sol in pareto_solutions:
    print("\n--- Solution ---")
    print(f"Cost: {sol.cost:.2f} €")
    print(f"Energy: {sol.energy:.2f} kWh")
    print(f"CO2: {sol.co2:.2f} kg")
    print(f"Path: {sol.path}")
