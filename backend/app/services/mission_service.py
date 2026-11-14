"""Servicio de orquestación del ciclo de vida de la misión espacial."""

from __future__ import annotations

import uuid
from typing import Any
from app.repositories.data import guardar_mision, obtener_mision
from app.repositories.seed import (
    ACUERDOS_FINANCIACION,
    CANDIDATOS_TRIPULACION,
    COMPONENTES_CATALOGO,
    DESTINOS_CATALOGO,
    NOMBRES_ETAPAS,
    construir_habitaciones_iniciales,
)
from app.schemas.mission import (
    CrearMisionRequest,
    DecisionRequest,
    DecisionResponse,
    EstadoAnimo,
    EstadoMision,
    EventoMision,
    InformeFinal,
    TripulanteEstado,
)
from app.simulation.consequences import (
    aplicar_decision,
    avanzar_etapa_mision,
    resolver_evento_activo,
)
from app.simulation.evaluator import generar_informe_final
from app.simulation.physics import recalcular_subsistemas_mision
from app.simulation.validation import validar_avance_etapa, validar_decision


def obtener_catalogo_completo() -> dict[str, Any]:
    """Devuelve el catálogo completo de componentes, tripulantes, destinos y acuerdos."""
    return {
        "destinos": [d.model_dump() for d in DESTINOS_CATALOGO.values()],
        "acuerdos_financiacion": ACUERDOS_FINANCIACION,
        "componentes": [c.model_dump() for c in COMPONENTES_CATALOGO],
        "candidatos_tripulacion": [t.model_dump() for t in CANDIDATOS_TRIPULACION],
        "etapas": NOMBRES_ETAPAS,
        "masa_lanzamiento_max_kg": 1300.0,
    }


def crear_nueva_mision(req: CrearMisionRequest) -> EstadoMision:
    """Inicializa una misión nueva con el director a bordo y configuración semilla.

    Args:
        req: Parámetros iniciales de creación de la misión.

    Returns:
        EstadoMision: Estado inicial persistido.
    """
    acuerdos = {a["id"]: a for a in ACUERDOS_FINANCIACION}
    acuerdo = acuerdos.get(req.acuerdo_financiacion_id, ACUERDOS_FINANCIACION[1])
    presupuesto_inicial = float(acuerdo["presupuesto_usd"])

    director = TripulanteEstado(
        id="crew_director",
        nombre="Cmdt. Director (Jugador)",
        rol="Director de Misión",
        especialidad=req.especialidad_director,
        experiencia=4,
        salario_usd=0.0,
        estado_animo=EstadoAnimo.SOL,
        es_jugador=True,
        habitacion_actual="cabina_mando",
        biografia_corta="Responsable de la planificación, diseño, ejecución y retorno de la expedición.",
    )

    # Configuración base inicial: motor estándar, energía estándar, antena básica y soporte vital ligero
    componentes_base = [
        "motor_biprop_estandar",
        "energia_solar_estandar",
        "antena_parabolica_x",
        "eclss_reciclaje_estandar",
    ]
    catalogo_map = {c.id: c for c in COMPONENTES_CATALOGO}
    costo_base = sum(catalogo_map[cid].costo_usd for cid in componentes_base)

    estado = EstadoMision(
        id=f"zenit-{uuid.uuid4().hex[:8]}",
        nombre_mision=req.nombre_mision,
        etapa_actual=1,
        nombre_etapa=NOMBRES_ETAPAS[1],
        destino=req.destino,
        acuerdo_financiacion_id=acuerdo["id"],
        presupuesto_inicial_usd=presupuesto_inicial,
        presupuesto_restante_usd=round(presupuesto_inicial - costo_base, 2),
        componentes_instalados=componentes_base,
        tripulacion=[director],
        habitaciones_2d=construir_habitaciones_iniciales(),
        bitacora_decisiones=[
            f"Misión '{req.nombre_mision}' iniciada con destino {req.destino.value} y presupuesto {presupuesto_inicial:,.0f} USD."
        ],
    )
    recalcular_subsistemas_mision(estado)
    return guardar_mision(estado)


