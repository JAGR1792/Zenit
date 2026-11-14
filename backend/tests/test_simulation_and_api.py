"""Pruebas unitarias y de integración para el motor de simulación y API de Zenit."""

from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.mission import (
    CrearMisionRequest,
    DecisionRequest,
    DestinoId,
    DificultadId,
    EstadoAnimo,
)
from app.services.mission_service import (
    crear_nueva_mision,
    obtener_informe_mision,
    procesar_avance_etapa,
    procesar_decision_mision,
)
from app.simulation.physics import (
    calcular_masa_y_propulsion,
    calcular_rendimiento_tripulacion,
)

client = TestClient(app)


def test_ecuacion_tsiolkovsky_interdependencia_masa_deltav() -> None:
    """Añadir un instrumento pesado incrementa la masa seca y reduce el Delta-v disponible."""
    _, _, masa_base, _, dv_base = calcular_masa_y_propulsion(
        masa_estructura_base_kg=420.0,
        componentes_ids=["motor_biprop_estandar", "energia_solar_estandar"],
        num_tripulantes=2,
    )
    _, _, masa_con_inst, _, dv_con_inst = calcular_masa_y_propulsion(
        masa_estructura_base_kg=420.0,
        componentes_ids=[
            "motor_biprop_estandar",
            "energia_solar_estandar",
            "inst_espectrometro",
        ],
        num_tripulantes=2,
    )
    assert masa_con_inst == masa_base + 50.0
    assert dv_con_inst < dv_base


def test_presupuesto_global_es_limite_duro() -> None:
    """Intentar comprar componentes o contratar personal superando el presupuesto es bloqueado."""
    mision = crear_nueva_mision(
        CrearMisionRequest(
            nombre_mision="Test Presupuesto",
            destino=DestinoId.OTB,
            acuerdo_financiacion_id="austero",
        )
    )
    # Gastamos presupuesto contratando tripulantes y cambiando a componentes caros
    procesar_decision_mision(
        mision.id,
        DecisionRequest(
            stage=3,
            decision="instalar_componente",
            params={"componente_id": "motor_crio_avanzado"},
        ),
    )
    procesar_decision_mision(
        mision.id,
        DecisionRequest(
            stage=3,
            decision="instalar_componente",
            params={"componente_id": "energia_hibrida_rtg"},
        ),
    )
    procesar_decision_mision(
        mision.id,
        DecisionRequest(
            stage=3,
            decision="instalar_componente",
            params={"componente_id": "antena_laser_ka"},
        ),
    )
    resp = procesar_decision_mision(
        mision.id,
        DecisionRequest(
            stage=3, decision="contratar_tripulante", params={"crew_id": "crew_marco"}
        ),
    )
    assert resp is not None
    assert resp.allowed is False
    assert resp.status == "fail"
    assert resp.mission_state.presupuesto_restante_usd >= 0


def test_sobrepeso_permitido_en_diseno_pero_fallo_inmediato_en_lanzamiento() -> None:
    """El juego permite construir una nave que supera masa_lanzamiento_max_kg en Etapa 3, pero falla en Etapa 5."""
    mision = crear_nueva_mision(
        CrearMisionRequest(
            nombre_mision="Nave Pesada",
            destino=DestinoId.LUNA,
            acuerdo_financiacion_id="ambicioso",
        )
    )
    # Instalamos todos los instrumentos científicos y el robot para superar 1.300 kg dentro del presupuesto
    for cid in [
        "inst_espectrometro",
        "inst_radar_criosfera",
        "inst_biocapsula",
        "robot_sonda_eva",
    ]:
        r = procesar_decision_mision(
            mision.id,
            DecisionRequest(
                stage=3, decision="instalar_componente", params={"componente_id": cid}
            ),
        )
        assert r is not None and r.allowed is True

    r_crew = procesar_decision_mision(
        mision.id,
        DecisionRequest(
            stage=3, decision="contratar_tripulante", params={"crew_id": "crew_elena"}
        ),
    )
    assert r_crew is not None and r_crew.allowed is True

    # Verificamos que la masa supera los 1.300 kg y no fue bloqueada en diseño
    estado_diseno = client.get(f"/api/v1/missions/{mision.id}").json()
    assert estado_diseno["masa_total_kg"] > estado_diseno["masa_lanzamiento_max_kg"]

    # Avanzamos hasta Etapa 5 (Lanzamiento) y ejecutamos el lanzamiento -> Fallo inmediato
    for _ in range(4):
        procesar_avance_etapa(mision.id)

    res_lanzamiento = procesar_avance_etapa(mision.id)
    assert res_lanzamiento is not None
    assert res_lanzamiento.mission_state.estado_juego == "fallo_inmediato"

    informe = obtener_informe_mision(mision.id)
    assert informe is not None
    assert informe.final_id == "fallo_total"
    assert informe.monologo_cuarta_pared is not None


def test_tripulacion_tareas_comunes_y_debuff_animo() -> None:
    """Un no-especialista no falla tareas comunes (Opción A), pero el especialista y el ánimo Sol rinden más."""
    mision = crear_nueva_mision(CrearMisionRequest())
    tripulante = mision.tripulacion[0]
    tripulante.especialidad = "geologia"
    tripulante.estado_animo = EstadoAnimo.SOL

    # Tarea común (reparación de ingeniería) hecha por geólogo en Sol
    vel_no_esp, cal_no_esp = calcular_rendimiento_tripulacion(
        [tripulante],
        especialidad_requerida="ingenieria",
        es_tarea_comun=True,
    )
    assert vel_no_esp > 0.0 and cal_no_esp > 0.0

    # Si cambia su estado a LLUVIA, sufre debuff de velocidad y calidad
    tripulante.estado_animo = EstadoAnimo.LLUVIA
    vel_lluvia, cal_lluvia = calcular_rendimiento_tripulacion(
        [tripulante],
        especialidad_requerida="ingenieria",
        es_tarea_comun=True,
    )
    assert vel_lluvia < vel_no_esp
    assert cal_lluvia < cal_no_esp


