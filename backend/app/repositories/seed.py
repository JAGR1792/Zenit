"""Catálogo semilla de componentes, destinos, financiación y perfiles de tripulación."""

from __future__ import annotations

from typing import Any
from app.schemas.mission import (
    CategoriaComponente,
    ComponenteCatalogo,
    DestinoId,
    EstadoAnimo,
    EstadoHabitacion2D,
    ParametrosDestino,
    TripulanteEstado,
)

NOMBRES_ETAPAS: dict[int, str] = {
    1: "1. Definición de la misión",
    2: "2. Negociación y financiación",
    3: "3. Diseño de la nave y selección de personal",
    4: "4. Planificación orbital",
    5: "5. Lanzamiento",
    6: "6. Tránsito",
    7: "7. Operaciones científicas",
    8: "8. Operaciones de tripulación",
    9: "9. Comunicaciones",
    10: "10. Retorno y evaluación",
}

DESTINOS_CATALOGO: dict[DestinoId, ParametrosDestino] = {
    # Presupuesto de delta-v de la NAVE (no del lanzador): el lanzador externo, de capacidad fija,
    # entrega la nave en OTB. Valores en docs/fuentes-nasa.md §4.
    DestinoId.OTB: ParametrosDestino(
        id=DestinoId.OTB,
        nombre="Órbita Terrestre Baja (OTB - 400 km)",
        distancia_km=400.0,
        # El ascenso desde la superficie lo paga el lanzador externo, no la nave.
        delta_v_lanzamiento_ms=0.0,
        # Valor de juego: ajuste de fase/altitud tras la separación del lanzador.
        delta_v_transito_insercion_ms=100.0,
        # Cálculo propio (dos cuerpos): desorbitar de 400 km a un perigeo de 50 km ≈ 102 m/s.
        delta_v_retorno_ms=102.0,
        delta_v_total_minimo_ms=202.0,
        dias_transito_estandar=1,
        dias_transito_rapido=1,
        dias_operacion_destino=4,
        fraccion_eclipse=0.38,
        entorno_riesgo="Ciclado térmico orbital rápido y micro-escombros en órbita baja.",
        descripcion=(
            "Misión de observación atmosférica y microgravedad en órbita terrestre baja. "
            "El lanzador externo entrega la nave en OTB, por lo que la exigencia de delta-v de la nave es mínima; "
            "el enlace es de corta distancia y hay eclipses frecuentes cada 90 minutos."
        ),
    ),
    # Misión ORBITAL lunar (sin descenso). La inyección translunar (TLI) la realiza la etapa superior
    # del lanzador externo; la nave paga la inserción en órbita lunar (LOI) y el retorno (TEI).
    # LOI = LOI-1 (913,5 m/s) + LOI-2 (41,1 m/s) y TEI = 1.072,6 m/s del Apolo 8 (NASA, post-launch report).
    DestinoId.LUNA: ParametrosDestino(
        id=DestinoId.LUNA,
        nombre="Órbita Lunar Polar (observación del Cráter Shackleton - 384.400 km)",
        distancia_km=384400.0,
        delta_v_lanzamiento_ms=0.0,
        delta_v_transito_insercion_ms=955.0,
        delta_v_retorno_ms=1073.0,
        delta_v_total_minimo_ms=2028.0,
        # Apolo 8: ≈66 h de tránsito (≈3 días). 4 días es el perfil estándar y 3 el rápido (valores de juego).
        dias_transito_estandar=4,
        dias_transito_rapido=3,
        dias_operacion_destino=5,
        # Valor de juego dentro de la cota calculada: a 100 km de altitud la sombra máxima es 0,394 de la órbita.
        fraccion_eclipse=0.25,
        entorno_riesgo=(
            "Radiación profunda, ocultación de señal al pasar por la cara oculta y ciclos térmicos en órbita lunar. "
            "El interior de Shackleton está en sombra permanente (NASA/LRO), por eso se observa desde órbita."
        ),
        descripcion=(
            "Misión orbital de cartografía y prospección polar: la nave llega en trayectoria translunar gracias al "
            "lanzador, se inserta en órbita lunar y regresa. Exige ≈2.030 m/s de delta-v propio, antena de largo "
            "alcance y reservas de soporte vital. No incluye descenso ni ascenso."
        ),
    ),
}

