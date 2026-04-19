# Agnirath-App.-Model

## System Architecture

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
