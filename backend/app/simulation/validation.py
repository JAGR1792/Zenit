"""Motor de validación de decisiones y clasificación de restricciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from app.repositories.seed import (
    ACUERDOS_FINANCIACION,
    CANDIDATOS_TRIPULACION,
    COMPONENTES_CATALOGO,
    DESTINOS_CATALOGO,
)
from app.schemas.mission import EstadoMision, PoliticaConsecuencia


@dataclass
class ResultadoValidacion:
    """Resultado devuelto por el motor de validación antes de mutar el estado."""

    allowed: bool
    status: Literal["allowed", "warning", "fail"]
    policy: PoliticaConsecuencia = PoliticaConsecuencia.NOMINAL
    message: str = "Decisión válida."
    warnings: list[str] = field(default_factory=list)


def validar_decision(
    estado: EstadoMision,
    stage: int,
    decision: str,
    params: dict[str, Any],
) -> ResultadoValidacion:
    """Valida una decisión del jugador contra los límites duros y reglas de etapa.

    Importante (Regla de Diseño):
    - El presupuesto global ($ USD) y el máximo de 4 tripulantes son límites duros preventivos.
    - Durante el diseño (Etapa 3), NO se bloquean configuraciones pesadas, deficitarias en
      energía ni incompatibles: el jugador lee la ficha técnica y la tabla de variables sin
      que el juego le advierta de qué desastre ocurrirá.
    - Las restricciones físicas críticas (como superar `masa_lanzamiento_max_kg` o carecer de
      motor/delta-v en el lanzamiento) producen fallo inmediato en el momento de ejecutar la
      maniobra física (Etapa 5+).

    Args:
        estado: Estado actual de la misión.
        stage: Etapa sobre la que se toma la decisión.
        decision: Identificador de la acción.
        params: Parámetros asociados a la decisión.

    Returns:
        ResultadoValidacion: Resultado con `allowed`, `status` y `policy`.
    """
    if estado.estado_juego in ("fallo_inmediato", "perdida_mision"):
        return ResultadoValidacion(
            allowed=False,
            status="fail",
            policy=PoliticaConsecuencia.FALLO_INMEDIATO,
            message="La misión ya ha finalizado por un fallo crítico.",
        )

    # Bloquear cambios de diseño o planificación si la nave ya despegó (Etapa 6+)
    if (
        decision
        in (
            "seleccionar_destino",
            "seleccionar_financiacion",
            "negociar_presupuesto",
            "instalar_componente",
            "remover_componente",
            "contratar_tripulante",
            "remover_tripulante",
            "configurar_trayectoria",
        )
        and estado.etapa_actual >= 6
    ):
        return ResultadoValidacion(
            allowed=False,
            status="fail",
            message="La nave ya está en vuelo; no se puede modificar la misión ni el diseño después del lanzamiento.",
        )

    # Etapa 1: Elegir destino
    if decision == "seleccionar_destino":
        destino_id = params.get("destino")
        if destino_id not in ("OTB", "LUNA"):
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Destino no válido para el MVP (debe ser OTB o LUNA).",
            )
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Destino actualizado."
        )

    # Etapa 2: Elegir acuerdo de financiación o negociar presupuesto en novela visual
    if decision == "seleccionar_financiacion":
        acuerdo_id = params.get("acuerdo_id")
        acuerdos = {a["id"]: a for a in ACUERDOS_FINANCIACION}
        if acuerdo_id not in acuerdos:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Acuerdo de financiación desconocido.",
            )
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Presupuesto global fijado."
        )

    if decision == "negociar_presupuesto":
        rondas_previas = sum(
            1
            for entrada in estado.bitacora_decisiones
            if entrada.startswith("Negociación con el Gato Jefe")
        )
        if rondas_previas >= 3:
            return ResultadoValidacion(
                allowed=False,
                status="warning",
                message="El Comité de los 3 Gatos ya cerró las 3 rondas de negociación para esta misión.",
            )
        bono = float(params.get("bono_usd", 0.0))
        if bono < -50000.0 or bono > 90000.0:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Ajuste de negociación fuera de rango permitido.",
            )
        return ResultadoValidacion(
            allowed=True,
            status="allowed",
            message="Argumento de negociación procesado por el comité.",
        )

    # Etapa 3: Instalar componente del catálogo
    if decision == "instalar_componente":
        comp_id = params.get("componente_id")
        catalogo = {c.id: c for c in COMPONENTES_CATALOGO}
        comp = catalogo.get(comp_id)
        if not comp:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message=f"El componente '{comp_id}' no existe en el catálogo.",
            )
        if comp_id in estado.componentes_instalados:
            return ResultadoValidacion(
                allowed=False,
                status="warning",
                message="Este componente ya está instalado en la nave.",
            )
        # Verificar si reemplaza otro del mismo tipo único (motor, energia, antena, soporte_vital)
        reembolso = 0.0
        if comp.categoria.value in ("motor", "energia", "antena", "soporte_vital"):
            for instalado_id in estado.componentes_instalados:
                inst = catalogo.get(instalado_id)
                if inst and inst.categoria == comp.categoria:
                    reembolso += inst.costo_usd

        costo_neto = comp.costo_usd - reembolso
        if estado.presupuesto_restante_usd - costo_neto < 0:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message=(
                    f"Límite duro de presupuesto excedido: faltan "
                    f"{abs(estado.presupuesto_restante_usd - costo_neto):,.0f} USD."
                ),
            )
        # Regla: NO advertimos si supera masa_lanzamiento_max_kg ni si hay déficit energético
        return ResultadoValidacion(
            allowed=True,
            status="allowed",
            policy=PoliticaConsecuencia.NOMINAL,
            message=f"Componente '{comp.nombre}' instalado.",
        )

    # Etapa 3: Desinstalar componente
    if decision == "remover_componente":
        comp_id = params.get("componente_id")
        if comp_id not in estado.componentes_instalados:
            return ResultadoValidacion(
                allowed=False,
                status="warning",
                message="El componente no está instalado.",
            )
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Componente retirado."
        )

    # Etapa 3: Contratar tripulante
    if decision == "contratar_tripulante":
        crew_id = params.get("crew_id")
        candidatos = {c.id: c for c in CANDIDATOS_TRIPULACION}
        cand = candidatos.get(crew_id)
        if not cand:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Candidato no encontrado en el pool.",
            )
        if any(t.id == crew_id for t in estado.tripulacion):
            return ResultadoValidacion(
                allowed=False,
                status="warning",
                message="Este especialista ya forma parte de la tripulación.",
            )
        if len(estado.tripulacion) >= 4:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Capacidad máxima alcanzada: máximo 4 personas en el MVP (incluido el director).",
            )
        if estado.presupuesto_restante_usd - cand.salario_usd < 0:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message="Presupuesto insuficiente para cubrir el salario del especialista.",
            )
        return ResultadoValidacion(
            allowed=True,
            status="allowed",
            message=f"{cand.nombre} incorporado a la tripulación.",
        )

    # Etapa 3: Despedir tripulante
    if decision == "remover_tripulante":
        crew_id = params.get("crew_id")
        miembro = next((t for t in estado.tripulacion if t.id == crew_id), None)
        if not miembro or miembro.es_jugador:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="No se puede retirar al director de la misión.",
            )
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Tripulante relevado."
        )

    # Etapa 4: Planificación orbital
    if decision == "configurar_trayectoria":
        perfil = params.get("perfil_trayectoria", "estandar")
        ventana = params.get("ventana_lanzamiento", "optima")
        if perfil not in ("estandar", "rapida") or ventana not in (
            "optima",
            "secundaria",
        ):
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                message="Parámetros orbitales inválidos.",
            )
        return ResultadoValidacion(
            allowed=True,
            status="allowed",
            message="Plan orbital registrado en la computadora de vuelo.",
        )

    # Bloquear operaciones de vuelo y gasto de recursos mientras la nave sigue en Tierra (Etapas 1 a 5)
    if decision == "tarea_tripulacion" and estado.etapa_actual < 6:
        return ResultadoValidacion(
            allowed=False,
            status="warning",
            message=(
                f"La nave aún está en Tierra ({estado.nombre_etapa}). "
                "Debes completar la planificación y despegar en la Etapa 5 antes de ejecutar tareas en vuelo."
            ),
        )

    if (
        decision in ("operacion_cientifica", "usar_ventana_comm")
        and estado.etapa_actual < 7
    ):
        return ResultadoValidacion(
            allowed=False,
            status="warning",
            message=(
                f"Operación bloqueada en '{estado.nombre_etapa}': la recolección de ciencia y transmisión de datos "
                "solo pueden ejecutarse tras llegar al destino (Etapas 7 a 9)."
            ),
        )

    # Costes imprevistos en Tránsito (Etapa 6) u Órbita (Etapas 7-9)
    if decision in (
        "contingencia_transito",
        "operacion_cientifica",
        "tarea_tripulacion",
        "usar_ventana_comm",
    ):
        costo_usd = float(params.get("costo_usd", 0.0))
        if estado.presupuesto_restante_usd - costo_usd < 0:
            return ResultadoValidacion(
                allowed=False,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message="Presupuesto financiero insuficiente para costear esta operación en tiempo real.",
            )
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Operación autorizada."
        )

    # Movimiento en Vista 2D (Tecla E)
    if decision in ("mover_habitacion", "inspeccionar_habitacion"):
        return ResultadoValidacion(
            allowed=True, status="allowed", message="Desplazamiento en módulo."
        )

    return ResultadoValidacion(
        allowed=True, status="allowed", message="Decisión validada."
    )


def validar_avance_etapa(estado: EstadoMision) -> ResultadoValidacion:
    """Evalúa qué ocurre al avanzar de etapa aplicando las políticas de consecuencias.

    Políticas:
    1. Restricciones físicas críticas (Etapa 5 Lanzamiento: masa > masa_lanzamiento_max_kg
       o sin motor/delta-v de ascenso): FALLO INMEDIATO.
    2. Recursos operativos (energía negativa, escasez de O2/comida): DEGRADACIÓN PROGRESIVA.
    3. Decisiones estratégicas (exceso de datos frente a antena, trayectoria ineficiente):
       PENALIZACIÓN DIFERIDA.

    Args:
        estado: Estado actual de la misión antes de avanzar a `etapa_actual + 1`.

    Returns:
        ResultadoValidacion: Veredicto de avance de etapa.
    """
    params_destino = DESTINOS_CATALOGO[estado.destino]

    # Al pasar de Etapa 4 a Etapa 5 (Lanzamiento) o ejecutar Etapa 5
    if estado.etapa_actual == 5:
        if estado.masa_total_kg > estado.masa_lanzamiento_max_kg:
            exceso = round(estado.masa_total_kg - estado.masa_lanzamiento_max_kg, 1)
            return ResultadoValidacion(
                allowed=True,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message=(
                    f"FALLO FÍSICO INMEDIATO EN LANZAMIENTO: La masa total de la nave ({estado.masa_total_kg} kg) "
                    f"supera la capacidad máxima fija del lanzador ({estado.masa_lanzamiento_max_kg} kg) por {exceso} kg. "
                    "Aborto estructural en la rampa."
                ),
            )
        if estado.delta_v_disponible_ms < params_destino.delta_v_lanzamiento_ms:
            return ResultadoValidacion(
                allowed=True,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message=(
                    f"FALLO FÍSICO INMEDIATO EN INSERCIÓN: Delta-v disponible ({estado.delta_v_disponible_ms} m/s) "
                    f"insuficiente para alcanzar la velocidad orbital inicial ({params_destino.delta_v_lanzamiento_ms} m/s)."
                ),
            )

    # En Tránsito (Etapa 6): verificar delta-v de transferencia e inicio de degradación
    if estado.etapa_actual == 6:
        dv_transito = params_destino.delta_v_transito_insercion_ms * (
            1.18 if estado.perfil_trayectoria == "rapida" else 1.0
        )
        if estado.delta_v_disponible_ms < dv_transito:
            return ResultadoValidacion(
                allowed=True,
                status="fail",
                policy=PoliticaConsecuencia.FALLO_INMEDIATO,
                message=(
                    f"FALLO CRÍTICO EN TRÁNSITO: Combustible agotado durante la inyección hacia {estado.destino.value}. "
                    f"Se requerían {dv_transito:.0f} m/s y solo quedaban {estado.delta_v_disponible_ms:.0f} m/s."
                ),
            )

    # Verificar recursos operativos -> Degradación progresiva como comportamiento predeterminado
    warnings: list[str] = []
    policy = PoliticaConsecuencia.NOMINAL
    if estado.etapa_actual >= 5:
        if estado.balance_potencia_w < 0 or estado.bateria_actual_wh <= 150:
            policy = PoliticaConsecuencia.DEGRADACION_PROGRESIVA
            warnings.append(
                "Déficit energético activo: degradación progresiva de subsistemas."
            )
        if estado.o2_dias_disponibles < 1.5 or estado.comida_dias_disponibles < 1.5:
            policy = PoliticaConsecuencia.DEGRADACION_PROGRESIVA
            warnings.append(
                "Escasez en soporte vital: degradación progresiva de salud y ánimo."
            )

    return ResultadoValidacion(
        allowed=True,
        status="warning" if warnings else "allowed",
        policy=policy,
        message="Transición de etapa procesada.",
        warnings=warnings,
    )
