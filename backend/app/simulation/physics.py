"""Modelos físicos e interdependencias entre subsistemas (fidelidad híbrida)."""

from __future__ import annotations

import math
from app.repositories.seed import COMPONENTES_CATALOGO, DESTINOS_CATALOGO
from app.schemas.mission import (
    CategoriaComponente,
    ComponenteCatalogo,
    DestinoId,
    DificultadId,
    EstadoAnimo,
    EstadoMision,
    ParametrosDestino,
    TripulanteEstado,
)

# Gravedad estándar (NASA NSSDC, Earth Fact Sheet: 9,80665 m/s², valor exacto CODATA 2018).
G0_MS2: float = 9.80665

# Decisión de diseño: los tripulantes son perritos ligeramente antropomórficos (~25 kg).
# NASA usa 82 kg para astronautas humanos (Logistics Beyond LEO, ASCEND 2023).
MASA_POR_TRIPULANTE_KG: float = 25.0


# Duración supuesta de una ventana de comunicación (valor de juego; ver docs/fuentes-nasa.md §3).
# Un paso de la Red de Espacio Profundo dura varias horas; 2 h es una abstracción conservadora.
DURACION_VENTANA_COMM_H: float = 2.0

# Potencia que NO depende del Sol y sigue disponible durante un eclipse.
# MMRTG: 110 W eléctricos al inicio de vida (NASA, hoja técnica del MMRTG).
GENERACION_NO_SOLAR_W: dict[str, float] = {"energia_hibrida_rtg": 110.0}

# Factores de juego sobre el delta-v de inserción (no provienen de una fuente NASA).
FACTOR_TRAYECTORIA_RAPIDA: float = 1.18
FACTOR_VENTANA_SECUNDARIA: float = 1.10


def calcular_delta_v_transito_ms(
    params_destino: ParametrosDestino, perfil_trayectoria: str, ventana_lanzamiento: str
) -> float:
    """Delta-v que la nave gasta en tránsito/inserción orbital (el lanzador pone el resto).

    Args:
        params_destino: Parámetros del destino.
        perfil_trayectoria: "estandar" o "rapida" (la rápida llega con más velocidad y exige más frenado).
        ventana_lanzamiento: "optima" o "secundaria".

    Returns:
        float: Delta-v de tránsito/inserción en m/s.
    """
    factor = FACTOR_TRAYECTORIA_RAPIDA if perfil_trayectoria == "rapida" else 1.0
    if ventana_lanzamiento == "secundaria":
        factor *= FACTOR_VENTANA_SECUNDARIA
    return round(params_destino.delta_v_transito_insercion_ms * factor, 1)


def calcular_delta_v_requerido_total_ms(
    params_destino: ParametrosDestino, perfil_trayectoria: str, ventana_lanzamiento: str
) -> float:
    """Delta-v total que la nave necesita: lanzamiento propio + tránsito/inserción + retorno."""
    return round(
        params_destino.delta_v_lanzamiento_ms
        + calcular_delta_v_transito_ms(
            params_destino, perfil_trayectoria, ventana_lanzamiento
        )
        + params_destino.delta_v_retorno_ms,
        1,
    )


def calcular_gb_por_ventana(
    tasa_kbps: float,
    probabilidad_enlace: float,
    duracion_h: float = DURACION_VENTANA_COMM_H,
) -> float:
    """Convierte la tasa del enlace en gigabytes (decimales) transmitidos en una ventana.

    GB = kbps × 1000 [bit/kbit] × (horas × 3600) [s] ÷ 8 [bit/byte] ÷ 10⁹ [byte/GB].
    La probabilidad de enlace se aplica como valor esperado.

    Args:
        tasa_kbps: Tasa del enlace en kilobits por segundo.
        probabilidad_enlace: Disponibilidad esperada del enlace (0 a 1).
        duracion_h: Duración de la ventana en horas.

    Returns:
        float: GB esperados por ventana (0 si no hay antena).
    """
    if tasa_kbps <= 0 or duracion_h <= 0:
        return 0.0
    bits = tasa_kbps * 1000.0 * duracion_h * 3600.0
    return round(bits / 8.0 / 1e9 * max(0.0, probabilidad_enlace), 2)


