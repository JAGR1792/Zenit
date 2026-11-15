"""Pruebas del modelo físico corregido: lanzamiento externo, datos, eclipses y tránsito.

No requieren FastAPI ni base de datos: ejercitan el motor de simulación directamente.
Aproximaciones y fuentes: `docs/fuentes-nasa.md`.
"""

from __future__ import annotations

import math
import random

from app.repositories.seed import (
    CANDIDATOS_TRIPULACION,
    DESTINOS_CATALOGO,
    NOMBRES_ETAPAS,
    construir_habitaciones_iniciales,
)
from app.schemas.mission import (
    DestinoId,
    DificultadId,
    EstadoAnimo,
    EstadoMision,
    TripulanteEstado,
)
from app.simulation.consequences import aplicar_decision, avanzar_etapa_mision
from app.simulation.physics import (
    calcular_autonomia_eclipse_h,
    calcular_balance_energetico,
    calcular_delta_v_requerido_total_ms,
    calcular_delta_v_transito_ms,
    calcular_gb_por_ventana,
    calcular_potencia_eclipse_w,
    recalcular_subsistemas_mision,
)

BASE = [
    "motor_biprop_estandar",
    "energia_solar_estandar",
    "antena_parabolica_x",
    "eclss_reciclaje_estandar",
    "inst_espectrometro",
]


def _mision(
    destino: DestinoId, componentes: list[str], extra: tuple[str, ...] = ()
) -> EstadoMision:
    director = TripulanteEstado(
        id="crew_director",
        nombre="Director",
        rol="Director de Misión",
        especialidad="ingenieria",
        experiencia=4,
        salario_usd=0.0,
        estado_animo=EstadoAnimo.SOL,
        es_jugador=True,
        habitacion_actual="cabina_mando",
        biografia_corta="Prueba.",
    )
    equipo = [director] + [
        c.model_copy(deep=True) for c in CANDIDATOS_TRIPULACION if c.id in extra
    ]
    estado = EstadoMision(
        id="prueba",
        nombre_mision="Prueba",
        etapa_actual=1,
        nombre_etapa=NOMBRES_ETAPAS[1],
        dificultad=DificultadId.NORMAL,
        destino=destino,
        acuerdo_financiacion_id="estandar",
        presupuesto_inicial_usd=500000.0,
        presupuesto_restante_usd=500000.0,
        masa_lanzamiento_max_kg=1300.0,
        componentes_instalados=list(componentes),
        tripulacion=equipo,
        habitaciones_2d=construir_habitaciones_iniciales(),
    )
    recalcular_subsistemas_mision(estado)
    return estado


def _llevar_a_etapa(estado: EstadoMision, etapa: int) -> None:
    rng = random.Random(7)
    while estado.etapa_actual < etapa and estado.estado_juego not in (
        "fallo_inmediato",
        "perdida_mision",
    ):
        avanzar_etapa_mision(estado, rng=rng)


def test_lanzamiento_no_descuenta_delta_v_de_la_nave() -> None:
    """El lanzador externo aporta el ascenso: la nave sale del lanzamiento con todo su delta-v."""
    estado = _mision(DestinoId.LUNA, BASE, ("crew_elena",))
    inicial = estado.delta_v_disponible_ms
    _llevar_a_etapa(estado, 5)
    avanzar_etapa_mision(estado)  # ejecuta el lanzamiento (Etapa 5)
    assert estado.estado_juego != "fallo_inmediato"
    assert estado.delta_v_disponible_ms == inicial


def test_sobrepeso_sigue_causando_fallo_en_lanzamiento() -> None:
    """El límite de masa del lanzador se mantiene como fallo inmediato."""
    estado = _mision(DestinoId.LUNA, BASE, ("crew_elena",))
    estado.masa_lanzamiento_max_kg = estado.masa_total_kg - 1.0
    _llevar_a_etapa(estado, 5)
    avanzar_etapa_mision(estado)
    assert estado.estado_juego == "fallo_inmediato"
    assert estado.causa_fallo is not None
    assert "masa" in estado.causa_fallo.lower()


