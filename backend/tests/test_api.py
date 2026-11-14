from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_scenarios():
    r = client.get("/api/v1/scenarios")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_validate_mission():
    payload = {
        "name": "Test",
        "scenario_id": "scn-leo-obs",
        "launch_vehicle_id": "lv-falcon9",
        "component_ids": ["cmp-structure-small", "cmp-solar-panels", "cmp-battery"],
    }
    r = client.post("/api/v1/missions/validate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "feasible" in data
    assert "score" in data