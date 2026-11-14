"""API v1 routes."""

from __future__ import annotations

import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.db import SessionLocal
from ..repositories.data import (
    list_scenarios, get_scenario, list_components, get_components_by_ids,
    list_launch_vehicles, get_launch_vehicle, get_mission, save_simulation, get_simulation,
)
from ..schemas.mission import (
    ScenarioOut, ComponentOut, LaunchVehicleOut, MissionCreate, MissionOut,
    SimulationResultOut, MassOut, PowerOut, CommOut, BudgetOut, OrbitOut,
)
from ..services.mission_service import (
    scenario_to_dict, component_to_dict, lv_to_dict, mission_to_out,
    create_mission, run_simulation,
)
from ..simulation.evaluator import SimulationResult

router = APIRouter(prefix="/api/v1")


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/scenarios", response_model=List[ScenarioOut])
def get_scenarios(db: Session = Depends(db_dep)):
    return [ScenarioOut(**scenario_to_dict(s)) for s in list_scenarios(db)]


@router.get("/components", response_model=List[ComponentOut])
def get_components(db: Session = Depends(db_dep)):
    return [ComponentOut(**component_to_dict(c)) for c in list_components(db)]


@router.get("/launch-vehicles", response_model=List[LaunchVehicleOut])
def get_launch_vehicles(db: Session = Depends(db_dep)):
    return [LaunchVehicleOut(**lv_to_dict(lv)) for lv in list_launch_vehicles(db)]


@router.post("/missions", response_model=MissionOut, status_code=201)
def create_mission_endpoint(payload: MissionCreate, db: Session = Depends(db_dep)):
    mid = create_mission(db, payload)
    m = get_mission(db, mid)
    return mission_to_out(m)


@router.post("/missions/validate", response_model=SimulationResultOut)
def validate_mission(payload: MissionCreate, db: Session = Depends(db_dep)):
    # Validate without persisting: create temp mission? Instead build spec inline.
    # Simpler: persist then run; but validate should not persist. We'll build spec
    # by creating a temporary mission row then delete. Easier: run via a helper.
    from ..services.mission_service import build_spec
    from ..repositories.data import create_mission as repo_create, get_mission
    import json
    mid = repo_create(db, payload.model_dump())
    try:
        res = run_simulation(db, mid)
        out = _result_to_out(res)
        return out
    finally:
        # remove temp mission
        m = get_mission(db, mid)
        if m:
            db.delete(m)
            db.commit()


@router.post("/simulations", response_model=SimulationResultOut, status_code=201)
def create_simulation(payload: dict, db: Session = Depends(db_dep)):
    mission_id = payload.get("mission_id")
    if not mission_id:
        # allow creating mission inline
        from ..schemas.mission import MissionCreate
        mc = MissionCreate(**payload)
        mission_id = create_mission(db, mc)
    res = run_simulation(db, mission_id)
    from ..repositories.data import save_simulation
    sid = save_simulation(db, mission_id, _result_to_json(res))
    out = _result_to_out(res)
    out.id = sid
    return out


@router.get("/simulations/{sim_id}", response_model=SimulationResultOut)
def get_simulation_endpoint(sim_id: str, db: Session = Depends(db_dep)):
    s = get_simulation(db, sim_id)
    if s is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    data = json.loads(s.result_json)
    return SimulationResultOut(**data)


def _result_to_out(res: SimulationResult) -> SimulationResultOut:
    return SimulationResultOut(
        mission_name=res.mission_name,
        feasible=res.feasible,
        score=res.score,
        mass=MassOut(
            structure_kg=res.mass.structure_kg,
            components_kg=res.mass.components_kg,
            propellant_kg=res.mass.propellant_kg,
            margin_kg=res.mass.margin_kg,
            total_kg=res.mass.total_kg,
            capacity_kg=res.mass.capacity_kg,
            within_capacity=res.mass.within_capacity,
        ),
        power=PowerOut(
            generation_w=res.power.generation_w,
            consumption_w=res.power.consumption_w,
            net_w=res.power.net_w,
            battery_capacity_wh=res.power.battery_capacity_wh,
            eclipse_hours=res.power.eclipse_hours,
            energy_deficit_wh=res.power.energy_deficit_wh,
            balanced=res.power.balanced,
        ),
        communications=CommOut(
            required_distance_km=res.communications.required_distance_km,
            max_range_km=res.communications.max_range_km,
            link_margin_db=res.communications.link_margin_db,
            data_rate_kbps=res.communications.data_rate_kbps,
            link_closed=res.communications.link_closed,
        ),
        budget=BudgetOut(
            components_usd=res.budget.components_usd,
            launch_vehicle_usd=res.budget.launch_vehicle_usd,
            operations_usd=res.budget.operations_usd,
            total_usd=res.budget.total_usd,
            limit_usd=res.budget.limit_usd,
            within_budget=res.budget.within_budget,
        ),
        orbit=OrbitOut(
            delta_v_ms=res.orbit.delta_v_ms,
            transfer_time_days=res.orbit.transfer_time_days,
            apoapsis_km=res.orbit.apoapsis_km,
            feasible=res.orbit.feasible,
            note=res.orbit.note,
        ),
        events=res.events,
        explanation=res.explanation,
    )


def _result_to_json(res: SimulationResult) -> str:
    out = _result_to_out(res)
    return out.model_dump_json()