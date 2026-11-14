"""ORM models."""

from __future__ import annotations

import json
from sqlalchemy import Column, String, Float, Integer, Text
from .db import Base


class ScenarioORM(Base):
    __tablename__ = "scenarios"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    objective = Column(Text, default="")
    destination = Column(String, default="")
    duration_days = Column(Float, default=0.0)
    required_comm_distance_km = Column(Float, default=0.0)
    budget_limit_usd = Column(Float, default=0.0)
    orbit_origin_radius_km = Column(Float, default=0.0)
    orbit_destination_radius_km = Column(Float, default=0.0)
    data_source = Column(String, default="estimated")


class ComponentORM(Base):
    __tablename__ = "components"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, default="")
    mass_kg = Column(Float, default=0.0)
    power_consumption_w = Column(Float, default=0.0)
    power_generation_w = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    comm_range_km = Column(Float, default=0.0)
    comm_data_rate_kbps = Column(Float, default=0.0)
    battery_wh = Column(Float, default=0.0)
    description = Column(Text, default="")
    data_source = Column(String, default="estimated")


class LaunchVehicleORM(Base):
    __tablename__ = "launch_vehicles"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    payload_capacity_kg = Column(Float, default=0.0)
    compatible_destinations = Column(Text, default="[]")  # JSON list
    cost_usd = Column(Float, default=0.0)
    data_source = Column(String, default="estimated")


class MissionORM(Base):
    __tablename__ = "missions"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    scenario_id = Column(String, nullable=False)
    launch_vehicle_id = Column(String, nullable=False)
    component_ids = Column(Text, default="[]")  # JSON list
    structure_mass_kg = Column(Float, default=0.0)
    propellant_mass_kg = Column(Float, default=0.0)
    margin_fraction = Column(Float, default=0.20)
    operations_cost_usd = Column(Float, default=0.0)
    available_delta_v_ms = Column(Float, default=0.0)
    eclipse_hours = Column(Float, default=0.0)


class SimulationORM(Base):
    __tablename__ = "simulations"
    id = Column(String, primary_key=True)
    mission_id = Column(String, nullable=False)
    result_json = Column(Text, default="{}")


def compatible_list(v: str) -> list:
    try:
        return json.loads(v or "[]")
    except Exception:
        return []