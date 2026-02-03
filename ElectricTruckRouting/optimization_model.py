import networkx as nx
import matplotlib.pyplot as plt

class ParetoSolution:
    def __init__(self, cost, energy, co2, path):
        self.cost = cost
        self.energy = energy
        self.co2 = co2
        self.path = path

class MultiObjectiveOptimizer:
    """Lightweight optimizer compatible with main.py's expected API.

    This uses simple scalarization with a few weight combinations to
    produce a small Pareto front from a small synthetic graph.
    """

    def __init__(self, graph, charger_mgr, energy_model):
        # Accept either RoadNetwork wrapper or a raw networkx graph
        try:
            self.G = graph.get_graph()
        except Exception:
            # assume graph is already a networkx graph
            self.G = graph
        self.charger_mgr = charger_mgr
        self.energy_model = energy_model

    def _path_metrics(self, path_nodes):
        # Compute distance, energy, and simple CO2 metric
        total_m = 0.0
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            data = self.G.get_edge_data(u, v)
            if data is None:
                continue
            # Get the first edge's data
            first = list(data.values())[0]
            total_m += first.get('length', 1000.0)
        km = total_m / 1000.0
        # Energy: use energy_model if it has a simple per-km method
        try:
            energy = km * getattr(self.energy_model, 'consumption_kwh_per_km', 1.45)
        except Exception:
            energy = km * 1.45
        # Cost (€/kWh assumed 0.32) and CO2 (kg, 0.42 kg/kWh)
        cost = energy * 0.32
        co2 = energy * 0.42
        return cost, energy, co2

    def run_nsga(self, start, end, population=40, generations=20):
        # Build a small set of weight combinations to approximate Pareto front
        weight_sets = [
            (1.0, 0.0, 0.0),  # time-only (distance)
            (0.0, 1.0, 0.0),  # energy-only
            (0.0, 0.0, 1.0),  # emissions-only (equivalent to energy)
            (0.33, 0.33, 0.34),
            (0.5, 0.25, 0.25)
        ]

        solutions = []
        # Convert start/end node names to actual nodes if necessary
        if start in self.G.nodes:
            start_node = start
        else:
            start_node = start
        if end in self.G.nodes:
            end_node = end
        else:
            end_node = end

        # For each weight set, compute shortest path with a composed weight
        for w_time, w_energy, w_em in weight_sets:
            # Assign edge weights
            G2 = self.G.copy()
            for u, v, k, data in list(G2.edges(keys=True, data=True)):
                dist_km = data.get('length', 1000.0) / 1000.0
                speed = data.get('speed_kph', 100)
                time_h = dist_km / speed
                energy = dist_km * 1.45
                em_kg = energy * 0.42
                data['weight'] = w_time * time_h + w_energy * energy + w_em * em_kg
            try:
                path = nx.shortest_path(G2, start_node, end_node, weight='weight')
            except Exception:
                path = []
            cost, energy, co2 = self._path_metrics(path)
            solutions.append(ParetoSolution(cost, energy, co2, path))

        # Deduplicate by path
        unique = {}
        for s in solutions:
            key = tuple(s.path)
            if key not in unique:
                unique[key] = s
        return list(unique.values())

    def plot_routes(self, pareto_solutions):
        # Basic matplotlib plot showing node positions and route lines
        plt.figure(figsize=(8,6))
        # plot nodes
        xs = [d.get('x', 0) for n, d in self.G.nodes(data=True)]
        ys = [d.get('y', 0) for n, d in self.G.nodes(data=True)]
        plt.scatter(xs, ys, c='k', s=20)
        for sol in pareto_solutions:
            xs = []
            ys = []
            for n in sol.path:
                d = self.G.nodes[n]
                xs.append(d.get('x', 0))
                ys.append(d.get('y', 0))
            plt.plot(xs, ys, label=f"cost={sol.cost:.1f}€, e={sol.energy:.1f}kWh")
        plt.legend()
        plt.title('Pareto route candidates')
        plt.xlabel('lon')
        plt.ylabel('lat')
        plt.grid(True)
        plt.show()
