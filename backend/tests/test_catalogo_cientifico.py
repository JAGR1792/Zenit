"""Pruebas de coherencia científica del catálogo (valores contrastados con NASA).

Las fuentes de cada valor están en `docs/fuentes-nasa.md`.
"""

from __future__ import annotations

import math
import re

from app.repositories.seed import COMPONENTES_CATALOGO, DESTINOS_CATALOGO
from app.schemas.mission import CategoriaComponente, DestinoId

# Constantes NASA NSSDC (Earth Fact Sheet).
RADIO_TIERRA_KM = 6378.137
MU_TIERRA_KM3_S2 = 398600.0

NOMBRES_NO_REALES = ("Hyper", "Methalox", "Z-360", "M-280", "P-780", "DeepLink")


def _por_id(componente_id: str):
    return next(c for c in COMPONENTES_CATALOGO if c.id == componente_id)


def test_catalogo_sin_nombres_ficticios() -> None:
    """Ningún componente conserva los nombres inventados que no corresponden a hardware real."""
    for comp in COMPONENTES_CATALOGO:
        for prohibido in NOMBRES_NO_REALES:
            assert prohibido not in comp.nombre
            assert prohibido not in comp.descripcion_ficha


def test_isp_de_motores_dentro_de_rangos_nasa() -> None:
    """El Isp de cada motor coincide con el rango que reporta NASA para su tecnología."""
    # Hidracina: 200-235 s típico para propulsores de >= 1 N (NASA SST-SoA, cap. 4).
    assert 200.0 <= _por_id("motor_monoprop_basico").isp_s <= 235.0
    # OMS-E de Orión: 315,1 s (NTRS 20240003648).
    assert math.isclose(_por_id("motor_biprop_estandar").isp_s, 315.1, abs_tol=2.0)
    # RL10A-3-3A: 444,4 +/- 2,5 s en vacío (NTRS 20140011176).
    assert math.isclose(_por_id("motor_crio_avanzado").isp_s, 444.4, abs_tol=5.0)


def test_los_tres_motores_estan_ordenados_por_isp() -> None:
    """La progresión del catálogo respeta monopropelente < bipropelente < criogénico."""
    motores = [
        c for c in COMPONENTES_CATALOGO if c.categoria == CategoriaComponente.MOTOR
    ]
    isp = [m.isp_s for m in motores]
    assert isp == sorted(isp)


def test_matriz_con_mmrtg_suma_datos_reales_de_nasa() -> None:
    """Matriz solar GaAs + MMRTG: 110 W y 45 kg del MMRTG (hoja técnica NASA)."""
    solar = _por_id("energia_solar_estandar")
    hibrida = _por_id("energia_hibrida_rtg")
    assert math.isclose(hibrida.generacion_w, solar.generacion_w + 110.0)
    assert math.isclose(hibrida.masa_kg, solar.masa_kg + 45.0)


def test_nombre_de_paneles_coincide_con_su_potencia() -> None:
    """El número del nombre de un panel (p. ej. 'Si-420') es su potencia en W."""
    for cid in ("energia_solar_compacto", "energia_solar_estandar"):
        comp = _por_id(cid)
        coincidencia = re.search(r"-(\d+)", comp.nombre)
        assert (
            coincidencia is not None
        ), f"El nombre '{comp.nombre}' no incluye su potencia"
        assert int(coincidencia.group(1)) == int(comp.generacion_w)


def test_antena_optica_no_se_describe_como_banda_ka() -> None:
    """La banda Ka es radiofrecuencia; la antena óptica debe describirse como láser infrarrojo."""
    optica = _por_id("antena_laser_ka")
    assert "Ka" not in optica.nombre.split()
    assert "láser" in optica.nombre


def test_fraccion_eclipse_otb_no_supera_el_maximo_teorico() -> None:
    """A 400 km la fracción en sombra no puede superar asin(R/r)/pi (≈0,390)."""
    radio_orbita = RADIO_TIERRA_KM + 400.0
    maximo = math.asin(RADIO_TIERRA_KM / radio_orbita) / math.pi
    assert DESTINOS_CATALOGO[DestinoId.OTB].fraccion_eclipse <= maximo


def test_velocidad_orbital_otb_muestra_que_el_ascenso_no_cuesta_1450_ms() -> None:
    """Documenta el pendiente: la velocidad orbital a 400 km (7,67 km/s) supera el delta-v de ascenso del juego."""
    velocidad_orbital_ms = (
        math.sqrt(MU_TIERRA_KM3_S2 / (RADIO_TIERRA_KM + 400.0)) * 1000.0
    )
    assert math.isclose(velocidad_orbital_ms, 7669.0, abs_tol=5.0)
    # Hoy el juego usa 1.450 m/s; ver docs/fuentes-nasa.md §4, punto 1.
    assert (
        DESTINOS_CATALOGO[DestinoId.OTB].delta_v_lanzamiento_ms < velocidad_orbital_ms
    )
