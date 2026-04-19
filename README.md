# Agnirath-App.-Model

## System Architecture for the Base Route

The following is a sequential, 5-layer pipeline.

### Layer 1 — Inputs
* **Route CSV:** Geospatial data and distances across waypoints
* **Solar CSV:** Incident solar energy based on time of the day, accurate to 1-second (modelled on as a Gaussian curve)
* **Car Constants:** Race car's physical parameters
* **Race Rules:** Constraints

### Layer 2 — Physics Engine
The physics and environmental simulators that calculate energy expenditure
* `mech_power(v, slope)`: Calculates the raw mechanical power required at the wheels to overcome drag, gravity, and rolling resistance
* `elec_power(v, slope, eta)`: Converts mechanical power into electrical battery draw

### Layer 3 — Heuristics
The preparation layer that aids the final optimizer with a bounded environment to work within.
* **Layer 3A: Greedy Solver:** A fast binary search that calculates a strictly feasible baseline velocity array (`feasible v[]`). This is to prevent the main optimizer from getting trapped in a local minimum.
* **Layer 3B: Speed Limits:** An array of strict upper-bound velocities (`v_hi[]`) mapped to each specific waypoint to ensure constraints

### Layer 4 — SLSQP Optimizer
The layer the refines the greedy heuristic into a complete strategy.
* **Objective:** Minimise total race time: `Σ d[i]/v[i]`
* **Main Constraints:** * `SOC ≥ min` (Battery must never drop below the legal floor)
  * `v in bounds` (Velocity must respect minimum speeds and waypoint speed limits)
  * `|Δv| ≤ limit` (Acceleration must be smooth)

### Layer 5 — Output
* **Strategy DataFrame + CSV:** The finalized, optimized velocity array and expected telemetry logs.


## System Architecture for the Distance Maximization Phase

This secondary architecture takes over during the optional loop phase at the Zeerust checkpoint. Instead of minimizing time over a fixed distance, this model maximizes distance within a fixed time window.

### Layer 1 — Inputs (Passed over from the base race)
The dynamic state of the car at the moment it arrives at the checkpoint, plus the specific rules for the loop phase.
* **State Data:** Current SOC (State of Charge) and the time.
* **Car Constants:** Vehicle's physical parameters
* **Solar CSV:** Incident solar energy based on time of the day, accurate to 1-second (modelled on as a Gaussian curve)
* **Loop Rules:** Loop length ($L$), mandatory stop time per loop ($t_{stop}$), and the race deadline.

### Layer 2 — Physics Engine
* **Flat Physics:** * `flat_road_power(v)`: Computes mechanical power with the straight-line assumption: $k \cdot v^3 + c \cdot v$.

### Layer 3 — Feasibility Bounds
Establishes the absolute limits.
* **Minimum Velocity:** Dictated by the time left. 
  * $v_{min} = \frac{N \cdot L}{T_{avail}}$
* **Maximum Velocity:** Dictated by the battery SoC. Found by calculating the root of the power cubic equation: 
  * $k \cdot v^3 - (\eta \cdot \frac{\Delta E}{N \cdot L}) \cdot v + (P_{loss} - \eta \cdot P_{sol}) = 0$

### Layer 4 — The Core Optimizer
* **SLSQP:** Takes values of N from 1 and increments by 1 and minimizes time ($\Sigma \frac{L}{v[i]}$) for that fixed number of loops ($N$).

### Layer 5 — Output
* **Data Export:** The final highest feasible loop count ($N^\star$) and the specific velocity profile required to achieve it
