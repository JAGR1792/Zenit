"""Pydantic schemas for the API."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ComponentOut(BaseModel):
    id: str
    name: str
    category: str
    mass_kg: float
    power_consumption_w: float = 0.0
    power_generation_w: float = 0.0
    cost_usd: float
    comm_range_km: float = 0.0
    comm_data_rate_kbps: float = 0.0
    battery_wh: float = 0.0
    description: str = ""
    data_source: str = "estimated"


class LaunchVehicleOut(BaseModel):
    id: str
    name: str
    payload_capacity_kg: float
    compatible_destinations: List[str] = Field(default_factory=list)
    cost_usd: float
    data_source: str = "estimated"


class ScenarioOut(BaseModel):
    id: str
    name: str
    objective: str
    destination: str
    duration_days: float
    required_comm_distance_km: float
    budget_limit_usd: float
    orbit_origin_radius_km: float
    orbit_destination_radius_km: float
    data_source: str = "estimated"


class MissionCreate(BaseModel):
    name: str
    scenario_id: str
    launch_vehicle_id: str
    component_ids: List[str] = Field(default_factory=list)
    structure_mass_kg: float = 0.0
    propellant_mass_kg: float = 0.0
    margin_fraction: float = 0.20
    operations_cost_usd: float = 0.0
    available_delta_v_ms: float = 0.0
    eclipse_hours: float = 0.0


class MassOut(BaseModel):
    structure_kg: float
    components_kg: float
    propellant_kg: float
    margin_kg: float
    total_kg: float
    capacity_kg: float
    within_capacity: bool


class PowerOut(BaseModel):
    generation_w: float
    consumption_w: float
    net_w: float
    battery_capacity_wh: float
    eclipse_hours: float
    energy_deficit_wh: float
    balanced: bool


class CommOut(BaseModel):
    required_distance_km: float
    max_range_km: float
    link_margin_db: float
    data_rate_kbps: float
    link_closed: bool


class BudgetOut(BaseModel):
    components_usd: float
    launch_vehicle_usd: float
    operations_usd: float
    total_usd: float
    limit_usd: float
    within_budget: bool


class OrbitOut(BaseModel):
    delta_v_ms: float
    transfer_time_days: float
    apoapsis_km: float
    feasible: bool
    note: str


class SimulationResultOut(BaseModel):
    id: Optional[str] = None
    mission_name: str
    feasible: bool
    score: int
    mass: MassOut
    power: PowerOut
    communications: CommOut
    budget: BudgetOut
    orbit: OrbitOut
    events: List[str] = Field(default_factory=list)
    explanation: str = ""


class MissionOut(BaseModel):
    id: str
    name: str
    scenario_id: str
    launch_vehicle_id: str
    component_ids: List[str]
    structure_mass_kg: float
    propellant_mass_kg: float
    margin_fraction: float
    operations_cost_usd: float
    available_delta_v_ms: float
    eclipse_hours: float