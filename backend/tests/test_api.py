from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_catalogo():
    r = client.get("/api/v1/catalog")
    assert r.status_code == 200
    data = r.json()
    assert "componentes" in data
    assert "destinos" in data


def test_crear_y_obtener_mision():
    r = client.post(
        "/api/v1/missions",
        json={
            "nombre_mision": "Prueba",
            "destino": "OTB",
            "acuerdo_financiacion_id": "estandar",
            "especialidad_director": "comando",
        },
    )
    assert r.status_code == 201
    mid = r.json()["id"]
    r2 = client.get(f"/api/v1/missions/{mid}")
    assert r2.status_code == 200
    assert r2.json()["destino"] == "OTB"


def test_decision_instalar_componente():
    r = client.post(
        "/api/v1/missions",
        json={
            "nombre_mision": "Prueba2",
            "destino": "OTB",
            "acuerdo_financiacion_id": "estandar",
        },
    )
    mid = r.json()["id"]
    r2 = client.post(
        f"/api/v1/missions/{mid}/decisions",
        json={
            "stage": 3,
            "decision": "instalar_componente",
            "params": {"componente_id": "inst_espectrometro"},
        },
    )
    assert r2.status_code == 200
    assert r2.json()["allowed"] is True
