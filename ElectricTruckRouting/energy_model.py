# ===============================================================
# energy_model.py
# Energy consumption model for a heavy-duty electric truck
# Used for Germany long-haul routing (Hamburg → Munich)
# ===============================================================

import numpy as np
import math

class ElectricTruckModel:
    """
    Heavy-duty electric truck energy model approximated using
    parameters from MAN eTruck 2024 / Mercedes eActros Long-Haul.
    """

    def __init__(self):
        # ----------- VEHICLE PHYSICAL PARAMETERS -----------
        self.mass_kg = 40000            # 40 tonnes GCWR (fully loaded)
        self.frontal_area = 9.0         # m²
        self.drag_coefficient = 0.55    # typical for HD trucks
        self.rolling_res_coeff = 0.006  # asphalt/bitumen highway
        self.air_density = 1.225        # kg/m³ at 15°C sea-level

        # ----------- POWERTRAIN EFFICIENCY -----------
        self.drivetrain_eff = 0.90               # motor + inverter
        self.regen_eff = 0.65                    # downhill / braking
        self.aux_load_kw = 2.5                   # HVAC, electronics
        self.temperature_loss_factor = 1.0       # no derating yet

        # ----------- BATTERY PARAMETERS -----------
        self.battery_capacity_kwh = 600          # typical for long-haul BEV trucks
        self.min_soc = 0.10                      # cannot go below 10%
        self.max_soc = 1.00

    # ===============================================================
    # PHYSICAL ENERGY COMPONENTS
    # ===============================================================

    def rolling_resistance_power(self, speed_mps):
        """
        Rolling resistance: P = Cr * m * g * v
        """
        g = 9.81
        return self.rolling_res_coeff * self.mass_kg * g * speed_mps

    def aerodynamic_drag_power(self, speed_mps):
        """
        Aerodynamic drag: P = 1/2 * rho * Cd * A * v³
        """
        return 0.5 * self.air_density * self.drag_coefficient * self.frontal_area * speed_mps**3

    def climbing_power(self, gradient, speed_mps):
        """
        Climbing power: P = m * g * grade * v
        """
        g = 9.81
        return self.mass_kg * g * gradient * speed_mps

    # ===============================================================
    # MAIN ENERGY COMPUTATION
    # ===============================================================

    def segment_energy_kwh(self, distance_m, avg_speed_mps, gradient):
        """
        Compute energy required for a road segment.
        Includes rolling, aero, gradient, auxiliaries.

        Parameters:
            - distance_m: segment length in meters
            - avg_speed_mps: average speed in m/s
            - gradient: slope = rise/run (positive uphill)

        Returns:
            Energy in kWh (positive uphill, negative for regen)
        """

        # Power contributions
        P_roll = self.rolling_resistance_power(avg_speed_mps)
        P_drag = self.aerodynamic_drag_power(avg_speed_mps)
        P_climb = self.climbing_power(gradient, avg_speed_mps)

        # Aux power
        P_aux = self.aux_load_kw * 1000  # convert kW → W

        # Total mechanical power
        P_total = P_roll + P_drag + P_climb + P_aux

        # Time to traverse segment
        time_sec = distance_m / avg_speed_mps

        # Mechanical energy
        E_mech_wh = (P_total * time_sec) / 3600 * 1000  # Wh

        # Apply drivetrain and regen efficiency
        if E_mech_wh >= 0:
            # Uphill / normal driving
            E_elec_wh = E_mech_wh / self.drivetrain_eff
        else:
            # Negative energy → regen
            E_elec_wh = E_mech_wh * self.regen_eff

        # Convert to kWh
        return E_elec_wh / 1000

    # ===============================================================
    # SOC UPDATE
    # ===============================================================

    def soc_after_segment(self, soc_initial, energy_kwh):
        """
        Update SOC after consuming energy.
        """
        battery_kwh_used = energy_kwh
        soc_new = soc_initial - (battery_kwh_used / self.battery_capacity_kwh)
        return soc_new

    def soc_valid(self, soc_value):
        """
        Check whether SOC is within allowable limits.
        """
        return self.min_soc <= soc_value <= self.max_soc

    # ===============================================================
    # TEMPERATURE DERATING MODULE (OPTIONAL)
    # ===============================================================

    def apply_temperature_effect(self, temp_c):
        """
        Adjust battery performance for cold temperatures.
        (Source: empirical modeling from Zubi et al. + DOE EV studies)
        """
        if temp_c < 0:
            self.temperature_loss_factor = 1.15    # 15% more energy
        elif temp_c < 10:
            self.temperature_loss_factor = 1.05
        else:
            self.temperature_loss_factor = 1.00

    # ===============================================================
    # WRAPPER FOR EDGE PROCESSING
    # ===============================================================

    def compute_edge_energy(self, edge_length_m, speed_mps, gradient, temp_c=15):
        """
        Wrapper function used during route computation.
        """
        self.apply_temperature_effect(temp_c)

        base_energy = self.segment_energy_kwh(edge_length_m, speed_mps, gradient)
        return base_energy * self.temperature_loss_factor


# -----------------------------------------------------------------
# Compatibility wrapper expected by the project's `main.py` script
# -----------------------------------------------------------------
class EnergyModel(ElectricTruckModel):
    """Compatibility wrapper that exposes the constructor used in
    `main.py` and a helper to compute route energy from a sequence of
    nodes. This keeps the existing detailed model but provides a
    simple compute_route_energy() used by the optimizer.
    """

    def __init__(self, mass_kg=42000, frontal_area_m2=10.2, drag_coeff=0.63,
                 rolling_resistance=0.0065, battery_kwh=600, drivetrain_eff=0.92):
        super().__init__()
        # Map parameters into ElectricTruckModel fields where sensible
        self.mass_kg = mass_kg
        self.frontal_area = frontal_area_m2
        self.drag_coefficient = drag_coeff
        self.rolling_res_coeff = rolling_resistance
        self.battery_capacity_kwh = battery_kwh
        self.drivetrain_eff = drivetrain_eff
        # A simple default consumption per km used by the lightweight optimizer
        self.consumption_kwh_per_km = 1.45

    def compute_route_energy(self, path_nodes, graph=None):
        """Compute route energy in kWh for a list of ordered nodes.

        If a graph is provided (networkx), it will sum actual edge lengths;
        otherwise it falls back to 1.45 kWh/km * straight-line estimate.
        Returns: (distance_km, energy_kwh)
        """
        total_m = 0.0
        if graph is not None:
            for i in range(len(path_nodes)-1):
                u, v = path_nodes[i], path_nodes[i+1]
                data = graph.get_edge_data(u, v)
                if data is None:
                    continue
                first = list(data.values())[0]
                total_m += first.get('length', 1000.0)
        else:
            # fallback: assume 100 km between each node
            total_m = 1000.0 * max(1, len(path_nodes)-1)

        km = total_m / 1000.0
        energy = km * self.consumption_kwh_per_km
        return km, energy
