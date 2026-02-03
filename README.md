A Multi-Objective Optimization Model for National Electric Truck Routing in Germany Using Real EAFO Charging Infrastructure Data

Introduction
Background
The rapid growth of freight transportation has significantly increased CO₂ emissions within the European Union (EU). Heavy-duty vehicles (HDVs), particularly long-haul trucks, account for approximately 25% of total road transport emissions, despite representing less than 5% of vehicles on the road (European Commission, 2024). Electrification of freight logistics through battery-electric trucks (BETs) is one of the most promising pathways to meet European Green Deal targets. As Europe’s logistics hub, Germany has accelerated deployment of high-power charging infrastructure suitable for electric trucks. According to the European Alternative Fuels Observatory (EAFO), Germany currently hosts ≈480 public HDV-capable charging stations, the highest in the EU (EAFO, 2025).However, routing an electric truck across long distances remains challenging due to battery size limitations, charging time constraints, non-uniform charging infrastructure availability, route energy consumption variability, and carbon intensity dependencies.
Problem Statement
The transition from diesel to electric freight transport requires accurate modeling of energy consumption, charging station availability, multi-objective optimization, and grid emission integration.
Research Objectives
1.	Develop a multi-objective mathematical model for electric truck routing.
2.	Model truck energy consumption using physical vehicle dynamics.
3.	Integrate real EAFO-compliant HDV charging station datasets.
4.	Implement and validate the model in Python.
5.	Benchmark against previous routing approaches.
Literature Review
The transition to electric mobility has accelerated research into electric vehicle routing, energy modeling, and charging infrastructure optimization. While the classical Vehicle Routing Problem (VRP) has been extensively studied for more than six decades, the electrification of transport introduces new constraints that fundamentally change routing logic such as limited battery capacity, range uncertainty, non-linear charging characteristics, and the environmental consequences of electricity generation. This chapter reviews the scholarly foundations relevant to the Electric Truck Routing Model developed in this thesis, focusing on four core literature streams: (1) Electric Vehicle Routing Problems, (2) Charging constraints and infrastructure behavior, (3) Energy consumption modeling, and (4) CO₂ intensity and environmental impact. The review concludes by identifying research gaps addressed by this thesis.
The VRP was first formalized by Dantzig and Ramser (1959) as a combinatorial optimization problem concerned with minimizing the cost of delivering goods using a fleet of vehicles. Traditional VRP assumes that vehicles can refuel quickly and operate with minimal constraints besides capacity and travel distance.
However, electrification significantly complicates routing because:
•	Electric vehicles (EVs) have limited range.
•	Charging requires substantial time, not instantaneous refueling.
•	Battery State-of-Charge (SoC) introduces dynamic, non-linear constraints.
•	Charging station availability becomes part of the feasible routing network.
These characteristics motivated the development of the Electric Vehicle Routing Problem (EVRP), formally defined by Conrad and Figliozzi (2011), which integrates battery constraints and charging decisions into routing optimization.
A range of methods has been proposed to solve EVRP which include:
1.	Mixed-Integer Linear Programming (MILP) – provides exact solutions for small networks (Keskin & Çatay, 2017).
2.	Label-setting and multi-criteria shortest-path algorithms – efficient for energy-feasible path construction (Schneider et al., 2014).
3.	Metaheuristics – including Tabu Search, Genetic Algorithms, and Large Neighborhood Search, providing scalable solutions (Macrina et al., 2019).
A consistent finding is that EV routing is computationally harder than VRP due to an expanded feasible state space that includes SoC profiles. As a result, the current thesis adopts a MILP-based model for a single electric truck routing between Hamburg and Munich. The EVRP literature directly informs range constraints, charging station selection, energy-feasible routing, and time windows. Unlike diesel refueling, which typically takes minutes, EV charging durations vary widely based on charger type (AC 22 kW, DC fast-charging 50–350 kW), battery chemistry, SoC at arrival, and temperature. Fast chargers follow a tapering curve where power is reduced after ~80% SoC to protect battery health (Neaimeh et al., 2017). 
Several studies incorporate station queueing models, showing that waiting time can significantly affect total travel time (Xiang et al., 2016). For heavy-duty trucks, where charging spaces may be limited, this effect is amplified. Recent literature indicates that multiple short charges can outperform long single-charging sessions, reducing total route time (Montoya et al., 2017). Optimal strategies often involve recharging only the energy required to reach the next charging node. The charging module of the thesis incorporates charging power levels, non-linear charging effects, and energy required to reach the next station. The research is also directly supported by the literature showing the necessity of modeling charging behavior accurately for realistic routing results.
Electric truck energy consumption depends on vehicle mass and payload, aerodynamic drag and rolling resistance, terrain and elevation, speed variations, and weather conditions. Physics-based models (Lee et al., 2013) define the required traction power using force equilibrium equations, while data-driven models use telematics or machine learning to estimate kWh/km (Lajunen, 2014). Heavy-duty electric trucks typically consume between 1.2–2.0 kWh/km depending on load and terrain (Browne et al., 2020). Long-distance operations are sensitive to small variations in energy modeling accuracy. As a result, the thesis integrates a physics-based energy consumption model derived from rolling resistance, aerodynamic drag, gravitational potential energy, and drivetrain efficiency. This allows the system to calculate whether the truck can reach each segment of the Hamburg → Munich corridor without violating battery limits.
The environmental benefit of electric trucks depends on the CO₂ intensity of the electricity used for charging. According to EAFO and ENTSO-E (2023), European electricity carbon intensity varies geographically:
•	Northern Europe: 50–150 gCO₂/kWh
•	Central Europe: 200–350 gCO₂/kWh
•	Coal-dependent regions: >500 gCO₂/kWh
Temporal variations (day/night cycles, renewable penetration) further influence emissions. Similarly, life-cycle assessments consistently show that EVs reduce emissions compared to diesel trucks, although the magnitude ranges from 50–90% depending on the grid mix (Hawkins et al., 2013). Thus, the current thesis incorporates EAFO-compliant CO₂ factors, enabling the model to calculate total electricity use, CO₂ emissions of each charging session, and full-route CO₂ savings relative to diesel. The models aligns the model with EU transport sustainability frameworks.
The literature shows substantial advances in EV routing, charging, and energy modeling. However, gaps still exist:
1.	Limited focus on long-distance electric trucking in Europe.
2.	Few studies integrate routing + charging + energy modeling + CO₂ intensity in a single framework.
3.	Most models use theoretical datasets rather than EAFO-compliant real infrastructure data.
This thesis addresses these gaps through a real Germany corridor route (Hamburg to Munich), EAFO-style dataset construction, an integrated MILP model for routing and charging, and CO₂-aware objective functions. The reviewed literature demonstrates that EV routing requires a multidisciplinary approach combining optimization, energy modeling, battery science, and environmental assessment. Existing studies provide strong theoretical foundations but also reveal important gaps, particularly regarding heavy-duty EV applications and real charging infrastructure alignment. The thesis contributes to this evolving field by integrating these elements into a unified, practical model for long-distance electric truck routing.
Methodology
Results and Validation
Conclusions and Recommendations

References
Agora Energiewende. (2024). The future of the German electricity grid: CO₂ intensity trends. Berlin, Germany.
Browne, D., O’Mahony, M., & Caulfield, B. (2021). Energy modeling of electric trucks using physics-based simulation. Energy, 224, 120172.
EAFO. (2025). HDV Recharging Infrastructure Dataset Release. European Alternative Fuels Observatory. https://alternative-fuels-observatory.ec.europa.eu
European Commission. (2024). Heavy-duty vehicles CO₂ emission standards. Brussels.
Gao, Z., Zhang, W., & Wang, Y. (2023). Multi-objective routing optimization for battery-electric freight vehicles. Transportation Research Part D, 120, 103868.
Hertwich, E. (2023). Carbon footprints of electricity generation under decarbonization. Nature Energy, 8(3), 214–225.
Schiffer, M., & Walther, G. (2017). The electric vehicle routing problem with time windows and energy consumption. Transportation Research Part B, 104, 322–343.
Xie, Y., Lin, J., & Gong, S. (2020). Routing and scheduling for electric fleets under charging constraints. IEEE Transactions on ITS, 21(7), 2899–2912.

