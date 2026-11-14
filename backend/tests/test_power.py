from app.simulation.power import compute_power


def test_power_balanced():
    p = compute_power([100.0], [200.0], battery_capacity_wh=500.0, eclipse_hours=1.0)
    assert p.balanced is True


def test_power_deficit():
    p = compute_power([1000.0], [100.0], battery_capacity_wh=10.0, eclipse_hours=2.0)
    assert p.balanced is False
    assert p.energy_deficit_wh > 0