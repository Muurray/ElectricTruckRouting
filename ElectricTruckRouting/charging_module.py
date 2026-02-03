from charging_integration import ChargingStationManager

class ChargingManager:
    """Compatibility wrapper exposing the expected API in main.py."""

    def __init__(self):
        self._mgr = None

    def load_eafo_dataset(self, csv_path):
        # Create manager lazily when needed; graph will be assigned later
        # For now just return the loaded stations
        # NOTE: ChargingStationManager requires a graph for snapping stations;
        # we'll instantiate it once a graph is passed to it by other modules.
        # To keep API simple, load CSV into a temporary manager without graph.
        temp = ChargingStationManager.__init__  # keep reference to class
        # Use ChargingStationManager without graph parameter by passing None
        mgr = ChargingStationManager.__new__(ChargingStationManager)
        # Manually call __init__ with graph=None
        try:
            ChargingStationManager.__init__(mgr, graph=None)
        except TypeError:
            ChargingStationManager.__init__(mgr)
        self._mgr = mgr
        return mgr.load_eafo_dataset(csv_path)

    def snap_stations(self, graph):
        if self._mgr is None:
            self._mgr = ChargingStationManager(graph)
        else:
            self._mgr.graph = graph
        return self._mgr.snap_stations_to_graph()

    # Proxy other useful methods
    def get_candidate_stations_near_route(self, path_nodes, buffer_km=5):
        return self._mgr.get_candidate_stations_near_route(path_nodes, buffer_km=buffer_km)

    def simulate_charging_event(self, soc_initial, target_soc, station_power_kw):
        return self._mgr.simulate_charging_event(soc_initial, target_soc, station_power_kw)
