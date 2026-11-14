"""Simplified orbit / trajectory model.

Uses a very rough two-body / Hohmann-style approximation. Values are
educational estimates, not high-fidelity astrodynamics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class OrbitBreakdown:
    delta_v_ms: float = 0.0
    transfer_time_days: float = 0.0
    apoapsis_km: float = 0.0
    feasible: bool = True
    note: str = ""


# Gravitational parameters (km^3/s^2) and radii (km) - educational constants.
MU_EARTH = 398600.0
R_EARTH = 6371.0
MU_SUN = 1.32712440018e11


def hohmann_delta_v(r1_km: float, r2_km: float, mu: float = MU_SUN) -> float:
    """Delta-v for a Hohmann transfer between two circular orbits (m/s)."""
    r1, r2 = float(r1_km), float(r2_km)
    if r1 <= 0 or r2 <= 0:
        return 0.0
    v1 = math.sqrt(mu / r1)
    v_transfer_peri = math.sqrt(mu * (2.0 / r1 - 2.0 / (r1 + r2)))
    v_transfer_apo = math.sqrt(mu * (2.0 / r2 - 2.0 / (r1 + r2)))
    v2 = math.sqrt(mu / r2)
    dv = abs(v_transfer_peri - v1) + abs(v2 - v_transfer_apo)
    return dv * 1000.0  # km/s -> m/s


def transfer_time_days(r1_km: float, r2_km: float, mu: float = MU_SUN) -> float:
    a = (r1_km + r2_km) / 2.0
    period_s = 2 * math.pi * math.sqrt(a ** 3 / mu)
    return period_s / 2.0 / 86400.0


def compute_orbit(
    origin_radius_km: float,
    destination_radius_km: float,
    available_delta_v_ms: float = 0.0,
    mu: float = MU_SUN,
) -> OrbitBreakdown:
    dv = hohmann_delta_v(origin_radius_km, destination_radius_km, mu)
    t = transfer_time_days(origin_radius_km, destination_radius_km, mu)
    feasible = available_delta_v_ms >= dv if available_delta_v_ms > 0 else True
    note = "Hohmann transfer estimate (educational)."
    return OrbitBreakdown(
        delta_v_ms=dv,
        transfer_time_days=t,
        apoapsis_km=max(origin_radius_km, destination_radius_km),
        feasible=feasible,
        note=note,
    )