"""Data access helpers (seed + CRUD)."""

from __future__ import annotations

import json
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.db import Base, engine, SessionLocal
from ..models.orm import (
    ScenarioORM, ComponentORM, LaunchVehicleORM, MissionORM, SimulationORM,
)
from .seed import SCENARIOS, COMPONENTS, LAUNCH_VEHICLES


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(ScenarioORM).count() == 0:
            for s in SCENARIOS:
                db.add(ScenarioORM(**s))
        if db.query(ComponentORM).count() == 0:
            for c in COMPONENTS:
                db.add(ComponentORM(**c))
        if db.query(LaunchVehicleORM).count() == 0:
            for lv in LAUNCH_VEHICLES:
                row = dict(lv)
                row["compatible_destinations"] = json.dumps(lv["compatible_destinations"])
                db.add(LaunchVehicleORM(**row))
        db.commit()
    finally:
        db.close()


def get_session() -> Session:
    return SessionLocal()


# ---- Scenarios ----
def list_scenarios(db: Session):
    return db.query(ScenarioORM).all()


def get_scenario(db: Session, sid: str):
    return db.query(ScenarioORM).filter(ScenarioORM.id == sid).first()


# ---- Components ----
def list_components(db: Session):
    return db.query(ComponentORM).all()


def get_components_by_ids(db: Session, ids: List[str]):
    return db.query(ComponentORM).filter(ComponentORM.id.in_(ids)).all()


# ---- Launch vehicles ----
def list_launch_vehicles(db: Session):
    return db.query(LaunchVehicleORM).all()


def get_launch_vehicle(db: Session, lid: str):
    return db.query(LaunchVehicleORM).filter(LaunchVehicleORM.id == lid).first()


# ---- Missions ----
def create_mission(db: Session, payload: dict) -> str:
    mid = str(uuid.uuid4())
    row = MissionORM(id=mid, **{k: (json.dumps(v) if isinstance(v, list) else v)
                                 for k, v in payload.items()})
    # component_ids stored as json
    if "component_ids" in payload:
        row.component_ids = json.dumps(payload["component_ids"])
    db.add(row)
    db.commit()
    return mid


def get_mission(db: Session, mid: str):
    return db.query(MissionORM).filter(MissionORM.id == mid).first()


# ---- Simulations ----
def save_simulation(db: Session, mission_id: str, result_json: str) -> str:
    sid = str(uuid.uuid4())
    db.add(SimulationORM(id=sid, mission_id=mission_id, result_json=result_json))
    db.commit()
    return sid


def get_simulation(db: Session, sid: str):
    return db.query(SimulationORM).filter(SimulationORM.id == sid).first()