ACUERDOS_FINANCIACION: list[dict[str, Any]] = [
    {
        "id": "austero",
        "nombre": "Fondo Académico Cooperativo",
        "presupuesto_usd": 95000.0,
        "exigencia_ciencia": 45.0,
        "descripcion": (
            "Presupuesto restrictivo (95.000 USD) otorgado por un consorcio universitario. "
            "Exige prudencia extrema en masa y costes imprevistos, con metas científicas moderadas."
        ),
    },
    {
        "id": "estandar",
        "nombre": "Programa Estatal Zenit (Estándar)",
        "presupuesto_usd": 125000.0,
        "exigencia_ciencia": 65.0,
        "descripcion": (
            "Asignación gubernamental equilibrada (125.000 USD). Permite instrumentación sólida "
            "y margen razonable para operaciones en vuelo si se administra sin derroches."
        ),
    },
    {
        "id": "ambicioso",
        "nombre": "Consorcio Aeroespacial de Alta Prioridad",
        "presupuesto_usd": 155000.0,
        "exigencia_ciencia": 85.0,
        "descripcion": (
            "Financiación máxima (155.000 USD) condicionada a resultados científicos sobresalientes "
            "y transmisión íntegra de telemetría de alta resolución."
        ),
    },
]

COMPONENTES_CATALOGO: list[ComponenteCatalogo] = [
    # --- MOTORES (PROPULSIÓN) ---
    ComponenteCatalogo(
        id="motor_monoprop_basico",
        nombre="Propulsor Monopropelente de Hidracina",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=18000.0,
        masa_kg=65.0,
        consumo_w=40.0,
        # NASA (State-of-the-Art of Small Spacecraft Technology, cap. 4): los propulsores de
        # hidracina de clase >= 1 N rinden típicamente 200-235 s. Ver docs/fuentes-nasa.md.
        isp_s=225.0,
        combustible_kg=650.0,
        fiabilidad_nominal=0.88,
        slot_visual="tobera_compacta",
        descripcion_ficha=(
            "Motor químico económico de monopropelente (hidracina). Isp: 225 s | Combustible integrado: 650 kg. "
            "Cubre OTB con holgura; para la órbita lunar (≈2.030 m/s) queda justo o corto según la masa seca."
        ),
    ),
    ComponenteCatalogo(
        id="motor_biprop_estandar",
        nombre="Motor Bipropelente MMH/MON-3 (clase OMS-E)",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=28000.0,
        masa_kg=80.0,
        consumo_w=55.0,
        # NASA (Artemis I Engine Performance, NTRS 20240003648): OMS-E del módulo de servicio
        # de Orión, 26,7 kN y Isp 315,1 s con MMH/MON-3.
        isp_s=315.0,
        combustible_kg=795.0,
        fiabilidad_nominal=0.94,
        slot_visual="tobera_campana",
        descripcion_ficha=(
            "Motor hipergólico MMH/MON-3 de la clase del OMS-E de Orión (26,7 kN, Isp 315 s según NASA) | "
            "Combustible: 795 kg (≈2.900-3.200 m/s según tripulación y carga). "
            "Cubre con margen los ≈2.030 m/s de la órbita lunar si se controla la masa seca."
        ),
    ),
    ComponenteCatalogo(
        id="motor_crio_avanzado",
        nombre="Motor Criogénico LH2/LOX (clase RL10)",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=42000.0,
        masa_kg=95.0,
        consumo_w=85.0,
        # NASA (Centaur RL10A-3-3A, NTRS 20140011176): Isp de vacío 444,4 +/- 2,5 s y
        # 16.500 lbf (73 kN) con LH2/LOX. Masa del conjunto: valor de juego (escala 1,3 t).
        isp_s=444.0,
        combustible_kg=810.0,
        fiabilidad_nominal=0.96,
        slot_visual="tobera_expansiva",
        descripcion_ficha=(
            "Propulsión criogénica LH2/LOX de la clase RL10 (Isp de vacío 444 s medida por NASA, ≈73 kN) "
            "y 810 kg de propelente. Máximo delta-v del catálogo; alto coste financiero y "
            "mayor demanda eléctrica de la criogenia."
        ),
    ),
    # --- ENERGÍA ---
    ComponenteCatalogo(
        id="energia_solar_compacto",
        nombre="Paneles Desplegables Si-420",
        categoria=CategoriaComponente.ENERGIA,
        costo_usd=11000.0,
        masa_kg=30.0,
        generacion_w=420.0,
        capacidad_wh=1400.0,
        fiabilidad_nominal=0.89,
        slot_visual="paneles_cortos",
        descripcion_ficha=(
            "Arreglo solar básico de silicio. Generación: 420 W | Batería: 1.400 Wh. "
            "Ligero y económico, pero vulnerable a déficits si se conectan varios instrumentos."
        ),
    ),
    ComponenteCatalogo(
        id="energia_solar_estandar",
        nombre="Alas Fotovoltaicas GaAs-550",
        categoria=CategoriaComponente.ENERGIA,
        costo_usd=19000.0,
        masa_kg=45.0,
        generacion_w=550.0,
        capacidad_wh=2200.0,
        fiabilidad_nominal=0.95,
        slot_visual="paneles_dobles",
        descripcion_ficha=(
            "Paneles de arseniuro de galio de triple unión. Generación: 550 W | Batería: 2.200 Wh. "
            "Balance equilibrado para sostener soporte vital y laboratorio moderado."
        ),
    ),
    ComponenteCatalogo(
        id="energia_hibrida_rtg",
        nombre="Matriz Solar GaAs + MMRTG",
        categoria=CategoriaComponente.ENERGIA,
        costo_usd=31000.0,
        # Matriz GaAs-550 (45 kg, 550 W) + 1 MMRTG. NASA (hoja técnica MMRTG): 110 W eléctricos
        # al inicio de vida y 45 kg => 660 W y 90 kg en total.
        masa_kg=90.0,
        generacion_w=660.0,
        capacidad_wh=3400.0,
        fiabilidad_nominal=0.98,
        slot_visual="paneles_rtg",
        descripcion_ficha=(
            "Matriz solar GaAs (550 W) más un MMRTG (110 W eléctricos al inicio de vida, 45 kg, según NASA): "
            "660 W / 3.400 Wh. La parte isotópica no depende del Sol; la solar sigue sufriendo eclipses. "
            "Añade 90 kg de masa seca a la estructura."
        ),
    ),
    # --- TELECOMUNICACIONES ---
    ComponenteCatalogo(
        id="antena_uhf_basica",
        nombre="Antena de Baja Ganancia Banda-S",
        categoria=CategoriaComponente.ANTENA,
        costo_usd=7500.0,
        masa_kg=15.0,
        consumo_w=45.0,
        alcance_km=1500.0,
        tasa_kbps=1200.0,
        ventanas_dia=2,
        probabilidad_enlace=0.72,
        fiabilidad_nominal=0.90,
        slot_visual="antena_dipolo",
        descripcion_ficha=(
            "Enlace de corto alcance (1.500 km) en banda S de baja ganancia, 2 ventanas/día y 72% de "
            "disponibilidad probabilística. Adecuada para OTB; sin ganancia ni caudal para volúmenes lunares."
        ),
    ),
    ComponenteCatalogo(
        id="antena_parabolica_x",
        nombre="Plato Direccional Banda-X (2 Mbps)",
        categoria=CategoriaComponente.ANTENA,
        costo_usd=15000.0,
        masa_kg=25.0,
        consumo_w=75.0,
        alcance_km=420000.0,
        tasa_kbps=2000.0,
        ventanas_dia=3,
        probabilidad_enlace=0.86,
        fiabilidad_nominal=0.94,
        slot_visual="antena_plato",
        descripcion_ficha=(
            "Antena parabólica de espacio cislunar (420.000 km). Tasa: 2.000 kbps (≈0,9 GB por hora de enlace), "
            "3 ventanas/día con 86% de probabilidad de enlace."
        ),
    ),
    ComponenteCatalogo(
        id="antena_laser_ka",
        nombre="Terminal de Comunicaciones Ópticas (láser infrarrojo)",
        categoria=CategoriaComponente.ANTENA,
        costo_usd=24000.0,
        masa_kg=40.0,
        consumo_w=115.0,
        alcance_km=600000.0,
        tasa_kbps=4500.0,
        ventanas_dia=4,
        probabilidad_enlace=0.95,
        fiabilidad_nominal=0.96,
        slot_visual="antena_laser",
        descripcion_ficha=(
            "Comunicación óptica por láser infrarrojo de alta velocidad (4.500 kbps, 4 ventanas/día, "
            "95% disponibilidad). Ideal cuando se instalan múltiples instrumentos científicos."
        ),
    ),
    # --- SOPORTE VITAL (ECLSS) ---
    # Aproximación documentada: `masa_kg` agrupa el módulo y sus consumibles a escala de tripulante de 25 kg
    # (NASA usa ≈6,57 kg/persona-día para humanos de 82 kg; ver docs/fuentes-nasa.md §4, punto 4).
    ComponenteCatalogo(
        id="eclss_abierto_ligero",
        nombre="Módulo Vital de Ciclo Abierto V-18",
        categoria=CategoriaComponente.SOPORTE_VITAL,
        costo_usd=10000.0,
        masa_kg=35.0,
        consumo_w=110.0,
        dias_o2=18.0,
        dias_comida=18.0,
        fiabilidad_nominal=0.90,
        slot_visual="eclss_compacto",
        descripcion_ficha=(
            "Reserva de consumibles de 18 días-persona (ej. 3 tripulantes durante 6 días). "
            "Ligero, pero sin margen ante retrasos de trayectoria o fugas."
        ),
    ),
    ComponenteCatalogo(
        id="eclss_reciclaje_estandar",
        nombre="Sistema Regenerativo Bioreactor V-32",
        categoria=CategoriaComponente.SOPORTE_VITAL,
        costo_usd=17500.0,
        masa_kg=50.0,
        consumo_w=145.0,
        dias_o2=32.0,
        dias_comida=32.0,
        fiabilidad_nominal=0.95,
        slot_visual="eclss_estandar",
        descripcion_ficha=(
            "Reciclaje parcial de CO2 y agua. Provee 32 días-persona de oxígeno y raciones "
            "(ej. 4 tripulantes durante 8 días)."
        ),
    ),
    ComponenteCatalogo(
        id="eclss_cerrado_lunar",
        nombre="Soporte Vital de Larga Duración V-48",
        categoria=CategoriaComponente.SOPORTE_VITAL,
        costo_usd=25000.0,
        masa_kg=75.0,
        consumo_w=180.0,
        dias_o2=48.0,
        dias_comida=48.0,
        fiabilidad_nominal=0.97,
        slot_visual="eclss_blindado",
        descripcion_ficha=(
            "Capacidad extendida de 48 días-persona con blindaje térmico adicional. "
            "Elevada masa y consumo energético continuo."
        ),
    ),
    # --- INSTRUMENTOS CIENTÍFICOS (PAYLOAD) ---
    ComponenteCatalogo(
        id="inst_espectrometro",
        nombre="Espectrómetro de Masas Orbital",
        categoria=CategoriaComponente.INSTRUMENTO,
        costo_usd=8000.0,
        masa_kg=50.0,
        consumo_w=120.0,
        puntos_ciencia_base=15.0,
        datos_gb_dia=2.0,
        especialidad_requerida="geologia",
        fiabilidad_nominal=0.93,
        slot_visual="payload_espectrometro",
        descripcion_ficha=(
            "Analizador espectral de alta resolución (+50 kg, +120 W, +8.000 USD). "
            "Genera +15 pts de ciencia base y +2 GB de datos/día. Especialidad afín: Geología."
        ),
    ),
    ComponenteCatalogo(
        id="inst_radar_criosfera",
        nombre="Radar de Penetración Subsuperficial",
        categoria=CategoriaComponente.INSTRUMENTO,
        costo_usd=11500.0,
        masa_kg=65.0,
        consumo_w=140.0,
        puntos_ciencia_base=22.0,
        datos_gb_dia=3.0,
        especialidad_requerida="ingenieria",
        fiabilidad_nominal=0.91,
        slot_visual="payload_radar",
        descripcion_ficha=(
            "Sonda activa para cartografiar hielo subterráneo y capas atmosféricas (+65 kg, +140 W). "
            "Genera +22 pts ciencia y +3 GB/día. Especialidad afín: Ingeniería."
        ),
    ),
    ComponenteCatalogo(
        id="inst_biocapsula",
        nombre=" Cámara de Exobiología y Radiación",
        categoria=CategoriaComponente.INSTRUMENTO,
        costo_usd=9500.0,
        masa_kg=40.0,
        consumo_w=95.0,
        puntos_ciencia_base=18.0,
        datos_gb_dia=1.8,
        especialidad_requerida="astrobiologia",
        fiabilidad_nominal=0.94,
        slot_visual="payload_biocapsula",
        descripcion_ficha=(
            "Laboratorio sellado de muestras y dosimetría biológica (+40 kg, +95 W). "
            "Genera +18 pts ciencia y +1,8 GB/día. Especialidad afín: Astrobiología."
        ),
    ),
    # --- SISTEMAS AUTÓNOMOS (ROBOTS OPCIONALES) ---
    ComponenteCatalogo(
        id="robot_sonda_eva",
        nombre="Unidad Autónoma Hexápodo 'Kibo-R1'",
        categoria=CategoriaComponente.ROBOT,
        costo_usd=12000.0,
        masa_kg=55.0,
        consumo_w=90.0,
        puntos_ciencia_base=12.0,
        datos_gb_dia=1.5,
        fiabilidad_nominal=0.88,
        slot_visual="modulo_robot",
        descripcion_ficha=(
            "Robot autónomo determinista (+55 kg, +90 W). No consume O2 ni comida y no sufre estado de ánimo. "
            "Abstracción del MVP: representa una sonda desplegable; no se simula descenso ni ascenso lunar."
        ),
    ),
]

