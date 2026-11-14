"""Modelos físicos e interdependencias entre subsistemas (fidelidad híbrida)."""

from __future__ import annotations

import math
from app.repositories.seed import COMPONENTES_CATALOGO, DESTINOS_CATALOGO
from app.schemas.mission import (
    CategoriaComponente,
    ComponenteCatalogo,
    DestinoId,
    EstadoAnimo,
    EstadoMision,
    TripulanteEstado,
)

G0_MS2: float = 9.80665
MASA_POR_TRIPULANTE_KG: float = 25.0


def obtener_mapa_catalogo() -> dict[str, ComponenteCatalogo]:
    """Devuelve un diccionario indexado por id de todos los componentes del catálogo.

    Returns:
        dict[str, ComponenteCatalogo]: Mapa de componentes disponibles.
    """
    return {comp.id: comp for comp in COMPONENTES_CATALOGO}


def calcular_masa_y_propulsion(
    masa_estructura_base_kg: float,
    componentes_ids: list[str],
    num_tripulantes: int,
    rendimiento_motor: float = 1.0,
) -> tuple[float, float, float, float, float]:
    """Calcula la masa seca, masa de combustible, masa total, Isp y Delta-v (Ecuación de Tsiolkovsky).

    Args:
        masa_estructura_base_kg: Masa del chasis base en kg.
        componentes_ids: Lista de IDs de componentes instalados.
        num_tripulantes: Cantidad total de tripulantes a bordo (1 a 4).
        rendimiento_motor: Factor de integridad del motor (1.0 nominal, <1.0 si hay fallo).

    Returns:
        tuple[float, float, float, float, float]:
            (masa_seca_kg, masa_combustible_kg, masa_total_kg, isp_efectivo_s, delta_v_ms).
    """
    catalogo = obtener_mapa_catalogo()
    masa_componentes_secos = 0.0
    masa_combustible = 0.0
    isp_base = 0.0

    for cid in componentes_ids:
        comp = catalogo.get(cid)
        if not comp:
            continue
        masa_componentes_secos += comp.masa_kg
        if comp.categoria == CategoriaComponente.MOTOR:
            masa_combustible += comp.combustible_kg
            isp_base = max(isp_base, comp.isp_s)

    masa_tripulacion = max(1, num_tripulantes) * MASA_POR_TRIPULANTE_KG
    masa_seca = round(
        masa_estructura_base_kg + masa_componentes_secos + masa_tripulacion, 2
    )
    masa_total = round(masa_seca + masa_combustible, 2)
    isp_efectivo = round(isp_base * max(0.1, rendimiento_motor), 2)

    if isp_efectivo <= 0 or masa_combustible <= 0 or masa_total <= masa_seca:
        return masa_seca, masa_combustible, masa_total, isp_efectivo, 0.0

    delta_v = isp_efectivo * G0_MS2 * math.log(masa_total / masa_seca)
    return masa_seca, masa_combustible, masa_total, isp_efectivo, round(delta_v, 1)


def calcular_balance_energetico(
    componentes_ids: list[str],
    destino: DestinoId,
    rendimiento_energia: float = 1.0,
    consumo_base_avionica_w: float = 110.0,
) -> tuple[float, float, float, float, float]:
    """Calcula el balance eléctrico en Watts y la autonomía de baterías en Wh.

    Args:
        componentes_ids: Lista de IDs de componentes instalados.
        destino: Destino seleccionado (afecta la fracción de eclipse).
        rendimiento_energia: Factor de integridad del sistema eléctrico (1.0 nominal).
        consumo_base_avionica_w: Consumo base de la cabina de mando en W.

    Returns:
        tuple[float, float, float, float, float]:
            (generacion_w, consumo_w, balance_neto_w, capacidad_wh, autonomia_eclipse_h).
    """
    catalogo = obtener_mapa_catalogo()
    params_destino = DESTINOS_CATALOGO[destino]

    generacion_bruta = 0.0
    consumo_total = consumo_base_avionica_w
    capacidad_wh = 600.0  # Batería de reserva interna del chasis

    for cid in componentes_ids:
        comp = catalogo.get(cid)
        if not comp:
            continue
        generacion_bruta += comp.generacion_w
        consumo_total += comp.consumo_w
        capacidad_wh += comp.capacidad_wh

    generacion_efectiva = round(generacion_bruta * max(0.1, rendimiento_energia), 1)
    consumo_total = round(consumo_total, 1)
    balance_neto = round(generacion_efectiva - consumo_total, 1)

    demanda_eclipse = max(50.0, consumo_total * params_destino.fraccion_eclipse)
    autonomia_h = round(capacidad_wh / demanda_eclipse, 1)

    return (
        generacion_efectiva,
        consumo_total,
        balance_neto,
        round(capacidad_wh, 1),
        autonomia_h,
    )


