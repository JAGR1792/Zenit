from app.simulation.mass import compute_mass


def test_mass_within_capacity():
    b = compute_mass([10.0, 20.0], structure_mass_kg=5.0, capacity_kg=100.0)
    assert b.total_kg > 0
    assert b.within_capacity is True


def test_mass_exceeds_capacity():
    b = compute_mass([1000.0], structure_mass_kg=100.0, capacity_kg=100.0)
    assert b.within_capacity is False