def calcular_potencia_eclipse_w(
    componentes_ids: list[str],
    consumo_total_w: float,
    rendimiento_energia: float = 1.0,
) -> float:
    """Potencia neta que debe suministrar la batería cuando los paneles no generan.

    Durante un eclipse la carga completa recae en la batería (menos lo que aporte una fuente
    no solar como el MMRTG). No se escala por la fracción de eclipse: esa fracción dice cuánto
    dura la sombra en cada órbita, no cuánta potencia se demanda mientras dura.

    Args:
        componentes_ids: Componentes instalados.
        consumo_total_w: Consumo eléctrico total de la nave en W.
        rendimiento_energia: Factor de integridad del sistema eléctrico.

    Returns:
        float: Potencia neta en W (nunca negativa).
    """
    no_solar = sum(GENERACION_NO_SOLAR_W.get(cid, 0.0) for cid in componentes_ids)
    return max(0.0, consumo_total_w - no_solar * max(0.1, rendimiento_energia))


def calcular_autonomia_eclipse_h(
    capacidad_wh: float, potencia_eclipse_w: float
) -> float:
    """Horas que la batería sostiene la potencia neta de un eclipse continuo (tope 999,9 h)."""
    return min(999.9, round(capacidad_wh / max(potencia_eclipse_w, 1.0), 1))


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
    """Calcula el balance eléctrico en W (con Sol) y la autonomía de la batería en un eclipse (h).

    Args:
        componentes_ids: Lista de IDs de componentes instalados.
        destino: Destino seleccionado (se conserva por compatibilidad: la autonomía en eclipse
            depende de la potencia neta y la batería, no de la fracción de eclipse).
        rendimiento_energia: Factor de integridad del sistema eléctrico (1.0 nominal).
        consumo_base_avionica_w: Consumo base de la cabina de mando en W.

    Returns:
        tuple[float, float, float, float, float]:
            (generacion_w, consumo_w, balance_neto_w, capacidad_wh, autonomia_eclipse_h).
    """
    catalogo = obtener_mapa_catalogo()

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

    potencia_eclipse = calcular_potencia_eclipse_w(
        componentes_ids, consumo_total, rendimiento_energia
    )
    autonomia_h = calcular_autonomia_eclipse_h(capacidad_wh, potencia_eclipse)

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

    # Delta-v propio de la nave: el lanzamiento (ascenso) lo aporta el lanzador externo.
    estado.delta_v_requerido_total_ms = calcular_delta_v_requerido_total_ms(
        params_destino, estado.perfil_trayectoria, estado.ventana_lanzamiento
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
    if estado.dificultad == DificultadId.FACIL:
        cap_wh = round(cap_wh + 800.0, 1)
        gen_w = round(gen_w + 80.0, 1)
        bal_w = round(gen_w - cons_w, 1)
        aut_h = calcular_autonomia_eclipse_h(
            cap_wh,
            calcular_potencia_eclipse_w(
                estado.componentes_instalados,
                cons_w,
                estado.rendimiento_subsistemas.get("energia", 1.0),
            ),
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
        bonus_vital = 6.0 if estado.dificultad == DificultadId.FACIL else 0.0
        estado.o2_dias_disponibles = round(o2_d + bonus_vital, 1)
        estado.comida_dias_disponibles = round(comida_d + bonus_vital, 1)

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
        bonus_ventanas = 3 if estado.dificultad == DificultadId.FACIL else 0
        estado.ventanas_comm_restantes = (
            ventanas * max(1, estado.dias_en_destino) + bonus_ventanas
        )
    estado.probabilidad_enlace_comm = round(
        min(
            0.99,
            prob_enlace * rend_antena
            + (0.08 if estado.dificultad == DificultadId.FACIL else 0.0),
        ),
        2,
    )
    estado.tiene_robot_autonomo = tiene_robot

    # Rendimiento determinista del equipo
    vel_eq, cal_eq = calcular_rendimiento_tripulacion(estado.tripulacion)
    estado.velocidad_tarea_equipo = vel_eq
    estado.calidad_tarea_equipo = cal_eq

    return estado
