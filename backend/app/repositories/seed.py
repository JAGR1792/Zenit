"""Seed data for the initial catalog.

All physical/economic values are marked with a data_source: 'real',
'estimated' or 'fictional'. None of these come from a NASA API.
"""

from __future__ import annotations


SCENARIOS = [
    {
        "id": "scn-leo-obs",
        "name": "LEO Earth Observation",
        "objective": "Image Earth surface for climate monitoring",
        "destination": "Low Earth Orbit",
        "duration_days": 30.0,
        "required_comm_distance_km": 2000.0,
        "budget_limit_usd": 5_000_000.0,
        "orbit_origin_radius_km": 6671.0,  # Earth radius + 300 km
        "orbit_destination_radius_km": 6671.0,
        "data_source": "estimated",
    },
    {
        "id": "scn-lunar-orbit",
        "name": "Lunar Orbit Survey",
        "objective": "Map the lunar surface from orbit",
        "destination": "Moon",
        "duration_days": 90.0,
        "required_comm_distance_km": 384400.0,
        "budget_limit_usd": 250_000_000.0,
        "orbit_origin_radius_km": 1.496e8,  # 1 AU
        "orbit_destination_radius_km": 3.844e5,
        "data_source": "estimated",
    },
    {
        "id": "scn-mars-flyby",
        "name": "Mars Flyby",
        "objective": "Collect data during a Mars flyby",
        "destination": "Mars",
        "duration_days": 300.0,
        "required_comm_distance_km": 2.25e8,
        "budget_limit_usd": 800_000_000.0,
        "orbit_origin_radius_km": 1.496e8,
        "orbit_destination_radius_km": 2.279e8,
        "data_source": "estimated",
    },
]


COMPONENTS = [
    {"id": "cmp-structure-small", "name": "Small satellite bus", "category": "structure",
     "mass_kg": 120.0, "power_consumption_w": 10.0, "power_generation_w": 0.0,
     "cost_usd": 200000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Compact bus for small sats", "data_source": "estimated"},
    {"id": "cmp-solar-panels", "name": "Solar panel array", "category": "power",
     "mass_kg": 25.0, "power_consumption_w": 0.0, "power_generation_w": 500.0,
     "cost_usd": 80000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Deployable panels", "data_source": "estimated"},
    {"id": "cmp-battery", "name": "Li-ion battery pack", "category": "power",
     "mass_kg": 40.0, "power_consumption_w": 0.0, "power_generation_w": 0.0,
     "cost_usd": 60000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 2000.0, "description": "Energy storage", "data_source": "estimated"},
    {"id": "cmp-propulsion", "name": "Ion thruster", "category": "propulsion",
     "mass_kg": 60.0, "power_consumption_w": 1500.0, "power_generation_w": 0.0,
     "cost_usd": 300000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Electric propulsion", "data_source": "estimated"},
    {"id": "cmp-comm-uhf", "name": "UHF transceiver", "category": "communications",
     "mass_kg": 8.0, "power_consumption_w": 30.0, "power_generation_w": 0.0,
     "cost_usd": 50000.0, "comm_range_km": 2000.0, "comm_data_rate_kbps": 9.6,
     "battery_wh": 0.0, "description": "Short range", "data_source": "estimated"},
    {"id": "cmp-comm-dsn", "name": "Deep Space Network transponder", "category": "communications",
     "mass_kg": 15.0, "power_consumption_w": 50.0, "power_generation_w": 0.0,
     "cost_usd": 500000.0, "comm_range_km": 5.0e8, "comm_data_rate_kbps": 1000.0,
     "battery_wh": 0.0, "description": "Deep space comm", "data_source": "estimated"},
    {"id": "cmp-payload-cam", "name": "Multispectral camera", "category": "payload",
     "mass_kg": 30.0, "power_consumption_w": 80.0, "power_generation_w": 0.0,
     "cost_usd": 250000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Imaging payload", "data_source": "estimated"},
    {"id": "cmp-thermal", "name": "Thermal control system", "category": "thermal",
     "mass_kg": 20.0, "power_consumption_w": 40.0, "power_generation_w": 0.0,
     "cost_usd": 90000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Heaters and radiators", "data_source": "estimated"},
    {"id": "cmp-avionics", "name": "Flight computer", "category": "avionics",
     "mass_kg": 12.0, "power_consumption_w": 25.0, "power_generation_w": 0.0,
     "cost_usd": 150000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Onboard computer", "data_source": "estimated"},
    {"id": "cmp-star-tracker", "name": "Star tracker", "category": "navigation",
     "mass_kg": 5.0, "power_consumption_w": 15.0, "power_generation_w": 0.0,
     "cost_usd": 120000.0, "comm_range_km": 0.0, "comm_data_rate_kbps": 0.0,
     "battery_wh": 0.0, "description": "Attitude determination", "data_source": "estimated"},
]


LAUNCH_VEHICLES = [
    {"id": "lv-falcon9", "name": "Falcon 9", "payload_capacity_kg": 22800.0,
     "compatible_destinations": ["Low Earth Orbit", "Moon", "Mars"],
     "cost_usd": 67000000.0, "data_source": "estimated"},
    {"id": "lv-electron", "name": "Electron", "payload_capacity_kg": 300.0,
     "compatible_destinations": ["Low Earth Orbit"],
     "cost_usd": 7500000.0, "data_source": "estimated"},
    {"id": "lv-sls", "name": "SLS Block 1", "payload_capacity_kg": 95000.0,
     "compatible_destinations": ["Low Earth Orbit", "Moon", "Mars"],
     "cost_usd": 2000000000.0, "data_source": "estimated"},
]