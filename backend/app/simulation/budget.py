"""Budget / cost model (USD)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class BudgetBreakdown:
    components_usd: float = 0.0
    launch_vehicle_usd: float = 0.0
    operations_usd: float = 0.0
    total_usd: float = 0.0
    limit_usd: float = 0.0

    @property
    def within_budget(self) -> bool:
        return self.total_usd <= self.limit_usd


def compute_budget(
    component_costs_usd: Iterable[float],
    launch_vehicle_cost_usd: float = 0.0,
    operations_cost_usd: float = 0.0,
    budget_limit_usd: float = 0.0,
) -> BudgetBreakdown:
    components = float(sum(component_costs_usd))
    total = components + launch_vehicle_cost_usd + operations_cost_usd
    return BudgetBreakdown(
        components_usd=components,
        launch_vehicle_usd=launch_vehicle_cost_usd,
        operations_usd=operations_cost_usd,
        total_usd=total,
        limit_usd=budget_limit_usd,
    )