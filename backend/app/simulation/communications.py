"""Simplified communications / link-budget model.

Distances are in kilometres (km). The model checks whether the selected
communication subsystem can close a link over the required distance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class CommBreakdown:
    required_distance_km: float = 0.0
    max_range_km: float = 0.0
    link_margin_db: float = 0.0
    data_rate_kbps: float = 0.0

    @property
    def link_closed(self) -> bool:
        return self.max_range_km >= self.required_distance_km and self.link_margin_db >= 0


def compute_communications(
    required_distance_km: float,
    component_max_ranges_km: Iterable[float],
    component_data_rates_kbps: Iterable[float],
    base_margin_db: float = 3.0,
) -> CommBreakdown:
    """Aggregate communication capability from selected components.

    The best (max) range and the sum of data rates are used. A simple
    margin is derived from how much the range exceeds the requirement.
    """
    ranges = list(component_max_ranges_km)
    rates = list(component_data_rates_kbps)
    max_range = max(ranges) if ranges else 0.0
    total_rate = float(sum(rates))
    if required_distance_km > 0:
        margin = 10.0 * (max_range / required_distance_km - 1.0) + base_margin_db
    else:
        margin = base_margin_db
    return CommBreakdown(
        required_distance_km=required_distance_km,
        max_range_km=max_range,
        link_margin_db=margin,
        data_rate_kbps=total_rate,
    )