def _resumen_estado(estado: EstadoMision) -> dict[str, Any]:
    """Genera un diccionario resumido del estado actual para la respuesta de API."""
    return {
        "etapa_actual": estado.etapa_actual,
        "nombre_etapa": estado.nombre_etapa,
        "estado_juego": estado.estado_juego,
        "destino": estado.destino.value,
        "masa_total_kg": estado.masa_total_kg,
        "masa_lanzamiento_max_kg": estado.masa_lanzamiento_max_kg,
        "delta_v_disponible_ms": estado.delta_v_disponible_ms,
        "delta_v_requerido_total_ms": estado.delta_v_requerido_total_ms,
        "balance_potencia_w": estado.balance_potencia_w,
        "bateria_actual_wh": estado.bateria_actual_wh,
        "presupuesto_restante_usd": estado.presupuesto_restante_usd,
        "datos_generados_gb": estado.datos_generados_gb,
        "datos_transmitidos_gb": estado.datos_transmitidos_gb,
        "puntos_ciencia_generados": estado.puntos_ciencia_generados,
    }


def procesar_decision_mision(
    mission_id: str, req: DecisionRequest
) -> DecisionResponse | None:
    """Valida y aplica una decisión del jugador sobre la misión.

    Args:
        mission_id: ID de la misión.
        req: Petición con la etapa, decisión y parámetros.

    Returns:
        DecisionResponse | None: Respuesta con la tabla de variables afectadas, o None si no existe.
    """
    estado = obtener_mision(mission_id)
    if not estado:
        return None

    veredicto = validar_decision(
        estado=estado,
        stage=req.stage,
        decision=req.decision,
        params=req.params,
    )
    if not veredicto.allowed:
        return DecisionResponse(
            allowed=False,
            status=veredicto.status,
            policy_triggered=veredicto.policy,
            message=veredicto.message,
            warnings=veredicto.warnings,
            affected_variables=[],
            new_state_summary=_resumen_estado(estado),
            mission_state=estado,
        )

    estado, cambios, narrativa = aplicar_decision(
        estado=estado,
        stage=req.stage,
        decision=req.decision,
        params=req.params,
    )
    guardar_mision(estado)
    return DecisionResponse(
        allowed=True,
        status=veredicto.status,
        policy_triggered=veredicto.policy,
        message=narrativa,
        warnings=veredicto.warnings,
        affected_variables=cambios,
        new_state_summary=_resumen_estado(estado),
        mission_state=estado,
    )


def procesar_avance_etapa(mission_id: str) -> DecisionResponse | None:
    """Avanza la misión a la siguiente etapa verificando las políticas de consecuencias."""
    estado = obtener_mision(mission_id)
    if not estado:
        return None

    veredicto = validar_avance_etapa(estado)
    estado, cambios, narrativa = avanzar_etapa_mision(estado)
    guardar_mision(estado)

    return DecisionResponse(
        allowed=veredicto.allowed,
        status=veredicto.status,
        policy_triggered=veredicto.policy,
        message=narrativa if veredicto.status != "fail" else veredicto.message,
        warnings=veredicto.warnings,
        affected_variables=cambios,
        new_state_summary=_resumen_estado(estado),
        mission_state=estado,
    )


def listar_eventos_activos(mission_id: str) -> list[EventoMision] | None:
    """Devuelve los eventos activos de la misión."""
    estado = obtener_mision(mission_id)
    if not estado:
        return None
    return estado.eventos_activos


def resolver_evento_mision(
    mission_id: str,
    event_id: str,
    option_id: str,
) -> DecisionResponse | None:
    """Resuelve un evento activo aplicando su opción elegida."""
    estado = obtener_mision(mission_id)
    if not estado:
        return None

    estado, cambios, narrativa = resolver_evento_activo(
        estado=estado,
        event_id=event_id,
        option_id=option_id,
    )
    guardar_mision(estado)
    return DecisionResponse(
        allowed=True,
        status="allowed",
        message=narrativa,
        affected_variables=cambios,
        new_state_summary=_resumen_estado(estado),
        mission_state=estado,
    )


def obtener_informe_mision(mission_id: str) -> InformeFinal | None:
    """Genera y devuelve el informe final multidimensional de la misión."""
    estado = obtener_mision(mission_id)
    if not estado:
        return None
    return generar_informe_final(estado)
