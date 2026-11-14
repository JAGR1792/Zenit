"""Mass budget model for a space mission.

All masses are in kilograms (kg). The model is deliberately simple and
independent of FastAPI / the database so it can be unit-tested directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class MassBreakdown:
    structure_kg: float = 0.0
    components_kg: float = 0.0
    propellant_kg: float = 0.0
    margin_kg: float = 0.0
    total_kg: float = 0.0
    capacity_kg: float = 0.0

    @property
    def margin_percent(self) -> float:
        if self.total_kg <= 0:
            return 0.0
        return (self.margin_kg / self.total_kg) * 100.0

    @property
    def within_capacity(self) -> bool:
        return self.total_kg <= self.capacity_kg


def compute_mass(
    component_masses: Iterable[float],
    structure_mass_kg: float = 0.0,
    propellant_mass_kg: float = 0.0,
    margin_fraction: float = 0.20,
    capacity_kg: float = 0.0,
) -> MassBreakdown:
    """Compute the total spacecraft mass and compare it to a launch capacity.

    ``margin_fraction`` is applied on top of (structure + components +
    propellant) to account for growth, integration and unknowns.
    """
    components = float(sum(component_masses))
    base = structure_mass_kg + components + propellant_mass_kg
    margin = base * margin_fraction
    total = base + margin
    return MassBreakdown(
        structure_kg=structure_mass_kg,
        components_kg=components,
        propellant_kg=propellant_mass_kg,
        margin_kg=margin,
        total_kg=total,
        capacity_kg=capacity_kg,
    )