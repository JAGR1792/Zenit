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
    DestinoId.OTB: ParametrosDestino(
        id=DestinoId.OTB,
        nombre="Órbita Terrestre Baja (OTB - 400 km)",
        distancia_km=400.0,
        delta_v_lanzamiento_ms=1450.0,
        delta_v_transito_insercion_ms=350.0,
        delta_v_retorno_ms=300.0,
        delta_v_total_minimo_ms=2100.0,
        dias_transito_estandar=1,
        dias_transito_rapido=1,
        dias_operacion_destino=4,
        fraccion_eclipse=0.38,
        entorno_riesgo="Ciclado térmico orbital rápido y micro-escombros en órbita baja.",
        descripcion=(
            "Misión de observación atmosférica y microgravedad en órbita terrestre baja. "
            "Menor exigencia de delta-v y enlace de corta distancia, pero eclipses frecuentes cada 90 minutos."
        ),
    ),
    DestinoId.LUNA: ParametrosDestino(
        id=DestinoId.LUNA,
        nombre="Órbita y Superficie Lunar (Cráter Shackleton - 384.400 km)",
        distancia_km=384400.0,
        delta_v_lanzamiento_ms=1450.0,
        delta_v_transito_insercion_ms=1050.0,
        delta_v_retorno_ms=600.0,
        delta_v_total_minimo_ms=3100.0,
        dias_transito_estandar=4,
        dias_transito_rapido=2,
        dias_operacion_destino=5,
        fraccion_eclipse=0.25,
        entorno_riesgo="Regolito lunar helado resbaladizo para sistemas robóticos, radiación profunda y ocultación de señal.",
        descripcion=(
            "Expedición científica cislunar y de prospección polar. Exige al menos 3.100 m/s de delta-v de misión, "
            "antena de largo alcance y reservas críticas de soporte vital."
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
        nombre="Propulsor Hidracina M-280",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=18000.0,
        masa_kg=65.0,
        consumo_w=40.0,
        isp_s=285.0,
        combustible_kg=650.0,
        fiabilidad_nominal=0.88,
        slot_visual="tobera_compacta",
        descripcion_ficha=(
            "Motor químico económico de monopropelente. Isp: 285 s | Combustible integrado: 650 kg. "
            "Suficiente para maniobras en OTB, pero muy ajustado para transferencia lunar pesada."
        ),
    ),
    ComponenteCatalogo(
        id="motor_biprop_estandar",
        nombre="Tobera Bipropelente Hyper-320",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=28000.0,
        masa_kg=80.0,
        consumo_w=55.0,
        isp_s=320.0,
        combustible_kg=795.0,
        fiabilidad_nominal=0.94,
        slot_visual="tobera_campana",
        descripcion_ficha=(
            "Motor hipergólico de referencia aeroespacial. Isp: 320 s | Combustible: 795 kg (~3.400 m/s base). "
            "Permite alcanzar los 3.100+ m/s requeridos para la Luna si se controla la masa seca."
        ),
    ),
    ComponenteCatalogo(
        id="motor_crio_avanzado",
        nombre="Cámara Criogénica Methalox Z-360",
        categoria=CategoriaComponente.MOTOR,
        costo_usd=42000.0,
        masa_kg=95.0,
        consumo_w=85.0,
        isp_s=360.0,
        combustible_kg=810.0,
        fiabilidad_nominal=0.96,
        slot_visual="tobera_expansiva",
        descripcion_ficha=(
            "Propulsión criogénica de alto impulso específico (360 s) y 810 kg de propelente. "
            "Alto coste financiero y mayor demanda eléctrica de criostatos."
        ),
    ),
    # --- ENERGÍA ---
    ComponenteCatalogo(
        id="energia_solar_compacto",
        nombre="Paneles Desplegables Si-380",
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
        nombre="Matriz Solar + Auxiliar Isotópico P-780",
        categoria=CategoriaComponente.ENERGIA,
        costo_usd=31000.0,
        masa_kg=85.0,
        generacion_w=780.0,
        capacidad_wh=3400.0,
        fiabilidad_nominal=0.98,
        slot_visual="paneles_rtg",
        descripcion_ficha=(
            "Sistema energético de alta capacidad (780 W / 3.400 Wh) inmune a sombras prolongadas. "
            "Añade 85 kg de masa seca a la estructura."
        ),
    ),
    # --- TELECOMUNICACIONES ---
    ComponenteCatalogo(
        id="antena_uhf_basica",
        nombre="Antena Omnidireccional Banda-S",
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
            "Enlace de corto alcance (1.500 km), 2 ventanas/día y 72% de disponibilidad probabilística. "
            "Adecuada para OTB; insuficiente en caudal y ganancia para grandes volúmenes lunares."
        ),
    ),
    ComponenteCatalogo(
        id="antena_parabolica_x",
        nombre="Plato Direccional Banda-X 2Mbps",
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
            "Antena parabólica de espacio cislunar (420.000 km). Tasa: 2.000 kbps (~2 GB/ventana), "
            "3 ventanas/día con 86% de probabilidad de enlace."
        ),
    ),
    ComponenteCatalogo(
        id="antena_laser_ka",
        nombre="Transceptor Óptico Banda-Ka DeepLink",
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
            "Comunicación óptica de alta velocidad (4.500 kbps, 4 ventanas/día, 95% disponibilidad). "
            "Ideal cuando se instalan múltiples instrumentos científicos."
        ),
    ),
    # --- SOPORTE VITAL (ECLSS) ---
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
            "Robot autónomo determinista (+55 kg, +90 W). No consume O2 ni comida y no sufre estado de ánimo, "
            "pero puede resbalar o atascarse en terreno lunar helado."
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
