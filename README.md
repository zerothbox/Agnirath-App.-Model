# Agnirath-App.-Model

## System Architecture for the Base Route

The Solar Race Strategy Model is designed as a sequential, 5-layer pipeline. It ingests raw environmental and vehicle data, evaluates the physical realities of the route, and runs a two-phase optimization (heuristic warm-start + gradient descent) to output the mathematically optimal speed profile.

### Layer 1 — Inputs
The foundation of the simulation, consisting of the static datasets and rules.
* **Route CSV:** Geospatial data and distances across 661 waypoints.
* **Car Constants:** Vehicle-specific physical parameters (mass, aerodynamic drag $C_dA$, rolling resistance, etc.).
* **Race Rules:** Strict event constraints, including maximum time limits and the minimum battery State of Charge (SOC) floor.

### Layer 2 — Core Models
The physics and environmental simulators that calculate energy expenditure and intake.
* **Layer 2A: Physics Engine:** * `mech_power(v, slope)`: Calculates the raw mechanical power required at the wheels to overcome drag, gravity, and rolling resistance.
  * `elec_power(v, slope, eta)`: Converts mechanical power into electrical battery draw, accounting for powertrain and regenerative braking efficiencies ($\eta$).
* **Layer 2B: Solar Model:** * `solar_power(t)`: Calculates incident solar energy based on the time of day.
  * Modeled as a clear-sky Gaussian curve: `I_peak * exp(...)`.

### Layer 3 — Heuristics & Boundaries
The preparation layer that gives the final optimizer a safe, bounded environment to work within.
* **Layer 3A: Greedy Solver:** A fast, energy-aware binary search that calculates a strictly feasible baseline velocity array (`feasible v[]`). This provides the vital "warm start" to prevent the downstream optimizer from getting trapped in local minima.
* **Layer 3B: Speed Limits:** An array of strict upper-bound velocities (`v_hi[]`) mapped to each specific waypoint to ensure traffic and road-rule compliance.

### Layer 4 — SLSQP Optimizer
The professional-grade gradient solver that refines the greedy heuristic into a perfect race strategy.
* **Objective:** Minimise total race time: `Σ d[i]/v[i]`
* **Constraints:** * `SOC ≥ min` (Battery must never drop below the legal floor)
  * `v in bounds` (Velocity must respect minimum speeds and waypoint speed limits)
  * `|Δv| ≤ limit` (Acceleration/deceleration must be physically possible and smooth)

### Layer 5 — Output
* **Strategy DataFrame + CSV:** The finalized, optimized velocity array and expected telemetry logs, exported for the driver interface and race engineers.


## System Architecture for the Distance Maximization Phase

This secondary architecture takes over during the optional loop phase at the Zeerust checkpoint. Instead of minimizing time over a fixed distance, this model maximizes distance (number of loops) within a fixed time window, using a nested optimization approach.

### Layer 1 — Inputs (Handed over from race leg)
The dynamic state of the car at the moment it arrives at the checkpoint, plus the specific rules for the loop phase.
* **State Data:** Current SOC (State of Charge) and the exact clock time at Zeerust.
* **Car Constants:** Vehicle-specific physical parameters (carried over from the main model).
* **Loop Rules:** Loop length ($L$), mandatory stop time per loop ($t_{stop}$), and the strict race deadline.

### Layer 2 — Core Models
* **Layer 2A: Flat Physics:** * `flat_road_power(v)`: Computes mechanical power without the gravity/slope term (straight-line assumption): $k \cdot v^3 + c \cdot v$.
* **Layer 2B: Solar + Stop Charge:** * `solar_power(t)`: The standard Gaussian clear-sky irradiance model.
  * `stop_charge(t_start, 300 s)`: Calculates the stationary solar energy gathered during the mandatory 5-minute (300s) checkpoint hold.

### Layer 3 — Per-Loop Feasibility Bounds (Algebraic)
Establishes the absolute limits for the solver to ensure mathematical feasibility.
* **Minimum Velocity:** Dictated by the ticking clock. 
  * $v_{min} = \frac{N \cdot L}{T_{avail}}$
* **Maximum Velocity:** Dictated by the battery drain. Found by calculating the root of the power cubic equation: 
  * $k \cdot v^3 - (\eta \cdot \frac{\Delta E}{N \cdot L}) \cdot v + (P_{loss} - \eta \cdot P_{sol}) = 0$

### Layer 4 & 5 — The Core Solvers (Nested Optimization)
* **Layer 4: Greedy N Estimator:** Uses a binary search to find a highly probable, feasible loop count (`N_greedy`) and generates a velocity warm-start (`v_warmstart`).
* **Layer 5: SLSQP Inner Optimizer:** Takes the warm-start and minimizes time ($\Sigma \frac{L}{v[i]}$) for that fixed number of loops ($N$).

### Layer 6 — Outer N Maximizer (Integer Scan)
Acts as the ultimate decision-maker. It takes the baseline `N_greedy` loops from Layer 4 and systematically attempts to force the SLSQP optimizer to solve for `N + 1`, `N + 2`, etc. It stops the moment the inner optimizer returns "infeasible", locking in the absolute maximum possible loops ($N^\star$).

### Layer 7 — Output
* **Data Export:** The final optimal loop count ($N^\star$), the specific velocity profile required to achieve it, and the exported tracking logs (`zeerust_loops_strategy.csv`, `zeerust_loops_summary.csv`).