CANDIDATOS_TRIPULACION: list[TripulanteEstado] = [
    TripulanteEstado(
        id="crew_elena",
        nombre="Dra. Elena Rostova",
        rol="Especialista en Geología Planetaria",
        especialidad="geologia",
        experiencia=4,
        salario_usd=11000.0,
        estado_animo=EstadoAnimo.SOL,
        habitacion_actual="laboratorio",
        biografia_corta="Veterana en espectroscopía orbital y estratigrafía lunar. Alta velocidad de análisis.",
    ),
    TripulanteEstado(
        id="crew_marco",
        nombre="Ing. Marco Valdés",
        rol="Jefe de Sistemas y Propulsión",
        especialidad="ingenieria",
        experiencia=5,
        salario_usd=14000.0,
        estado_animo=EstadoAnimo.SOL,
        habitacion_actual="sala_sistemas",
        biografia_corta="Especialista senior en mantenimiento en vuelo, radar y reparación de subsistemas críticos.",
    ),
    TripulanteEstado(
        id="crew_lin",
        nombre="Dr. Lin Wei",
        rol="Especialista en Astrobiología",
        especialidad="astrobiologia",
        experiencia=3,
        salario_usd=9500.0,
        estado_animo=EstadoAnimo.SOL,
        habitacion_actual="laboratorio",
        biografia_corta="Investigador de efectos radiológicos y cámaras biológicas en espacio profundo.",
    ),
    TripulanteEstado(
        id="crew_sara",
        nombre="Dra. Sara Al-Mansoor",
        rol="Oficial Médico y Soporte Vital",
        especialidad="medicina",
        experiencia=4,
        salario_usd=10500.0,
        estado_animo=EstadoAnimo.SOL,
        habitacion_actual="soporte_vital",
        biografia_corta="Preserva la estabilidad psicológica del equipo y optimiza el reciclaje de soporte vital.",
    ),
    TripulanteEstado(
        id="crew_tomas",
        nombre="Téc. Tomás Ferrer",
        rol="Técnico Generalista Junior",
        especialidad="ingenieria",
        experiencia=2,
        salario_usd=6000.0,
        estado_animo=EstadoAnimo.NUBE,
        habitacion_actual="sala_sistemas",
        biografia_corta="Opción económica para cubrir la especialidad de ingeniería, aunque con menor velocidad de ejecución.",
    ),
]