def test_flujo_completo_mision_api_rest() -> None:
    """Verifica el flujo completo de principio a fin (Etapas 1 a 10) a través de los endpoints REST."""
    # 1. Crear misión
    res_create = client.post(
        "/api/v1/missions",
        json={
            "nombre_mision": "Zenit OTB Explorador",
            "destino": "OTB",
            "acuerdo_financiacion_id": "estandar",
            "especialidad_director": "ingenieria",
        },
    )
    assert res_create.status_code == 201
    mission_id = res_create.json()["id"]

    # 2. Añadir un espectrómetro y contratar a la especialista en geología
    res_inst = client.post(
        f"/api/v1/missions/{mission_id}/decisions",
        json={
            "stage": 3,
            "decision": "instalar_componente",
            "params": {"componente_id": "inst_espectrometro"},
        },
    )
    assert res_inst.status_code == 200
    datos_inst = res_inst.json()
    assert datos_inst["allowed"] is True
    assert len(datos_inst["affected_variables"]) >= 5

    res_crew = client.post(
        f"/api/v1/missions/{mission_id}/decisions",
        json={
            "stage": 3,
            "decision": "contratar_tripulante",
            "params": {"crew_id": "crew_elena"},
        },
    )
    assert res_crew.status_code == 200

    # Avanzar hasta Etapa 7 (Operaciones científicas)
    for _ in range(6):
        r_adv = client.post(f"/api/v1/missions/{mission_id}/advance")
        assert r_adv.status_code == 200

    # Moverse con tecla E al laboratorio y ejecutar ciencia
    client.post(
        f"/api/v1/missions/{mission_id}/decisions",
        json={
            "stage": 7,
            "decision": "mover_habitacion",
            "params": {"habitacion_id": "laboratorio"},
        },
    )
    res_sci = client.post(
        f"/api/v1/missions/{mission_id}/decisions",
        json={"stage": 7, "decision": "operacion_cientifica", "params": {}},
    )
    assert res_sci.json()["mission_state"]["puntos_ciencia_generados"] > 0

    # Avanzar a Etapa 8 y 9 y transmitir datos
    client.post(f"/api/v1/missions/{mission_id}/advance")
    client.post(f"/api/v1/missions/{mission_id}/advance")
    res_comm = client.post(
        f"/api/v1/missions/{mission_id}/decisions",
        json={"stage": 9, "decision": "usar_ventana_comm", "params": {}},
    )
    assert res_comm.json()["mission_state"]["datos_transmitidos_gb"] > 0

    # Avanzar a Etapa 10 (Retorno y Evaluación) y obtener informe final
    client.post(f"/api/v1/missions/{mission_id}/advance")
    res_report = client.get(f"/api/v1/missions/{mission_id}/report")
    assert res_report.status_code == 200
    report = res_report.json()
    assert report["numero_final"] in (1, 2, 3, 4, 5)
    assert len(report["dimensiones"]) == 7


def test_modo_facil_otorga_margen_presupuesto_e_instrumento_inicial() -> None:
    """Verifica que la dificultad fácil otorgue mayor presupuesto, límite de masa y espectrómetro preinstalado."""
    mision_facil = crear_nueva_mision(
        CrearMisionRequest(
            nombre_mision="Zenit Cadete",
            destino=DestinoId.OTB,
            dificultad=DificultadId.FACIL,
            acuerdo_financiacion_id="estandar",
        )
    )
    mision_normal = crear_nueva_mision(
        CrearMisionRequest(
            nombre_mision="Zenit Normal",
            destino=DestinoId.OTB,
            dificultad=DificultadId.NORMAL,
            acuerdo_financiacion_id="estandar",
        )
    )
    assert mision_facil.presupuesto_inicial_usd > mision_normal.presupuesto_inicial_usd
    assert mision_facil.masa_lanzamiento_max_kg > mision_normal.masa_lanzamiento_max_kg
    assert "inst_espectrometro" in mision_facil.componentes_instalados

    # En Etapa 1 (Tierra), intentar recolectar ciencia o transmitir está bloqueado para no gastar recursos antes de despegar
    res_bloqueado_tierra = procesar_decision_mision(
        mision_facil.id,
        DecisionRequest(stage=1, decision="operacion_cientifica", params={}),
    )
    assert res_bloqueado_tierra is not None
    assert res_bloqueado_tierra.allowed is False

    # Avanzamos hasta Etapa 7 (Destino) y verificamos que transmitir con 0 GB no gasta ventanas
    for _ in range(6):
        procesar_avance_etapa(mision_facil.id)

    ventanas_antes = mision_facil.ventanas_comm_restantes
    res_tx = procesar_decision_mision(
        mision_facil.id,
        DecisionRequest(stage=7, decision="usar_ventana_comm", params={}),
    )
    assert res_tx is not None
    assert res_tx.allowed is True
    assert res_tx.mission_state.ventanas_comm_restantes == ventanas_antes