def calcular_soporte_vital_simplificado(
    componentes_ids: list[str],
    num_tripulantes: int,
    rendimiento_eclss: float = 1.0,
) -> tuple[float, float]:
    """Calcula los días de oxígeno y comida disponibles para la dotación actual.

    Args:
        componentes_ids: Componentes instalados.
        num_tripulantes: Número de tripulantes vivos (1 a 4).
        rendimiento_eclss: Factor de integridad del soporte vital.

    Returns:
        tuple[float, float]: (o2_dias_disponibles, comida_dias_disponibles).
    """
    catalogo = obtener_mapa_catalogo()
    dias_persona_o2 = 4.0  # Reserva de emergencia de cabina
    dias_persona_comida = 4.0

    for cid in componentes_ids:
        comp = catalogo.get(cid)
        if not comp:
            continue
        dias_persona_o2 += comp.dias_o2
        dias_persona_comida += comp.dias_comida

    n_crew = max(1, num_tripulantes)
    o2_dias = round((dias_persona_o2 * max(0.2, rendimiento_eclss)) / n_crew, 1)
    comida_dias = round(dias_persona_comida / n_crew, 1)
    return o2_dias, comida_dias


def calcular_rendimiento_tripulacion(
    tripulacion: list[TripulanteEstado],
    especialidad_requerida: str | None = None,
    es_tarea_comun: bool = True,
) -> tuple[float, float]:
    """Calcula determinísticamente la velocidad y calidad de ejecución del equipo.

    Regla acordada (Opción A):
    - La especialidad habilita tareas científicas/técnicas específicas y optimiza tareas comunes.
    - En tareas comunes (como reparar), un no-especialista NUNCA falla por incompetencia,
      únicamente tarda más tiempo y obtiene menor rendimiento/calidad.
    - La experiencia (1-5) modifica la velocidad de ejecución.
    - El estado de ánimo ('sol', 'nube', 'lluvia') aplica un debuff por desconcentración.

    Args:
        tripulacion: Lista de tripulantes en la misión.
        especialidad_requerida: Especialidad afín a la tarea (si aplica).
        es_tarea_comun: Si la tarea puede ser ejecutada por cualquier rol sin bloquearse.

    Returns:
        tuple[float, float]: (multiplicador_velocidad, multiplicador_calidad).
    """
    vivos = [t for t in tripulacion if t.vivo]
    if not vivos:
        return 0.0, 0.0

    factores_animo_vel = {
        EstadoAnimo.SOL: 1.0,
        EstadoAnimo.NUBE: 0.82,
        EstadoAnimo.LLUVIA: 0.62,
    }
    factores_animo_cal = {
        EstadoAnimo.SOL: 1.0,
        EstadoAnimo.NUBE: 0.88,
        EstadoAnimo.LLUVIA: 0.70,
    }

    velocidades: list[float] = []
    calidades: list[float] = []

    for miembro in vivos:
        mod_exp = 0.75 + (miembro.experiencia * 0.10)  # Exp 1 -> 0.85, Exp 5 -> 1.25
        if (
            especialidad_requerida is None
            or miembro.especialidad == especialidad_requerida
        ):
            mod_rol_vel = 1.20 if especialidad_requerida else 1.0
            mod_rol_cal = 1.15 if especialidad_requerida else 1.0
        elif es_tarea_comun:
            # Opción A: Nunca falla, pero es más lento y de menor calidad
            mod_rol_vel = 0.72
            mod_rol_cal = 0.80
        else:
            mod_rol_vel = 0.45
            mod_rol_cal = 0.55

        vel = mod_exp * mod_rol_vel * factores_animo_vel[miembro.estado_animo]
        cal = mod_rol_cal * factores_animo_cal[miembro.estado_animo]
        velocidades.append(vel)
        calidades.append(cal)

    # Bonificación de coordinación si hay entre 2 y 4 tripulantes; penalización si está en solitario
    factor_dotacion = 0.80 if len(vivos) == 1 else min(1.15, 0.90 + 0.08 * len(vivos))

    vel_media = round((sum(velocidades) / len(velocidades)) * factor_dotacion, 2)
    cal_media = round(min(1.25, sum(calidades) / len(calidades)), 2)
    return vel_media, cal_media