def construir_habitaciones_iniciales() -> list[EstadoHabitacion2D]:
    """Crea las 4 habitaciones contiguas para la interfaz 2D (interacción con tecla E)."""
    return [
        EstadoHabitacion2D(
            id="cabina_mando",
            nombre="Cabina de Mando",
            orden=0,
            puerta_izquierda=None,
            puerta_derecha="laboratorio",
            sistema_principal="Telemetría de Energía, Combustible y Delta-v",
            alerta_activa=False,
            color_alerta="cyan",
            mensaje_terminal="Consola principal activa. Lecturas exactas de energía y propelente disponibles aquí.",
            requiere_visita_para_datos=True,
        ),
        EstadoHabitacion2D(
            id="laboratorio",
            nombre="Laboratorio Científico",
            orden=1,
            puerta_izquierda="cabina_mando",
            puerta_derecha="soporte_vital",
            sistema_principal="Instrumentación Científica y Procesamiento de Datos",
            alerta_activa=False,
            color_alerta="cyan",
            mensaje_terminal="Bancos de experimentación listos. Requiere presencia en sala para operar instrumentos.",
            requiere_visita_para_datos=True,
        ),
        EstadoHabitacion2D(
            id="soporte_vital",
            nombre="Módulo de Vida y Habitación",
            orden=2,
            puerta_izquierda="laboratorio",
            puerta_derecha="sala_sistemas",
            sistema_principal="ECLSS (Oxígeno, Agua, Raciones) y Descanso",
            alerta_activa=False,
            color_alerta="green",
            mensaje_terminal="Presión atmosférica y reciclaje nominales. Estado anímico de la tripulación monitorizado.",
            requiere_visita_para_datos=False,
        ),
        EstadoHabitacion2D(
            id="sala_sistemas",
            nombre="Sala de Sistemas y Esclusa",
            orden=3,
            puerta_izquierda="soporte_vital",
            puerta_derecha=None,
            sistema_principal="Buses de Potencia, Propulsión, Antena y Bahía Robótica",
            alerta_activa=False,
            color_alerta="amber" if False else "cyan",
            mensaje_terminal="Núcleo de distribución eléctrica, válvulas propulsivas y control de antena.",
            requiere_visita_para_datos=False,
        ),
    ]
