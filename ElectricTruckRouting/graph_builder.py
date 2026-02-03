import networkx as nx

class RoadNetwork:
    """Lightweight RoadNetwork stub for compatibility with main.py

    This creates a small synthetic graph connecting Hamburg and Munich
    so the examples and optimizer can run quickly without downloading
    full Germany OSM data.
    """

    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.custom_points = {}

    def build_graph_with_chargers(self, chargers_df=None):
        # Synthetic nodes with approximate lat/lon
        nodes = {
            "Hamburg": (53.5511, 9.9937),
            "Hannover": (52.3791, 9.7596),
            "Magdeburg": (52.1205, 11.6276),
            "Erfurt": (50.9848, 11.0299),
            "Nuremberg": (49.4521, 11.0767),
            "Munich": (48.1351, 11.5820)
        }

        # Add nodes
        for name, (lat, lon) in nodes.items():
            self.G.add_node(name, x=lon, y=lat)

        # Add edges (directed) with lengths (m) and speed_kph
        edges = [
            ("Hamburg", "Hannover", 150000.0, 100),
            ("Hannover", "Magdeburg", 120000.0, 100),
            ("Magdeburg", "Erfurt", 200000.0, 100),
            ("Erfurt", "Nuremberg", 230000.0, 100),
            ("Nuremberg", "Munich", 170000.0, 100),
            # alternative route
            ("Hannover", "Nuremberg", 360000.0, 100),
        ]

        for u, v, length_m, speed in edges:
            self.G.add_edge(u, v, length=length_m, speed_kph=speed)
            # Add travel_time_h convenience attribute
            self.G[u][v][0]["travel_time_h"] = (length_m / 1000) / speed

        return self.G

    def get_city_coordinates(self, city_name):
        # Return (lat, lon) tuple for a known city
        n = self.G.nodes.get(city_name)
        if n:
            return (n["y"], n["x"])  # (lat, lon)
        # fallback: return None
        return None

    def add_custom_point(self, name, coords):
        # coords expected as (lat, lon)
        lat, lon = coords
        self.custom_points[name] = coords
        self.G.add_node(name, x=lon, y=lat)

        # Connect this custom point to the nearest existing city node
        def haversine_km(a_lat, a_lon, b_lat, b_lon):
            from math import radians, sin, cos, asin, sqrt
            R = 6371.0
            dlat = radians(b_lat - a_lat)
            dlon = radians(b_lon - a_lon)
            a = sin(dlat/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dlon/2)**2
            c = 2 * asin(min(1, sqrt(a)))
            return R * c

        nearest = None
        nearest_dist_km = float('inf')
        for n, data in self.G.nodes(data=True):
            if n == name:
                continue
            n_lat = data.get('y')
            n_lon = data.get('x')
            if n_lat is None or n_lon is None:
                continue
            dkm = haversine_km(lat, lon, n_lat, n_lon)
            if dkm < nearest_dist_km:
                nearest_dist_km = dkm
                nearest = n

        if nearest is not None:
            # Add bidirectional short edges to connect custom point
            length_m = max(500.0, nearest_dist_km * 1000.0)
            speed = 80  # assumed connector speed
            self.G.add_edge(name, nearest, length=length_m, speed_kph=speed)
            self.G.add_edge(nearest, name, length=length_m, speed_kph=speed)
            self.G[name][nearest][0]["travel_time_h"] = (length_m / 1000) / speed
            self.G[nearest][name][0]["travel_time_h"] = (length_m / 1000) / speed

        return name

    # Helper to provide networkx-compatible API used elsewhere
    def copy(self):
        return self.G.copy()

    def get_graph(self):
        return self.G