def recalcular_subsistemas_mision(estado: EstadoMision) -> EstadoMision:
    """Sincroniza todas las variables interdependientes del estado de la misión.

    Args:
        estado: Estado de la misión a recalcular.

    Returns:
        EstadoMision: Estado actualizado con todas las variables físicas sincronizadas.
    """
    catalogo = obtener_mapa_catalogo()
    params_destino = DESTINOS_CATALOGO[estado.destino]
    num_vivos = max(1, len([t for t in estado.tripulacion if t.vivo]))

    masa_seca, masa_comb, masa_total, isp_ef, dv_total = calcular_masa_y_propulsion(
        masa_estructura_base_kg=estado.masa_estructura_base_kg,
        componentes_ids=estado.componentes_instalados,
        num_tripulantes=num_vivos,
        rendimiento_motor=estado.rendimiento_subsistemas.get("motor", 1.0),
    )
    estado.masa_seca_kg = masa_seca
    estado.masa_combustible_kg = masa_comb
    estado.masa_total_kg = masa_total
    estado.isp_efectivo_s = isp_ef

    if estado.etapa_actual <= 4:
        estado.delta_v_inicial_ms = dv_total
        estado.delta_v_disponible_ms = dv_total

    # Requerimiento orbital según destino y perfil de trayectoria
    factor_trayectoria = 1.18 if estado.perfil_trayectoria == "rapida" else 1.0
    factor_ventana = 1.10 if estado.ventana_lanzamiento == "secundaria" else 1.0
    estado.delta_v_requerido_total_ms = round(
        params_destino.delta_v_total_minimo_ms * factor_trayectoria * factor_ventana, 1
    )
    estado.dias_transito = (
        params_destino.dias_transito_rapido
        if estado.perfil_trayectoria == "rapida"
        else params_destino.dias_transito_estandar
    )
    estado.dias_en_destino = params_destino.dias_operacion_destino

    # Energía
    gen_w, cons_w, bal_w, cap_wh, aut_h = calcular_balance_energetico(
        componentes_ids=estado.componentes_instalados,
        destino=estado.destino,
        rendimiento_energia=estado.rendimiento_subsistemas.get("energia", 1.0),
    )
    estado.generacion_w = gen_w
    estado.consumo_w = cons_w
    estado.balance_potencia_w = bal_w
    estado.bateria_capacidad_wh = cap_wh
    if estado.etapa_actual <= 4:
        estado.bateria_actual_wh = cap_wh
    else:
        estado.bateria_actual_wh = min(estado.bateria_actual_wh, cap_wh)
    estado.autonomia_eclipse_h = aut_h

    # Soporte Vital Simplificado
    if estado.etapa_actual <= 4:
        o2_d, comida_d = calcular_soporte_vital_simplificado(
            componentes_ids=estado.componentes_instalados,
            num_tripulantes=num_vivos,
            rendimiento_eclss=estado.rendimiento_subsistemas.get("soporte_vital", 1.0),
        )
        estado.o2_dias_disponibles = o2_d
        estado.comida_dias_disponibles = comida_d

    # Telecomunicaciones y Robot
    tasa_kbps = 0.0
    ventanas = 0
    prob_enlace = 0.0
    tiene_robot = False
    for cid in estado.componentes_instalados:
        comp = catalogo.get(cid)
        if not comp:
            continue
        if comp.categoria == CategoriaComponente.ANTENA:
            tasa_kbps = max(tasa_kbps, comp.tasa_kbps)
            ventanas = max(ventanas, comp.ventanas_dia)
            # Penalizar probabilidad si la antena no tiene alcance para la Luna
            penalizacion_alcance = (
                0.45 if comp.alcance_km < params_destino.distancia_km else 1.0
            )
            prob_enlace = max(
                prob_enlace, round(comp.probabilidad_enlace * penalizacion_alcance, 2)
            )
        if comp.categoria == CategoriaComponente.ROBOT:
            tiene_robot = True

    rend_antena = estado.rendimiento_subsistemas.get("antena", 1.0)
    estado.tasa_transmision_kbps = round(tasa_kbps * rend_antena, 1)
    estado.ventanas_comm_por_dia = ventanas
    if estado.etapa_actual <= 4:
        estado.ventanas_comm_restantes = ventanas * max(1, estado.dias_en_destino)
    estado.probabilidad_enlace_comm = round(prob_enlace * rend_antena, 2)
    estado.tiene_robot_autonomo = tiene_robot

    # Rendimiento determinista del equipo
    vel_eq, cal_eq = calcular_rendimiento_tripulacion(estado.tripulacion)
    estado.velocidad_tarea_equipo = vel_eq
    estado.calidad_tarea_equipo = cal_eq

    return estado
