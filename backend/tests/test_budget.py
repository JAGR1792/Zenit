from app.simulation.budget import compute_budget


def test_budget_within():
    b = compute_budget([100.0, 200.0], launch_vehicle_cost_usd=1000.0, budget_limit_usd=2000.0)
    assert b.within_budget is True


def test_budget_exceeds():
    b = compute_budget([10000.0], launch_vehicle_cost_usd=1000.0, budget_limit_usd=5000.0)
    assert b.within_budget is False