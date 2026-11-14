"""Mission evaluator: orchestrates the simulation modules into a result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .mass import compute_mass, MassBreakdown
from .power import compute_power, PowerBreakdown
from .communications import compute_communications, CommBreakdown
from .budget import compute_budget, BudgetBreakdown
from .orbit import compute_orbit, OrbitBreakdown


@dataclass
class MissionSpec:
    mission_name: str = "Unnamed mission"
    scenario_name: str = ""
    destination: str = ""
    duration_days: float = 0.0
    required_comm_distance_km: float = 0.0
    orbit_origin_radius_km: float = 1.0  # AU in km? we'll pass km
    orbit_destination_radius_km: float = 1.0
    available_delta_v_ms: float = 0.0
    # component resolved data
    component_masses: List[float] = field(default_factory=list)
    component_consumption_w: List[float] = field(default_factory=list)
    component_generation_w: List[float] = field(default_factory=list)
    component_costs_usd: List[float] = field(default_factory=list)
    component_comm_ranges_km: List[float] = field(default_factory=list)
    component_comm_rates_kbps: List[float] = field(default_factory=list)
    component_battery_wh: float = 0.0
    structure_mass_kg: float = 0.0
    propellant_mass_kg: float = 0.0
    margin_fraction: float = 0.20
    launch_vehicle_capacity_kg: float = 0.0
    launch_vehicle_cost_usd: float = 0.0
    operations_cost_usd: float = 0.0
    budget_limit_usd: float = 0.0
    eclipse_hours: float = 0.0


@dataclass
class SimulationResult:
    mission_name: str
    feasible: bool
    score: int
    mass: MassBreakdown
    power: PowerBreakdown
    communications: CommBreakdown
    budget: BudgetBreakdown
    orbit: OrbitBreakdown
    events: List[str] = field(default_factory=list)
    explanation: str = ""


def evaluate(spec: MissionSpec) -> SimulationResult:
    mass = compute_mass(
        spec.component_masses,
        structure_mass_kg=spec.structure_mass_kg,
        propellant_mass_kg=spec.propellant_mass_kg,
        margin_fraction=spec.margin_fraction,
        capacity_kg=spec.launch_vehicle_capacity_kg,
    )
    power = compute_power(
        spec.component_consumption_w,
        spec.component_generation_w,
        battery_capacity_wh=spec.component_battery_wh,
        eclipse_hours=spec.eclipse_hours,
        mission_duration_hours=spec.duration_days * 24.0,
    )
    comm = compute_communications(
        spec.required_comm_distance_km,
        spec.component_comm_ranges_km,
        spec.component_comm_rates_kbps,
    )
    budget = compute_budget(
        spec.component_costs_usd,
        launch_vehicle_cost_usd=spec.launch_vehicle_cost_usd,
        operations_cost_usd=spec.operations_cost_usd,
        budget_limit_usd=spec.budget_limit_usd,
    )
    orbit = compute_orbit(
        spec.orbit_origin_radius_km,
        spec.orbit_destination_radius_km,
        available_delta_v_ms=spec.available_delta_v_ms,
    )

    events: List[str] = []
    checks = {
        "mass": mass.within_capacity,
        "power": power.balanced,
        "communications": comm.link_closed,
        "budget": budget.within_budget,
        "orbit": orbit.feasible,
    }
    for name, ok in checks.items():
        if ok:
            events.append(f"PASS: {name}")
        else:
            events.append(f"FAIL: {name}")

    feasible = all(checks.values())
    # score: number of passed checks out of 5, scaled to 100
    score = int(round(sum(1 for v in checks.values() if v) / len(checks) * 100))

    parts = []
    if not mass.within_capacity:
        parts.append(
            f"Mass {mass.total_kg:.1f} kg exceeds launch capacity "
            f"{mass.capacity_kg:.1f} kg."
        )
    if not power.balanced:
        parts.append(
            f"Power imbalance: generation {power.generation_w:.1f} W vs "
            f"consumption {power.consumption_w:.1f} W; energy deficit "
            f"{power.energy_deficit_wh:.1f} Wh."
        )
    if not comm.link_closed:
        parts.append(
            f"Communication link not closed: max range {comm.max_range_km:.0f} km "
            f"< required {comm.required_distance_km:.0f} km."
        )
    if not budget.within_budget:
        parts.append(
            f"Budget {budget.total_usd:.0f} USD exceeds limit "
            f"{budget.limit_usd:.0f} USD."
        )
    if not orbit.feasible:
        parts.append(
            f"Orbit: required delta-v {orbit.delta_v_ms:.0f} m/s exceeds "
            f"available {spec.available_delta_v_ms:.0f} m/s."
        )
    if feasible:
        explanation = (
            f"Mission '{spec.mission_name}' is feasible. All constraints "
            f"passed (score {score}/100)."
        )
    else:
        explanation = (
            f"Mission '{spec.mission_name}' is NOT feasible. "
            + " ".join(parts)
        )

    return SimulationResult(
        mission_name=spec.mission_name,
        feasible=feasible,
        score=score,
        mass=mass,
        power=power,
        communications=comm,
        budget=budget,
        orbit=orbit,
        events=events,
        explanation=explanation,
    )