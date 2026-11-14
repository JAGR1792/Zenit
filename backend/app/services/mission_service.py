"""Application services: build MissionSpec from stored data and run evaluation."""

from __future__ import annotations

import json
from typing import List

from sqlalchemy.orm import Session

from ..models.orm import (
    ScenarioORM, ComponentORM, LaunchVehicleORM, MissionORM, compatible_list,
)
from ..schemas.mission import MissionCreate, MissionOut
from ..simulation.evaluator import MissionSpec, evaluate, SimulationResult
from ..simulation.mass import MassBreakdown


def scenario_to_dict(s: ScenarioORM) -> dict:
    return {
        "id": s.id, "name": s.name, "objective": s.objective,
        "destination": s.destination, "duration_days": s.duration_days,
        "required_comm_distance_km": s.required_comm_distance_km,
        "budget_limit_usd": s.budget_limit_usd,
        "orbit_origin_radius_km": s.orbit_origin_radius_km,
        "orbit_destination_radius_km": s.orbit_destination_radius_km,
        "data_source": s.data_source,
    }


def component_to_dict(c: ComponentORM) -> dict:
    return {
        "id": c.id, "name": c.name, "category": c.category,
        "mass_kg": c.mass_kg, "power_consumption_w": c.power_consumption_w,
        "power_generation_w": c.power_generation_w, "cost_usd": c.cost_usd,
        "comm_range_km": c.comm_range_km, "comm_data_rate_kbps": c.comm_data_rate_kbps,
        "battery_wh": c.battery_wh, "description": c.description,
        "data_source": c.data_source,
    }


def lv_to_dict(lv: LaunchVehicleORM) -> dict:
    return {
        "id": lv.id, "name": lv.name, "payload_capacity_kg": lv.payload_capacity_kg,
        "compatible_destinations": compatible_list(lv.compatible_destinations),
        "cost_usd": lv.cost_usd, "data_source": lv.data_source,
    }


def mission_to_out(m: MissionORM) -> MissionOut:
    try:
        cids = json.loads(m.component_ids or "[]")
    except Exception:
        cids = []
    return MissionOut(
        id=m.id, name=m.name, scenario_id=m.scenario_id,
        launch_vehicle_id=m.launch_vehicle_id, component_ids=cids,
        structure_mass_kg=m.structure_mass_kg, propellant_mass_kg=m.propellant_mass_kg,
        margin_fraction=m.margin_fraction, operations_cost_usd=m.operations_cost_usd,
        available_delta_v_ms=m.available_delta_v_ms, eclipse_hours=m.eclipse_hours,
    )


def create_mission(db: Session, payload: MissionCreate) -> str:
    from ..repositories.data import create_mission as repo_create
    data = payload.model_dump()
    return repo_create(db, data)


def build_spec(db: Session, mission_id: str) -> MissionSpec:
    from ..repositories.data import get_mission
    m = get_mission(db, mission_id)
    if m is None:
        raise ValueError("mission not found")
    scen = db.query(ScenarioORM).filter(ScenarioORM.id == m.scenario_id).first()
    lv = db.query(LaunchVehicleORM).filter(LaunchVehicleORM.id == m.launch_vehicle_id).first()
    try:
        cids = json.loads(m.component_ids or "[]")
    except Exception:
        cids = []
    comps = db.query(ComponentORM).filter(ComponentORM.id.in_(cids)).all() if cids else []

    spec = MissionSpec(
        mission_name=m.name,
        scenario_name=scen.name if scen else "",
        destination=scen.destination if scen else "",
        duration_days=scen.duration_days if scen else 0.0,
        required_comm_distance_km=scen.required_comm_distance_km if scen else 0.0,
        orbit_origin_radius_km=scen.orbit_origin_radius_km if scen else 0.0,
        orbit_destination_radius_km=scen.orbit_destination_radius_km if scen else 0.0,
        available_delta_v_ms=m.available_delta_v_ms,
        component_masses=[c.mass_kg for c in comps],
        component_consumption_w=[c.power_consumption_w for c in comps],
        component_generation_w=[c.power_generation_w for c in comps],
        component_costs_usd=[c.cost_usd for c in comps],
        component_comm_ranges_km=[c.comm_range_km for c in comps],
        component_comm_rates_kbps=[c.comm_data_rate_kbps for c in comps],
        component_battery_wh=sum(c.battery_wh for c in comps),
        structure_mass_kg=m.structure_mass_kg,
        propellant_mass_kg=m.propellant_mass_kg,
        margin_fraction=m.margin_fraction,
        launch_vehicle_capacity_kg=lv.payload_capacity_kg if lv else 0.0,
        launch_vehicle_cost_usd=lv.cost_usd if lv else 0.0,
        operations_cost_usd=m.operations_cost_usd,
        budget_limit_usd=scen.budget_limit_usd if scen else 0.0,
        eclipse_hours=m.eclipse_hours,
    )
    return spec


def run_simulation(db: Session, mission_id: str) -> SimulationResult:
    spec = build_spec(db, mission_id)
    return evaluate(spec)