def test_transito_lunar_descuenta_solo_la_insercion_orbital() -> None:
    """En Etapa 6 la nave gasta la inserción lunar (≈955 m/s), no el presupuesto total."""
    estado = _mision(DestinoId.LUNA, BASE, ("crew_elena",))
    inicial = estado.delta_v_disponible_ms
    _llevar_a_etapa(estado, 7)
    assert math.isclose(estado.delta_v_disponible_ms, inicial - 955.0, abs_tol=0.1)


def test_la_ventana_secundaria_y_la_trayectoria_rapida_son_coherentes_con_el_requerido() -> (
    None
):
    """El delta-v requerido total es exactamente lo que la nave termina gastando."""
    luna = DESTINOS_CATALOGO[DestinoId.LUNA]
    transito = calcular_delta_v_transito_ms(luna, "rapida", "secundaria")
    total = calcular_delta_v_requerido_total_ms(luna, "rapida", "secundaria")
    assert math.isclose(total, transito + luna.delta_v_retorno_ms, abs_tol=0.1)
    assert transito > luna.delta_v_transito_insercion_ms


def test_conversion_de_datos_kbps_a_gb() -> None:
    """2 Mbps durante 1 h son 0,9 GB; 4,5 Mbps durante 1 h son 2,025 GB (decimales)."""
    assert math.isclose(calcular_gb_por_ventana(2000.0, 1.0, 1.0), 0.9, abs_tol=0.005)
    assert math.isclose(calcular_gb_por_ventana(4500.0, 1.0, 1.0), 2.03, abs_tol=0.01)
    # La probabilidad de enlace actúa como valor esperado.
    assert math.isclose(calcular_gb_por_ventana(2000.0, 0.5, 1.0), 0.45, abs_tol=0.005)


def test_sin_antena_no_se_transmite_ni_hay_minimo_artificial() -> None:
    """Sin antena la capacidad es 0 GB (antes un mínimo de 2,5 GB permitía transmitir igual)."""
    assert calcular_gb_por_ventana(0.0, 0.9) == 0.0
    sin_antena = [c for c in BASE if not c.startswith("antena")]
    estado = _mision(DestinoId.LUNA, sin_antena, ("crew_elena",))
    _llevar_a_etapa(estado, 7)
    aplicar_decision(estado, 7, "operacion_cientifica", {})
    ventanas = estado.ventanas_comm_restantes
    aplicar_decision(estado, 7, "usar_ventana_comm", {})
    assert estado.datos_transmitidos_gb == 0.0
    assert estado.ventanas_comm_restantes == ventanas


def test_autonomia_en_eclipse_usa_la_potencia_completa() -> None:
    """Con 400 W de consumo y 2.000 Wh, la batería dura 5 h de eclipse (no se escala por la fracción)."""
    potencia = calcular_potencia_eclipse_w(["energia_solar_estandar"], 400.0)
    assert potencia == 400.0
    assert calcular_autonomia_eclipse_h(2000.0, potencia) == 5.0


def test_el_mmrtg_reduce_la_potencia_que_debe_cubrir_la_bateria() -> None:
    """El MMRTG (110 W) sigue generando en eclipse; los paneles no."""
    solar = calcular_potencia_eclipse_w(["energia_solar_estandar"], 400.0)
    hibrida = calcular_potencia_eclipse_w(["energia_hibrida_rtg"], 400.0)
    assert math.isclose(solar - hibrida, 110.0)


def test_balance_energetico_devuelve_autonomia_coherente() -> None:
    """La autonomía devuelta equivale a capacidad ÷ consumo total para una nave solo solar."""
    gen, cons, _, cap, autonomia = calcular_balance_energetico(BASE, DestinoId.LUNA)
    assert gen > 0
    assert math.isclose(autonomia, round(cap / cons, 1), abs_tol=0.1)
