"""Power and energy model (watts / watt-hours)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class PowerBreakdown:
    generation_w: float = 0.0
    consumption_w: float = 0.0
    net_w: float = 0.0
    battery_capacity_wh: float = 0.0
    eclipse_hours: float = 0.0
    energy_deficit_wh: float = 0.0

    @property
    def balanced(self) -> bool:
        return self.net_w >= 0 and self.energy_deficit_wh <= 0


def compute_power(
    component_consumption_w: Iterable[float],
    component_generation_w: Iterable[float],
    battery_capacity_wh: float = 0.0,
    eclipse_hours: float = 0.0,
    mission_duration_hours: float = 24.0,
) -> PowerBreakdown:
    """Compare generated vs consumed power and check eclipse energy.

    Energy deficit is computed for the longest eclipse: consumption during
    eclipse minus available battery. Generation is assumed zero in eclipse.
    """
    consumption = float(sum(component_consumption_w))
    generation = float(sum(component_generation_w))
    net = generation - consumption
    eclipse_consumption = consumption * eclipse_hours
    deficit = max(0.0, eclipse_consumption - battery_capacity_wh)
    return PowerBreakdown(
        generation_w=generation,
        consumption_w=consumption,
        net_w=net,
        battery_capacity_wh=battery_capacity_wh,
        eclipse_hours=eclipse_hours,
        energy_deficit_wh=deficit,
    )