/**
 * Motor de simulación local de respaldo (100% compatible con el backend Python de Zenit).
 * Garantiza que en despliegues serverless (como Vercel) donde las instancias efímeras
 * puedan reiniciar `/tmp` entre peticiones o cuando el proxy `/api` no esté disponible,
 * el jugador nunca sufra bloqueos al iniciar o avanzar la expedición.
 */

import type {
  AcuerdoFinanciacion,
  CambioVariable,
  CatalogoCompleto,
  ComponenteCatalogo,
  DecisionResponse,
  DestinoId,
  DificultadId,
  DimensionEvaluacion,
  EstadoHabitacion2D,
  EstadoMision,
  EventoMision,
  InformeFinal,
  ParametrosDestino,
  TripulanteEstado,
} from './api'

const G0_MS2 = 9.80665
const MASA_POR_TRIPULANTE_KG = 25.0

export const NOMBRES_ETAPAS_LOCAL: Record<string, string> = {
  '1': '1. Definición de la misión',
  '2': '2. Negociación y financiación',
  '3': '3. Diseño de la nave y selección de personal',
  '4': '4. Planificación orbital',
  '5': '5. Lanzamiento',
  '6': '6. Tránsito',
  '7': '7. Operaciones científicas',
  '8': '8. Operaciones de tripulación',
  '9': '9. Comunicaciones',
  '10': '10. Retorno y evaluación',
}

export const DESTINOS_LOCAL: Record<DestinoId, ParametrosDestino> = {
  OTB: {
    id: 'OTB',
    nombre: 'Órbita Terrestre Baja (OTB - 400 km)',
    distancia_km: 400,
    delta_v_lanzamiento_ms: 1450,
    delta_v_transito_insercion_ms: 350,
    delta_v_retorno_ms: 300,
    delta_v_total_minimo_ms: 2100,
    dias_transito_estandar: 1,
    dias_transito_rapido: 1,
    dias_operacion_destino: 4,
    fraccion_eclipse: 0.38,
    entorno_riesgo: 'Ciclado térmico orbital rápido y micro-escombros en órbita baja.',
    descripcion:
      'Misión de observación atmosférica y microgravedad en órbita terrestre baja. Menor exigencia de delta-v y enlace de corta distancia, pero eclipses frecuentes cada 90 minutos.',
  },
  LUNA: {
    id: 'LUNA',
    nombre: 'Órbita y Superficie Lunar (Cráter Shackleton - 384.400 km)',
    distancia_km: 384400,
    delta_v_lanzamiento_ms: 1450,
    delta_v_transito_insercion_ms: 1050,
    delta_v_retorno_ms: 600,
    delta_v_total_minimo_ms: 3100,
    dias_transito_estandar: 4,
    dias_transito_rapido: 2,
    dias_operacion_destino: 5,
    fraccion_eclipse: 0.25,
    entorno_riesgo:
      'Regolito lunar helado resbaladizo para sistemas robóticos, radiación profunda y ocultación de señal.',
    descripcion:
      'Expedición científica cislunar y de prospección polar. Exige al menos 3.100 m/s de delta-v de misión, antena de largo alcance y reservas críticas de soporte vital.',
  },
}

export const ACUERDOS_LOCAL: AcuerdoFinanciacion[] = [
  {
    id: 'austero',
    nombre: 'Fondo Académico Cooperativo',
    presupuesto_usd: 95000,
    exigencia_ciencia: 45,
    descripcion:
      'Presupuesto restrictivo (95.000 USD) otorgado por un consorcio universitario. Exige prudencia extrema en masa y costes imprevistos, con metas científicas moderadas.',
  },
  {
    id: 'estandar',
    nombre: 'Programa Estatal Zenit (Estándar)',
    presupuesto_usd: 125000,
    exigencia_ciencia: 65,
    descripcion:
      'Asignación gubernamental equilibrada (125.000 USD). Permite instrumentación sólida y margen razonable para operaciones en vuelo si se administra sin derroches.',
  },
  {
    id: 'ambicioso',
    nombre: 'Consorcio Aeroespacial de Alta Prioridad',
    presupuesto_usd: 155000,
    exigencia_ciencia: 85,
    descripcion:
      'Financiación máxima (155.000 USD) condicionada a resultados científicos sobresalientes y transmisión íntegra de telemetría de alta resolución.',
  },
]

export const COMPONENTES_LOCAL: ComponenteCatalogo[] = [
  {
    id: 'motor_monoprop_basico',
    nombre: 'Propulsor Hidracina M-280',
    categoria: 'motor',
    costo_usd: 18000,
    masa_kg: 65,
    consumo_w: 40,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 285,
    combustible_kg: 650,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.88,
    slot_visual: 'tobera_compacta',
    descripcion_ficha:
      'Motor químico económico de monopropelente. Isp: 285 s | Combustible integrado: 650 kg. Suficiente para maniobras en OTB, pero muy ajustado para transferencia lunar pesada.',
  },
  {
    id: 'motor_biprop_estandar',
    nombre: 'Tobera Bipropelente Hyper-320',
    categoria: 'motor',
    costo_usd: 28000,
    masa_kg: 80,
    consumo_w: 55,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 320,
    combustible_kg: 795,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.94,
    slot_visual: 'tobera_campana',
    descripcion_ficha:
      'Motor hipergólico de referencia aeroespacial. Isp: 320 s | Combustible: 795 kg (~3.400 m/s base). Permite alcanzar los 3.100+ m/s requeridos para la Luna si se controla la masa seca.',
  },
  {
    id: 'motor_crio_avanzado',
    nombre: 'Cámara Criogénica Methalox Z-360',
    categoria: 'motor',
    costo_usd: 42000,
    masa_kg: 95,
    consumo_w: 85,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 360,
    combustible_kg: 810,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.96,
    slot_visual: 'tobera_expansiva',
    descripcion_ficha:
      'Propulsión criogénica de alto impulso específico (360 s) y 810 kg de propelente. Alto coste financiero y mayor demanda eléctrica de criostatos.',
  },
  {
    id: 'energia_solar_compacto',
    nombre: 'Paneles Desplegables Si-380',
    categoria: 'energia',
    costo_usd: 11000,
    masa_kg: 30,
    consumo_w: 0,
    generacion_w: 420,
    capacidad_wh: 1400,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.89,
    slot_visual: 'paneles_cortos',
    descripcion_ficha:
      'Arreglo solar básico de silicio. Generación: 420 W | Batería: 1.400 Wh. Ligero y económico, pero vulnerable a déficits si se conectan varios instrumentos.',
  },
  {
    id: 'energia_solar_estandar',
    nombre: 'Alas Fotovoltaicas GaAs-550',
    categoria: 'energia',
    costo_usd: 19000,
    masa_kg: 45,
    consumo_w: 0,
    generacion_w: 550,
    capacidad_wh: 2200,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.95,
    slot_visual: 'paneles_dobles',
    descripcion_ficha:
      'Paneles de arseniuro de galio de triple unión. Generación: 550 W | Batería: 2.200 Wh. Balance equilibrado para sostener soporte vital y laboratorio moderado.',
  },
  {
    id: 'energia_hibrida_rtg',
    nombre: 'Matriz Solar + Auxiliar Isotópico P-780',
    categoria: 'energia',
    costo_usd: 31000,
    masa_kg: 85,
    consumo_w: 0,
    generacion_w: 780,
    capacidad_wh: 3400,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.98,
    slot_visual: 'paneles_rtg',
    descripcion_ficha:
      'Sistema energético de alta capacidad (780 W / 3.400 Wh) inmune a sombras prolongadas. Añade 85 kg de masa seca a la estructura.',
  },
  {
    id: 'antena_uhf_basica',
    nombre: 'Antena Omnidireccional Banda-S',
    categoria: 'antena',
    costo_usd: 7500,
    masa_kg: 15,
    consumo_w: 45,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 1500,
    tasa_kbps: 1200,
    ventanas_dia: 2,
    probabilidad_enlace: 0.72,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.9,
    slot_visual: 'antena_dipolo',
    descripcion_ficha:
      'Enlace de corto alcance (1.500 km), 2 ventanas/día y 72% de disponibilidad probabilística. Adecuada para OTB; insuficiente en caudal y ganancia para grandes volúmenes lunares.',
  },
  {
    id: 'antena_parabolica_x',
    nombre: 'Plato Direccional Banda-X 2Mbps',
    categoria: 'antena',
    costo_usd: 15000,
    masa_kg: 25,
    consumo_w: 75,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 420000,
    tasa_kbps: 2000,
    ventanas_dia: 3,
    probabilidad_enlace: 0.86,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.94,
    slot_visual: 'antena_plato',
    descripcion_ficha:
      'Antena parabólica de espacio cislunar (420.000 km). Tasa: 2.000 kbps (~2 GB/ventana), 3 ventanas/día con 86% de probabilidad de enlace.',
  },
  {
    id: 'antena_laser_ka',
    nombre: 'Transceptor Óptico Banda-Ka DeepLink',
    categoria: 'antena',
    costo_usd: 24000,
    masa_kg: 40,
    consumo_w: 115,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 600000,
    tasa_kbps: 4500,
    ventanas_dia: 4,
    probabilidad_enlace: 0.95,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.96,
    slot_visual: 'antena_laser',
    descripcion_ficha:
      'Comunicación óptica de alta velocidad (4.500 kbps, 4 ventanas/día, 95% disponibilidad). Ideal cuando se instalan múltiples instrumentos científicos.',
  },
  {
    id: 'eclss_abierto_ligero',
    nombre: 'Módulo Vital de Ciclo Abierto V-18',
    categoria: 'soporte_vital',
    costo_usd: 10000,
    masa_kg: 35,
    consumo_w: 110,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 18,
    dias_comida: 18,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.9,
    slot_visual: 'eclss_compacto',
    descripcion_ficha:
      'Reserva de consumibles de 18 días-persona (ej. 3 tripulantes durante 6 días). Ligero, pero sin margen ante retrasos de trayectoria o fugas.',
  },
  {
    id: 'eclss_reciclaje_estandar',
    nombre: 'Sistema Regenerativo Bioreactor V-32',
    categoria: 'soporte_vital',
    costo_usd: 17500,
    masa_kg: 50,
    consumo_w: 145,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 32,
    dias_comida: 32,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.95,
    slot_visual: 'eclss_estandar',
    descripcion_ficha:
      'Reciclaje parcial de CO2 y agua. Provee 32 días-persona de oxígeno y raciones (ej. 4 tripulantes durante 8 días).',
  },
  {
    id: 'eclss_cerrado_lunar',
    nombre: 'Soporte Vital de Larga Duración V-48',
    categoria: 'soporte_vital',
    costo_usd: 25000,
    masa_kg: 75,
    consumo_w: 180,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 48,
    dias_comida: 48,
    puntos_ciencia_base: 0,
    datos_gb_dia: 0,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.97,
    slot_visual: 'eclss_blindado',
    descripcion_ficha:
      'Capacidad extendida de 48 días-persona con blindaje térmico adicional. Elevada masa y consumo energético continuo.',
  },
  {
    id: 'inst_espectrometro',
    nombre: 'Espectrómetro de Masas Orbital',
    categoria: 'instrumento',
    costo_usd: 8000,
    masa_kg: 50,
    consumo_w: 120,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 15,
    datos_gb_dia: 2,
    especialidad_requerida: 'geologia',
    fiabilidad_nominal: 0.93,
    slot_visual: 'payload_espectrometro',
    descripcion_ficha:
      'Analizador espectral de alta resolución (+50 kg, +120 W, +8.000 USD). Genera +15 pts de ciencia base y +2 GB de datos/día. Especialidad afín: Geología.',
  },
  {
    id: 'inst_radar_criosfera',
    nombre: 'Radar de Penetración Subsuperficial',
    categoria: 'instrumento',
    costo_usd: 11500,
    masa_kg: 65,
    consumo_w: 140,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 22,
    datos_gb_dia: 3,
    especialidad_requerida: 'ingenieria',
    fiabilidad_nominal: 0.91,
    slot_visual: 'payload_radar',
    descripcion_ficha:
      'Sonda activa para cartografiar hielo subterráneo y capas atmosféricas (+65 kg, +140 W). Genera +22 pts ciencia y +3 GB/día. Especialidad afín: Ingeniería.',
  },
  {
    id: 'inst_biocapsula',
    nombre: 'Cámara de Exobiología y Radiación',
    categoria: 'instrumento',
    costo_usd: 9500,
    masa_kg: 40,
    consumo_w: 95,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 18,
    datos_gb_dia: 1.8,
    especialidad_requerida: 'astrobiologia',
    fiabilidad_nominal: 0.94,
    slot_visual: 'payload_biocapsula',
    descripcion_ficha:
      'Laboratorio sellado de muestras y dosimetría biológica (+40 kg, +95 W). Genera +18 pts ciencia y +1,8 GB/día. Especialidad afín: Astrobiología.',
  },
  {
    id: 'robot_sonda_eva',
    nombre: "Unidad Autónoma Hexápodo 'Kibo-R1'",
    categoria: 'robot',
    costo_usd: 12000,
    masa_kg: 55,
    consumo_w: 90,
    generacion_w: 0,
    capacidad_wh: 0,
    isp_s: 0,
    combustible_kg: 0,
    alcance_km: 0,
    tasa_kbps: 0,
    ventanas_dia: 0,
    probabilidad_enlace: 0,
    dias_o2: 0,
    dias_comida: 0,
    puntos_ciencia_base: 12,
    datos_gb_dia: 1.5,
    especialidad_requerida: null,
    fiabilidad_nominal: 0.88,
    slot_visual: 'modulo_robot',
    descripcion_ficha:
      'Robot autónomo determinista (+55 kg, +90 W). No consume O2 ni comida y no sufre estado de ánimo, pero puede resbalar o atascarse en terreno lunar helado.',
  },
]

export const CANDIDATOS_LOCAL: TripulanteEstado[] = [
  {
    id: 'crew_elena',
    nombre: 'Dra. Elena Rostova',
    rol: 'Especialista en Geología Planetaria',
    especialidad: 'geologia',
    experiencia: 4,
    salario_usd: 11000,
    estado_animo: 'sol',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: false,
    habitacion_actual: 'laboratorio',
    biografia_corta:
      'Veterana en espectroscopía orbital y estratigrafía lunar. Alta velocidad de análisis.',
  },
  {
    id: 'crew_marco',
    nombre: 'Ing. Marco Valdés',
    rol: 'Jefe de Sistemas y Propulsión',
    especialidad: 'ingenieria',
    experiencia: 5,
    salario_usd: 14000,
    estado_animo: 'sol',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: false,
    habitacion_actual: 'sala_sistemas',
    biografia_corta:
      'Especialista senior en mantenimiento en vuelo, radar y reparación de subsistemas críticos.',
  },
  {
    id: 'crew_lin',
    nombre: 'Dr. Lin Wei',
    rol: 'Especialista en Astrobiología',
    especialidad: 'astrobiologia',
    experiencia: 3,
    salario_usd: 9500,
    estado_animo: 'sol',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: false,
    habitacion_actual: 'laboratorio',
    biografia_corta:
      'Investigador de efectos radiológicos y cámaras biológicas en espacio profundo.',
  },
  {
    id: 'crew_sara',
    nombre: 'Dra. Sara Al-Mansoor',
    rol: 'Oficial Médico y Soporte Vital',
    especialidad: 'medicina',
    experiencia: 4,
    salario_usd: 10500,
    estado_animo: 'sol',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: false,
    habitacion_actual: 'soporte_vital',
    biografia_corta:
      'Preserva la estabilidad psicológica del equipo y optimiza el reciclaje de soporte vital.',
  },
  {
    id: 'crew_tomas',
    nombre: 'Téc. Tomás Ferrer',
    rol: 'Técnico Generalista Junior',
    especialidad: 'ingenieria',
    experiencia: 2,
    salario_usd: 6000,
    estado_animo: 'nube',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: false,
    habitacion_actual: 'sala_sistemas',
    biografia_corta:
      'Opción económica para cubrir la especialidad de ingeniería, aunque con menor velocidad de ejecución.',
  },
]

function construirHabitacionesIniciales(): EstadoHabitacion2D[] {
  return [
    {
      id: 'cabina_mando',
      nombre: 'Cabina de Mando',
      orden: 0,
      puerta_izquierda: null,
      puerta_derecha: 'laboratorio',
      sistema_principal: 'Telemetría de Energía, Combustible y Delta-v',
      alerta_activa: false,
      color_alerta: 'cyan',
      mensaje_terminal:
        'Consola principal activa. Lecturas exactas de energía y propelente disponibles aquí.',
      requiere_visita_para_datos: true,
    },
    {
      id: 'laboratorio',
      nombre: 'Laboratorio Científico',
      orden: 1,
      puerta_izquierda: 'cabina_mando',
      puerta_derecha: 'soporte_vital',
      sistema_principal: 'Instrumentación Científica y Procesamiento de Datos',
      alerta_activa: false,
      color_alerta: 'cyan',
      mensaje_terminal:
        'Bancos de experimentación listos. Requiere presencia en sala para operar instrumentos.',
      requiere_visita_para_datos: true,
    },
    {
      id: 'soporte_vital',
      nombre: 'Módulo de Vida y Habitación',
      orden: 2,
      puerta_izquierda: 'laboratorio',
      puerta_derecha: 'sala_sistemas',
      sistema_principal: 'ECLSS (Oxígeno, Agua, Raciones) y Descanso',
      alerta_activa: false,
      color_alerta: 'green',
      mensaje_terminal:
        'Presión atmosférica y reciclaje nominales. Estado anímico de la tripulación monitorizado.',
      requiere_visita_para_datos: false,
    },
    {
      id: 'sala_sistemas',
      nombre: 'Sala de Sistemas y Esclusa',
      orden: 3,
      puerta_izquierda: 'soporte_vital',
      puerta_derecha: null,
      sistema_principal: 'Buses de Potencia, Propulsión, Antena y Bahía Robótica',
      alerta_activa: false,
      color_alerta: 'cyan',
      mensaje_terminal:
        'Núcleo de distribución eléctrica, válvulas propulsivas y control de antena.',
      requiere_visita_para_datos: false,
    },
  ]
}

const STORAGE_KEY = 'zenit_misiones_locales_v1'
const memMissions: Record<string, EstadoMision> = {}

function cargarMapaLocal(): Record<string, EstadoMision> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Record<string, EstadoMision>
      Object.assign(memMissions, parsed)
    }
  } catch {
    // En entornos sin localStorage se usa memMissions
  }
  return memMissions
}

export function guardarMisionEnCacheLocal(estado: EstadoMision): EstadoMision {
  cargarMapaLocal()
  const copia = JSON.parse(JSON.stringify(estado)) as EstadoMision
  memMissions[copia.id] = copia
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(memMissions))
  } catch {
    // Ignorar errores de cuota
  }
  return copia
}

export function obtenerMisionDeCacheLocal(missionId: string): EstadoMision | null {
  cargarMapaLocal()
  const found = memMissions[missionId]
  return found ? (JSON.parse(JSON.stringify(found)) as EstadoMision) : null
}

function round(val: number, decimals = 1): number {
  const factor = Math.pow(10, decimals)
  return Math.round(val * factor) / factor
}

function calcularRendimientoTripulacion(
  tripulacion: TripulanteEstado[],
  especialidadRequerida: string | null = null,
  esTareaComun = true,
): [number, number] {
  const vivos = tripulacion.filter((t) => t.vivo)
  if (vivos.length === 0) return [0, 0]

  const factoresVel: Record<string, number> = { sol: 1.0, nube: 0.82, lluvia: 0.62 }
  const factoresCal: Record<string, number> = { sol: 1.0, nube: 0.88, lluvia: 0.7 }

  const velocidades: number[] = []
  const calidades: number[] = []

  for (const m of vivos) {
    const modExp = 0.75 + m.experiencia * 0.1
    let modRolVel = 1.0
    let modRolCal = 1.0
    if (especialidadRequerida === null || m.especialidad === especialidadRequerida) {
      modRolVel = especialidadRequerida ? 1.2 : 1.0
      modRolCal = especialidadRequerida ? 1.15 : 1.0
    } else if (esTareaComun) {
      modRolVel = 0.72
      modRolCal = 0.8
    } else {
      modRolVel = 0.45
      modRolCal = 0.55
    }
    velocidades.push(modExp * modRolVel * (factoresVel[m.estado_animo] ?? 1.0))
    calidades.push(modRolCal * (factoresCal[m.estado_animo] ?? 1.0))
  }

  const factorDotacion = vivos.length === 1 ? 0.8 : Math.min(1.15, 0.9 + 0.08 * vivos.length)
  const velMedia = round(
    (velocidades.reduce((a, b) => a + b, 0) / velocidades.length) * factorDotacion,
    2,
  )
  const calMedia = round(
    Math.min(1.25, calidades.reduce((a, b) => a + b, 0) / calidades.length),
    2,
  )
  return [velMedia, calMedia]
}

export function recalcularSubsistemasLocal(estado: EstadoMision): EstadoMision {
  const catalogo = Object.fromEntries(COMPONENTES_LOCAL.map((c) => [c.id, c]))
  const paramsDestino = DESTINOS_LOCAL[estado.destino]
  const numVivos = Math.max(1, estado.tripulacion.filter((t) => t.vivo).length)

  let masaCompSecos = 0
  let masaComb = 0
  let ispBase = 0
  let genBruta = 0
  let consTotal = 110.0
  let capWh = 600.0
  let diasPersonaO2 = 4.0
  let diasPersonaComida = 4.0
  let tasaKbps = 0
  let ventanas = 0
  let probEnlace = 0
  let tieneRobot = false

  for (const cid of estado.componentes_instalados) {
    const comp = catalogo[cid]
    if (!comp) continue
    masaCompSecos += comp.masa_kg
    if (comp.categoria === 'motor') {
      masaComb += comp.combustible_kg
      ispBase = Math.max(ispBase, comp.isp_s)
    }
    genBruta += comp.generacion_w
    consTotal += comp.consumo_w
    capWh += comp.capacidad_wh
    diasPersonaO2 += comp.dias_o2
    diasPersonaComida += comp.dias_comida
    if (comp.categoria === 'antena') {
      tasaKbps = Math.max(tasaKbps, comp.tasa_kbps)
      ventanas = Math.max(ventanas, comp.ventanas_dia)
      const pen = comp.alcance_km < paramsDestino.distancia_km ? 0.45 : 1.0
      probEnlace = Math.max(probEnlace, round(comp.probabilidad_enlace * pen, 2))
    }
    if (comp.categoria === 'robot') {
      tieneRobot = true
    }
  }

  const masaSeca = round(
    estado.masa_estructura_base_kg + masaCompSecos + numVivos * MASA_POR_TRIPULANTE_KG,
    2,
  )
  const masaTotal = round(masaSeca + masaComb, 2)
  const rendMotor = estado.rendimiento_subsistemas.motor ?? 1.0
  const ispEf = round(ispBase * Math.max(0.1, rendMotor), 2)
  const dvTotal =
    ispEf > 0 && masaComb > 0 && masaTotal > masaSeca
      ? round(ispEf * G0_MS2 * Math.log(masaTotal / masaSeca), 1)
      : 0

  estado.masa_seca_kg = masaSeca
  estado.masa_combustible_kg = masaComb
  estado.masa_total_kg = masaTotal
  estado.isp_efectivo_s = ispEf

  if (estado.etapa_actual <= 4) {
    estado.delta_v_inicial_ms = dvTotal
    estado.delta_v_disponible_ms = dvTotal
  }

  const factorTray = estado.perfil_trayectoria === 'rapida' ? 1.18 : 1.0
  const factorVent = estado.ventana_lanzamiento === 'secundaria' ? 1.1 : 1.0
  estado.delta_v_requerido_total_ms = round(
    paramsDestino.delta_v_total_minimo_ms * factorTray * factorVent,
    1,
  )
  estado.dias_transito =
    estado.perfil_trayectoria === 'rapida'
      ? paramsDestino.dias_transito_rapido
      : paramsDestino.dias_transito_estandar
  estado.dias_en_destino = paramsDestino.dias_operacion_destino

  const rendEnergia = estado.rendimiento_subsistemas.energia ?? 1.0
  let genEf = round(genBruta * Math.max(0.1, rendEnergia), 1)
  consTotal = round(consTotal, 1)
  if (estado.dificultad === 'facil') {
    capWh = round(capWh + 800, 1)
    genEf = round(genEf + 80, 1)
  }
  const balW = round(genEf - consTotal, 1)
  const demandaEclipse = Math.max(50, consTotal * paramsDestino.fraccion_eclipse)

  estado.generacion_w = genEf
  estado.consumo_w = consTotal
  estado.balance_potencia_w = balW
  estado.bateria_capacidad_wh = round(capWh, 1)
  if (estado.etapa_actual <= 4) {
    estado.bateria_actual_wh = estado.bateria_capacidad_wh
  } else {
    estado.bateria_actual_wh = Math.min(estado.bateria_actual_wh, estado.bateria_capacidad_wh)
  }
  estado.autonomia_eclipse_h = round(capWh / demandaEclipse, 1)

  if (estado.etapa_actual <= 4) {
    const rendEclss = estado.rendimiento_subsistemas.soporte_vital ?? 1.0
    const o2D = round((diasPersonaO2 * Math.max(0.2, rendEclss)) / numVivos, 1)
    const comidaD = round(diasPersonaComida / numVivos, 1)
    const bonusVital = estado.dificultad === 'facil' ? 6.0 : 0.0
    estado.o2_dias_disponibles = round(o2D + bonusVital, 1)
    estado.comida_dias_disponibles = round(comidaD + bonusVital, 1)
  }

  const rendAntena = estado.rendimiento_subsistemas.antena ?? 1.0
  estado.tasa_transmision_kbps = round(tasaKbps * rendAntena, 1)
  estado.ventanas_comm_por_dia = ventanas
  if (estado.etapa_actual <= 4) {
    const bonusVentanas = estado.dificultad === 'facil' ? 3 : 0
    estado.ventanas_comm_restantes = ventanas * Math.max(1, estado.dias_en_destino) + bonusVentanas
  }
  estado.probabilidad_enlace_comm = round(
    Math.min(0.99, probEnlace * rendAntena + (estado.dificultad === 'facil' ? 0.08 : 0.0)),
    2,
  )
  estado.tiene_robot_autonomo = tieneRobot

  const [velEq, calEq] = calcularRendimientoTripulacion(estado.tripulacion)
  estado.velocidad_tarea_equipo = velEq
  estado.calidad_tarea_equipo = calEq

  return estado
}

function capturarInstantanea(estado: EstadoMision): Record<string, [string, number, string]> {
  const catalogo = Object.fromEntries(COMPONENTES_LOCAL.map((c) => [c.id, c]))
  const tasaDatosDia = estado.componentes_instalados.reduce(
    (acc, cid) => acc + (catalogo[cid]?.datos_gb_dia ?? 0),
    0,
  )
  const datosVisibles = round(estado.datos_generados_gb + tasaDatosDia, 2)
  return {
    masa_total_kg: ['Masa total', round(estado.masa_total_kg, 1), 'kg'],
    balance_potencia_w: ['Balance de energía', round(estado.balance_potencia_w, 1), 'W'],
    bateria_actual_wh: ['Reserva de batería', round(estado.bateria_actual_wh, 1), 'Wh'],
    delta_v_disponible_ms: ['Delta-v disponible', round(estado.delta_v_disponible_ms, 1), 'm/s'],
    datos_flujo_gb: ['Volumen/flujo de datos', datosVisibles, 'GB'],
    presupuesto_restante_usd: [
      'Presupuesto restante',
      round(estado.presupuesto_restante_usd, 0),
      'USD',
    ],
    o2_dias_disponibles: [
      'Autonomía soporte vital',
      round(estado.o2_dias_disponibles, 1),
      'días',
    ],
    puntos_ciencia_generados: [
      'Potencial/puntos ciencia',
      round(estado.puntos_ciencia_generados, 1),
      'pts',
    ],
  }
}

function construirCambios(
  antes: Record<string, [string, number, string]>,
  despues: Record<string, [string, number, string]>,
): CambioVariable[] {
  const troncales = new Set([
    'masa_total_kg',
    'balance_potencia_w',
    'delta_v_disponible_ms',
    'datos_flujo_gb',
    'presupuesto_restante_usd',
  ])
  const cambios: CambioVariable[] = []
  for (const [clave, [etiqueta, valAnt, unidad]] of Object.entries(antes)) {
    const valNue = despues[clave][1]
    const delta = round(valNue - valAnt, 2)
    if (troncales.has(clave) || Math.abs(delta) > 0.01) {
      cambios.push({
        variable: clave,
        etiqueta,
        valor_anterior: valAnt,
        valor_nuevo: valNue,
        delta,
        unidad,
      })
    }
  }
  return cambios
}

export function getCatalogLocal(): CatalogoCompleto {
  return {
    destinos: Object.values(DESTINOS_LOCAL),
    acuerdos_financiacion: ACUERDOS_LOCAL,
    componentes: COMPONENTES_LOCAL,
    candidatos_tripulacion: CANDIDATOS_LOCAL,
    etapas: NOMBRES_ETAPAS_LOCAL,
    masa_lanzamiento_max_kg: 1300.0,
  }
}

export function createMissionLocal(payload: {
  nombre_mision: string
  destino: DestinoId
  dificultad?: DificultadId
  acuerdo_financiacion_id: string
  especialidad_director: string
}): EstadoMision {
  const dificultad: DificultadId = payload.dificultad ?? 'facil'
  const acuerdo =
    ACUERDOS_LOCAL.find((a) => a.id === payload.acuerdo_financiacion_id) ?? ACUERDOS_LOCAL[1]
  const factorPres = dificultad === 'facil' ? 1.35 : dificultad === 'dificil' ? 0.9 : 1.0
  const presupuestoInicial = Math.round(acuerdo.presupuesto_usd * factorPres)
  const masaMaxLanzador = dificultad === 'facil' ? 1480.0 : dificultad === 'dificil' ? 1280.0 : 1300.0

  const director: TripulanteEstado = {
    id: 'crew_director',
    nombre: 'Cmdt. Director (Jugador)',
    rol: 'Director de Misión',
    especialidad: (payload.especialidad_director as TripulanteEstado['especialidad']) || 'comando',
    experiencia: 4,
    salario_usd: 0,
    estado_animo: 'sol',
    salud: 100,
    salud_mental: 100,
    vivo: true,
    es_jugador: true,
    habitacion_actual: 'cabina_mando',
    biografia_corta:
      'Responsable de la planificación, diseño, ejecución y retorno de la expedición.',
  }

  const componentesBase = [
    'motor_biprop_estandar',
    'energia_solar_estandar',
    'antena_parabolica_x',
    'eclss_reciclaje_estandar',
  ]
  const catalogoMap = Object.fromEntries(COMPONENTES_LOCAL.map((c) => [c.id, c]))
  const costoBase = componentesBase.reduce((acc, cid) => acc + (catalogoMap[cid]?.costo_usd ?? 0), 0)

  if (dificultad === 'facil') {
    componentesBase.push('inst_espectrometro')
  }

  const randomHex = Math.random().toString(16).substring(2, 10)
  const estado: EstadoMision = {
    id: `zenit-${randomHex}`,
    nombre_mision: payload.nombre_mision || 'Expedición Zenit-1',
    etapa_actual: 1,
    nombre_etapa: NOMBRES_ETAPAS_LOCAL['1'],
    estado_juego: 'en_curso',
    causa_fallo: null,
    dificultad,
    destino: payload.destino,
    acuerdo_financiacion_id: acuerdo.id,
    presupuesto_inicial_usd: presupuestoInicial,
    presupuesto_restante_usd: round(presupuestoInicial - costoBase, 2),
    masa_estructura_base_kg: 155.0,
    masa_lanzamiento_max_kg: masaMaxLanzador,
    masa_seca_kg: 0,
    masa_combustible_kg: 0,
    masa_total_kg: 0,
    componentes_instalados: componentesBase,
    rendimiento_subsistemas: {
      motor: 1.0,
      energia: 1.0,
      antena: 1.0,
      soporte_vital: 1.0,
      cientifico: 1.0,
      robot: 1.0,
    },
    isp_efectivo_s: 0,
    delta_v_inicial_ms: 0,
    delta_v_disponible_ms: 0,
    delta_v_requerido_total_ms: 0,
    perfil_trayectoria: 'estandar',
    ventana_lanzamiento: 'optima',
    dias_transito: 1,
    dias_en_destino: 4,
    dias_transcurridos: 0,
    generacion_w: 0,
    consumo_w: 0,
    balance_potencia_w: 0,
    bateria_capacidad_wh: 0,
    bateria_actual_wh: 0,
    autonomia_eclipse_h: 0,
    tripulacion: [director],
    tiene_robot_autonomo: false,
    o2_dias_disponibles: 16,
    comida_dias_disponibles: 16,
    velocidad_tarea_equipo: 1,
    calidad_tarea_equipo: 1,
    puntos_ciencia_generados: 0,
    calidad_datos_promedio: 100,
    datos_generados_gb: 0,
    datos_transmitidos_gb: 0,
    tasa_transmision_kbps: 2000,
    ventanas_comm_por_dia: 3,
    ventanas_comm_restantes: 12,
    probabilidad_enlace_comm: 0.86,
    habitacion_jugador: 'cabina_mando',
    habitaciones_2d: construirHabitacionesIniciales(),
    eventos_activos: [],
    historial_eventos: [],
    alertas_no_cuantificadas: [],
    banderas_penalizacion_diferida: [],
    ultimos_cambios_variables: [],
    bitacora_decisiones: [
      `Misión '${payload.nombre_mision}' iniciada en modo '${dificultad.toUpperCase()}' con destino ${payload.destino} y presupuesto ${presupuestoInicial.toLocaleString()} USD.`,
    ],
  }

  recalcularSubsistemasLocal(estado)
  return guardarMisionEnCacheLocal(estado)
}

export function sendDecisionLocal(
  missionId: string,
  payload: { stage: number; decision: string; params: Record<string, unknown> },
): DecisionResponse {
  const estado = obtenerMisionDeCacheLocal(missionId)
  if (!estado) {
    throw new Error(`Misión '${missionId}' no encontrada.`)
  }

  const catalogo = Object.fromEntries(COMPONENTES_LOCAL.map((c) => [c.id, c]))
  const antes = capturarInstantanea(estado)
  const { decision, params } = payload
  let resumen = 'Decisión procesada.'

  if (
    estado.etapa_actual < 6 &&
    ['operacion_cientifica', 'usar_ventana_comm', 'tarea_tripulacion', 'mover_habitacion'].includes(
      decision,
    )
  ) {
    return {
      allowed: false,
      status: 'fail',
      policy_triggered: 'Restricción Operativa Pre-Vuelo',
      message:
        'La nave aún está en Tierra. Las operaciones en cabina 2D, recolección científica y transmisión se habilitan tras el lanzamiento.',
      warnings: [],
      affected_variables: [],
      new_state_summary: {},
      mission_state: estado,
    }
  }

  if (decision === 'seleccionar_destino') {
    estado.destino = (params.destino as DestinoId) || 'OTB'
    recalcularSubsistemasLocal(estado)
    resumen = `Destino fijado en ${DESTINOS_LOCAL[estado.destino].nombre}.`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'seleccionar_financiacion') {
    const acuerdoId = String(params.acuerdo_id || 'estandar')
    const acuerdo = ACUERDOS_LOCAL.find((a) => a.id === acuerdoId) ?? ACUERDOS_LOCAL[1]
    const factorPres =
      estado.dificultad === 'facil' ? 1.35 : estado.dificultad === 'dificil' ? 0.9 : 1.0
    const nuevoInicial = Math.round(acuerdo.presupuesto_usd * factorPres)
    const gastoAcumulado = estado.presupuesto_inicial_usd - estado.presupuesto_restante_usd
    estado.acuerdo_financiacion_id = acuerdo.id
    estado.presupuesto_inicial_usd = nuevoInicial
    estado.presupuesto_restante_usd = Math.max(0, round(nuevoInicial - gastoAcumulado, 2))
    recalcularSubsistemasLocal(estado)
    resumen = `Acuerdo '${acuerdo.nombre}' firmado. Presupuesto global ajustado: ${nuevoInicial.toLocaleString()} USD.`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'negociar_presupuesto') {
    const bono = Math.max(0, Math.min(50000, Math.round(Number(params.bono_usd) || 0)))
    estado.presupuesto_inicial_usd = round(estado.presupuesto_inicial_usd + bono, 2)
    estado.presupuesto_restante_usd = round(estado.presupuesto_restante_usd + bono, 2)
    recalcularSubsistemasLocal(estado)
    resumen = `Negociación con el comité de gatos: +${bono.toLocaleString()} USD al presupuesto.`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'instalar_componente') {
    const compId = String(params.componente_id || '')
    const comp = catalogo[compId]
    if (!comp) {
      throw new Error(`Componente '${compId}' no existe.`)
    }
    let reembolso = 0
    if (['motor', 'energia', 'antena', 'soporte_vital'].includes(comp.categoria)) {
      for (const cid of estado.componentes_instalados) {
        if (catalogo[cid]?.categoria === comp.categoria) {
          reembolso += catalogo[cid].costo_usd
        }
      }
    }
    const costoNeto = comp.costo_usd - reembolso
    if (costoNeto > estado.presupuesto_restante_usd) {
      return {
        allowed: false,
        status: 'fail',
        policy_triggered: 'Límite Duro de Presupuesto Global',
        message: `Presupuesto insuficiente para instalar '${comp.nombre}'. Coste neto: ${costoNeto.toLocaleString()} USD | Disponible: ${estado.presupuesto_restante_usd.toLocaleString()} USD.`,
        warnings: [],
        affected_variables: [],
        new_state_summary: {},
        mission_state: estado,
      }
    }
    if (['motor', 'energia', 'antena', 'soporte_vital'].includes(comp.categoria)) {
      estado.componentes_instalados = estado.componentes_instalados.filter(
        (cid) => catalogo[cid]?.categoria !== comp.categoria,
      )
      estado.presupuesto_restante_usd += reembolso
    }
    if (!estado.componentes_instalados.includes(compId)) {
      estado.componentes_instalados.push(compId)
    }
    estado.presupuesto_restante_usd = round(estado.presupuesto_restante_usd - comp.costo_usd, 2)
    recalcularSubsistemasLocal(estado)
    resumen = `Instalado en nave: ${comp.nombre} (-${comp.costo_usd.toLocaleString()} USD, +${comp.masa_kg} kg).`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'remover_componente') {
    const compId = String(params.componente_id || '')
    const comp = catalogo[compId]
    if (comp && estado.componentes_instalados.includes(compId)) {
      estado.componentes_instalados = estado.componentes_instalados.filter((id) => id !== compId)
      estado.presupuesto_restante_usd = round(estado.presupuesto_restante_usd + comp.costo_usd, 2)
      recalcularSubsistemasLocal(estado)
      resumen = `Desinstalado: ${comp.nombre} (+${comp.costo_usd.toLocaleString()} USD reembolsados).`
      estado.bitacora_decisiones.push(resumen)
    }
  } else if (decision === 'contratar_tripulante') {
    const crewId = String(params.crew_id || '')
    const cand = CANDIDATOS_LOCAL.find((c) => c.id === crewId)
    if (!cand) {
      throw new Error(`Tripulante '${crewId}' no encontrado.`)
    }
    if (estado.tripulacion.length >= 4) {
      return {
        allowed: false,
        status: 'fail',
        policy_triggered: 'Capacidad de Cabina (1 a 4 Tripulantes)',
        message: 'La nave admite un máximo de 4 tripulantes.',
        warnings: [],
        affected_variables: [],
        new_state_summary: {},
        mission_state: estado,
      }
    }
    if (cand.salario_usd > estado.presupuesto_restante_usd) {
      return {
        allowed: false,
        status: 'fail',
        policy_triggered: 'Límite Duro de Presupuesto Global',
        message: `Presupuesto insuficiente para contratar a ${cand.nombre} (${cand.salario_usd.toLocaleString()} USD).`,
        warnings: [],
        affected_variables: [],
        new_state_summary: {},
        mission_state: estado,
      }
    }
    estado.tripulacion.push(JSON.parse(JSON.stringify(cand)) as TripulanteEstado)
    estado.presupuesto_restante_usd = round(estado.presupuesto_restante_usd - cand.salario_usd, 2)
    recalcularSubsistemasLocal(estado)
    resumen = `Contratado: ${cand.nombre} (${cand.rol}, Salario: -${cand.salario_usd.toLocaleString()} USD).`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'remover_tripulante') {
    const crewId = String(params.crew_id || '')
    const miembro = estado.tripulacion.find((t) => t.id === crewId && !t.es_jugador)
    if (miembro) {
      estado.tripulacion = estado.tripulacion.filter((t) => t.id !== crewId)
      estado.presupuesto_restante_usd = round(
        estado.presupuesto_restante_usd + miembro.salario_usd,
        2,
      )
      recalcularSubsistemasLocal(estado)
      resumen = `Relevado de la misión: ${miembro.nombre} (+${miembro.salario_usd.toLocaleString()} USD).`
      estado.bitacora_decisiones.push(resumen)
    }
  } else if (decision === 'configurar_trayectoria') {
    estado.perfil_trayectoria =
      (params.perfil_trayectoria as 'estandar' | 'rapida') || 'estandar'
    estado.ventana_lanzamiento =
      (params.ventana_lanzamiento as 'optima' | 'secundaria') || 'optima'
    recalcularSubsistemasLocal(estado)
    resumen = `Trayectoria '${estado.perfil_trayectoria}' en ventana '${estado.ventana_lanzamiento}' fijada. Delta-v requerido estimado: ${estado.delta_v_requerido_total_ms} m/s.`
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'mover_habitacion') {
    const destHab = String(params.habitacion_id || 'cabina_mando')
    const room = estado.habitaciones_2d.find((h) => h.id === destHab)
    if (room) {
      estado.habitacion_jugador = destHab
      for (const t of estado.tripulacion) {
        if (t.es_jugador) t.habitacion_actual = destHab
      }
      resumen = `[Tecla E] Compuerta abierta. Te has desplazado a: ${room.nombre}.`
    }
  } else if (decision === 'operacion_cientifica') {
    const instrumentos = estado.componentes_instalados
      .map((cid) => catalogo[cid])
      .filter((c): c is ComponenteCatalogo => !!c && (c.categoria === 'instrumento' || c.categoria === 'robot'))

    if (instrumentos.length === 0) {
      const [, calBase] = calcularRendimientoTripulacion(estado.tripulacion, null, true)
      const rendSub = estado.rendimiento_subsistemas.cientifico ?? 1.0
      const pts = round(14.0 * calBase * rendSub, 1)
      const gb = round(2.4 * rendSub, 2)
      estado.puntos_ciencia_generados = round(estado.puntos_ciencia_generados + pts, 1)
      estado.datos_generados_gb = round(estado.datos_generados_gb + gb, 2)
      estado.bateria_actual_wh = round(Math.max(0, estado.bateria_actual_wh - 90), 1)
      estado.calidad_datos_promedio = round(Math.min(100, estado.calidad_tarea_equipo * 88), 1)
      resumen = `Campaña ejecutada con Sensores Base del Laboratorio: +${pts} pts de ciencia, +${gb} GB en memoria (-90 Wh). Ahora puedes transmitirlos a Tierra con la antena.`
    } else {
      let ptsTot = 0
      let gbTot = 0
      let whTot = 0
      for (const inst of instrumentos) {
        const [, calEsp] = calcularRendimientoTripulacion(
          estado.tripulacion,
          inst.especialidad_requerida,
          false,
        )
        const rendSub =
          estado.rendimiento_subsistemas[inst.categoria === 'robot' ? 'robot' : 'cientifico'] ?? 1.0
        ptsTot += round(inst.puntos_ciencia_base * calEsp * rendSub, 1)
        gbTot += round(
          inst.datos_gb_dia * Math.max(1, Math.floor(estado.dias_en_destino / 2)) * rendSub,
          2,
        )
        whTot += inst.consumo_w * 1.2
      }
      estado.puntos_ciencia_generados = round(estado.puntos_ciencia_generados + ptsTot, 1)
      estado.datos_generados_gb = round(estado.datos_generados_gb + gbTot, 2)
      estado.bateria_actual_wh = round(Math.max(0, estado.bateria_actual_wh - whTot), 1)
      estado.calidad_datos_promedio = round(Math.min(100, estado.calidad_tarea_equipo * 92), 1)
      resumen = `Operación en Laboratorio completada: +${ptsTot.toFixed(1)} pts de ciencia, +${gbTot.toFixed(1)} GB de datos almacenados (-${Math.round(whTot)} Wh). ¡Listos para transmitir a Tierra!`
    }
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'tarea_tripulacion') {
    const subtipo = String(params.subtipo || 'mantenimiento_general')
    const [vel, cal] = calcularRendimientoTripulacion(
      estado.tripulacion,
      subtipo === 'mantenimiento_general' ? 'ingenieria' : 'medicina',
      true,
    )
    if (subtipo === 'mantenimiento_general') {
      for (const k of Object.keys(estado.rendimiento_subsistemas)) {
        estado.rendimiento_subsistemas[k] = round(
          Math.min(1.0, estado.rendimiento_subsistemas[k] + 0.12 * cal),
          2,
        )
      }
      estado.bateria_actual_wh = round(Math.max(0, estado.bateria_actual_wh - 110), 1)
      recalcularSubsistemasLocal(estado)
      resumen = `Mantenimiento preventivo ejecutado (Velocidad equipo: ${vel}x, Calidad: ${cal}x). Subsistemas recalibrados.`
    } else {
      for (const m of estado.tripulacion) {
        if (m.vivo) {
          m.estado_animo = 'sol'
          m.salud_mental = Math.min(100, round(m.salud_mental + 18 * cal, 1))
        }
      }
      recalcularSubsistemasLocal(estado)
      resumen = 'Sesión de estabilización y descanso en Módulo de Vida: la tripulación recupera estado Sol.'
    }
    estado.bitacora_decisiones.push(resumen)
  } else if (decision === 'usar_ventana_comm') {
    const pendientes = round(Math.max(0, estado.datos_generados_gb - estado.datos_transmitidos_gb), 2)
    if (estado.datos_generados_gb <= 0) {
      resumen =
        "Aún no tienes datos científicos en memoria (0 GB). Paso 1: Pulsa '🔬 Recolectar Datos en Laboratorio' antes de transmitir."
    } else if (pendientes <= 0) {
      resumen = `¡Todos los datos en memoria (${estado.datos_transmitidos_gb} GB) ya fueron transmitidos a Tierra! No se consumió ninguna ventana adicional.`
    } else if (estado.ventanas_comm_restantes <= 0) {
      resumen = 'No quedan ventanas de comunicación disponibles en esta órbita/ciclo.'
    } else {
      estado.ventanas_comm_restantes -= 1
      estado.bateria_actual_wh = round(Math.max(0, estado.bateria_actual_wh - 100), 1)
      const gbPorVentana = Math.max(
        2.5,
        round((estado.tasa_transmision_kbps / 1000) * estado.probabilidad_enlace_comm * 2.2, 2),
      )
      const txAhora = round(Math.min(pendientes, gbPorVentana), 2)
      estado.datos_transmitidos_gb = round(estado.datos_transmitidos_gb + txAhora, 2)
      resumen = `📡 Transmisión exitosa a Tierra: +${txAhora} GB enviados (Total transmitido: ${estado.datos_transmitidos_gb} / ${estado.datos_generados_gb} GB · Quedan ${estado.ventanas_comm_restantes} ventanas).`
      estado.bitacora_decisiones.push(resumen)
    }
  }

  const despues = capturarInstantanea(estado)
  const cambios = construirCambios(antes, despues)
  estado.ultimos_cambios_variables = cambios
  guardarMisionEnCacheLocal(estado)

  return {
    allowed: true,
    status: 'allowed',
    policy_triggered: 'nominal',
    message: resumen,
    warnings: [],
    affected_variables: cambios,
    new_state_summary: {},
    mission_state: estado,
  }
}

export function advanceStageLocal(missionId: string): DecisionResponse {
  const estado = obtenerMisionDeCacheLocal(missionId)
  if (!estado) {
    throw new Error(`Misión '${missionId}' no encontrada.`)
  }
  const antes = capturarInstantanea(estado)
  const paramsDestino = DESTINOS_LOCAL[estado.destino]
  let narrativa = ''

  if (estado.etapa_actual === 5) {
    if (estado.masa_total_kg > estado.masa_lanzamiento_max_kg) {
      estado.estado_juego = 'fallo_inmediato'
      estado.causa_fallo = `Sobrecarga estructural: masa de nave (${estado.masa_total_kg} kg) superó masa máxima de lanzamiento (${estado.masa_lanzamiento_max_kg} kg).`
      estado.etapa_actual = 10
      estado.nombre_etapa = NOMBRES_ETAPAS_LOCAL['10']
      const cambios = construirCambios(antes, capturarInstantanea(estado))
      guardarMisionEnCacheLocal(estado)
      return {
        allowed: false,
        status: 'fail',
        policy_triggered: 'Límite Físico Crítico de Masa al Lanzamiento',
        message: estado.causa_fallo,
        warnings: [],
        affected_variables: cambios,
        new_state_summary: {},
        mission_state: estado,
      }
    }
    estado.delta_v_disponible_ms = round(
      estado.delta_v_disponible_ms - paramsDestino.delta_v_lanzamiento_ms,
      1,
    )
    narrativa = `Ascenso orbital completado. Se consumieron ${paramsDestino.delta_v_lanzamiento_ms} m/s de Delta-v.`
  } else if (estado.etapa_actual === 6) {
    const dvTransito = round(
      paramsDestino.delta_v_transito_insercion_ms *
        (estado.perfil_trayectoria === 'rapida' ? 1.18 : 1.0),
      1,
    )
    estado.delta_v_disponible_ms = round(Math.max(0, estado.delta_v_disponible_ms - dvTransito), 1)
    estado.dias_transcurridos += estado.dias_transito
    estado.o2_dias_disponibles = round(
      Math.max(0, estado.o2_dias_disponibles - estado.dias_transito),
      1,
    )
    estado.comida_dias_disponibles = round(
      Math.max(0, estado.comida_dias_disponibles - estado.dias_transito),
      1,
    )
    const tarifa = estado.dificultad === 'facil' ? 600 : 1100
    const costoOps = estado.dias_transito * tarifa
    estado.presupuesto_restante_usd = round(
      Math.max(0, estado.presupuesto_restante_usd - costoOps),
      2,
    )
    narrativa = `Tránsito a ${estado.destino} completado en ${estado.dias_transito} día(s). Coste de seguimiento: -${costoOps.toLocaleString()} USD.`
  } else if ([7, 8, 9].includes(estado.etapa_actual)) {
    estado.dias_transcurridos += 1
    const consVital = estado.dificultad === 'facil' ? 0.7 : 1.0
    estado.o2_dias_disponibles = round(Math.max(0, estado.o2_dias_disponibles - consVital), 1)
    estado.comida_dias_disponibles = round(
      Math.max(0, estado.comida_dias_disponibles - consVital),
      1,
    )
    const costoDiario = estado.dificultad === 'facil' ? 450 : 850
    estado.presupuesto_restante_usd = round(
      Math.max(0, estado.presupuesto_restante_usd - costoDiario),
      2,
    )
  }

  if (estado.etapa_actual < 10) {
    estado.etapa_actual += 1
    estado.nombre_etapa = NOMBRES_ETAPAS_LOCAL[String(estado.etapa_actual)]
    if (estado.etapa_actual === 10) {
      const dvRetorno = paramsDestino.delta_v_retorno_ms
      if (estado.delta_v_disponible_ms >= dvRetorno) {
        estado.delta_v_disponible_ms = round(estado.delta_v_disponible_ms - dvRetorno, 1)
        estado.estado_juego = 'completada'
        narrativa =
          'Maniobra de retorno completada. Entrando al despacho del Director para la evaluación final.'
      } else {
        estado.estado_juego = 'completada'
        if (!estado.banderas_penalizacion_diferida.includes('sin_deltav_retorno')) {
          estado.banderas_penalizacion_diferida.push('sin_deltav_retorno')
        }
        narrativa = `ALERTA CRÍTICA DE RETORNO: Delta-v restante (${estado.delta_v_disponible_ms} m/s) insuficiente para el retorno nominal (${dvRetorno} m/s).`
      }
    }
  }

  if (estado.etapa_actual === 6 && estado.eventos_activos.length === 0) {
    const ev: EventoMision = {
      id: `ev-transito-${estado.etapa_actual}`,
      titulo: 'Oscilación en Bus de Regulación Térmica',
      mensaje_alerta:
        'La consola secundaria muestra una fluctuación de voltaje en el circuito de potencia. No se reporta el porcentaje exacto de degradación.',
      subsistema_afectado: 'energia',
      severidad_visual: 'incertidumbre',
      etapa_origen: estado.etapa_actual,
      contexto: 'transito',
      resuelto: false,
      diagnosticado_por_tierra: false,
      diagnostico_detallado:
        'Deriva en regulador de paneles (-12% de rendimiento si no se recalibra).',
      opciones: [
        {
          id: 'reparar_bordo',
          texto: 'Asignar a la tripulación para recalibrar en Sala de Sistemas',
          tipo_accion: 'reparacion_tripulacion',
          costo_presupuesto_usd: 0,
          costo_energia_wh: 120,
          costo_delta_v_ms: 0,
          consume_ventana_comm: false,
          especialidad_ideal: 'ingenieria',
        },
        {
          id: 'parche_tierra',
          texto: 'Contratar tele-ingeniería de soporte desde Tierra',
          tipo_accion: 'soporte_tierra_presupuesto',
          costo_presupuesto_usd: 4500,
          costo_energia_wh: 40,
          costo_delta_v_ms: 0,
          consume_ventana_comm: false,
          especialidad_ideal: null,
        },
      ],
      resultado_narrativo: null,
    }
    estado.eventos_activos.push(ev)
  }

  recalcularSubsistemasLocal(estado)
  if (!narrativa) {
    narrativa = `Avanzando a ${estado.nombre_etapa}.`
  }
  estado.bitacora_decisiones.push(narrativa)
  const cambios = construirCambios(antes, capturarInstantanea(estado))
  estado.ultimos_cambios_variables = cambios
  guardarMisionEnCacheLocal(estado)

  return {
    allowed: true,
    status: 'allowed',
    policy_triggered: 'nominal',
    message: narrativa,
    warnings: [],
    affected_variables: cambios,
    new_state_summary: {},
    mission_state: estado,
  }
}

export function resolveEventLocal(
  missionId: string,
  eventId: string,
  optionId: string,
): DecisionResponse {
  const estado = obtenerMisionDeCacheLocal(missionId)
  if (!estado) {
    throw new Error(`Misión '${missionId}' no encontrada.`)
  }
  const antes = capturarInstantanea(estado)
  const ev = estado.eventos_activos.find((e) => e.id === eventId)
  if (!ev) {
    return {
      allowed: true,
      status: 'allowed',
      policy_triggered: 'nominal',
      message: 'Evento ya resuelto.',
      warnings: [],
      affected_variables: [],
      new_state_summary: {},
      mission_state: estado,
    }
  }
  const opt = ev.opciones.find((o) => o.id === optionId) ?? ev.opciones[0]
  estado.presupuesto_restante_usd = round(
    Math.max(0, estado.presupuesto_restante_usd - opt.costo_presupuesto_usd),
    2,
  )
  estado.bateria_actual_wh = round(Math.max(0, estado.bateria_actual_wh - opt.costo_energia_wh), 1)
  estado.delta_v_disponible_ms = round(
    Math.max(0, estado.delta_v_disponible_ms - opt.costo_delta_v_ms),
    1,
  )
  if (opt.consume_ventana_comm) {
    estado.ventanas_comm_restantes = Math.max(0, estado.ventanas_comm_restantes - 1)
  }
  ev.resuelto = true
  const msg = `Resuelto mediante '${opt.texto}'.`
  ev.resultado_narrativo = msg
  estado.eventos_activos = estado.eventos_activos.filter((e) => e.id !== eventId)
  estado.historial_eventos.push(ev)
  recalcularSubsistemasLocal(estado)
  const cambios = construirCambios(antes, capturarInstantanea(estado))
  estado.ultimos_cambios_variables = cambios
  guardarMisionEnCacheLocal(estado)

  return {
    allowed: true,
    status: 'allowed',
    policy_triggered: 'nominal',
    message: msg,
    warnings: [],
    affected_variables: cambios,
    new_state_summary: {},
    mission_state: estado,
  }
}

export function getReportLocal(missionId: string): InformeFinal {
  const estado = obtenerMisionDeCacheLocal(missionId)
  if (!estado) {
    throw new Error(`Misión '${missionId}' no encontrada.`)
  }
  const acuerdo =
    ACUERDOS_LOCAL.find((a) => a.id === estado.acuerdo_financiacion_id) ?? ACUERDOS_LOCAL[1]
  const metaCiencia = acuerdo.exigencia_ciencia
  const vivos = estado.tripulacion.filter((t) => t.vivo)
  const totalCrew = Math.max(1, estado.tripulacion.length)
  const sinRetorno = estado.banderas_penalizacion_diferida.includes('sin_deltav_retorno')
  const falloTemprano =
    estado.estado_juego === 'fallo_inmediato' || estado.estado_juego === 'perdida_mision'
  const huboBajas = vivos.length < totalCrew || sinRetorno || falloTemprano

  const scoreCiencia = falloTemprano
    ? 0
    : round(Math.min(100, (estado.puntos_ciencia_generados / Math.max(10, metaCiencia)) * 100), 1)
  const ratioTx =
    estado.datos_generados_gb <= 0
      ? 0
      : Math.min(1, estado.datos_transmitidos_gb / estado.datos_generados_gb)
  const scoreDatos = round(ratioTx * (estado.calidad_datos_promedio / 100) * 100, 1)
  const scoreSupervivencia =
    falloTemprano || vivos.length === 0 ? 0 : sinRetorno ? 20 : round((vivos.length / totalCrew) * 100, 1)
  const ratioPres = Math.max(
    0,
    estado.presupuesto_restante_usd / Math.max(1, estado.presupuesto_inicial_usd),
  )
  const scorePresupuesto = round(Math.min(100, 45 + ratioPres * 110), 1)
  const scoreTiempo = falloTemprano ? 0 : 90
  const scoreNave = falloTemprano ? 0 : 95
  const scoreRetorno =
    falloTemprano || sinRetorno
      ? 0
      : round(Math.min(100, 65 + (estado.delta_v_disponible_ms / 400) * 35), 1)

  const puntuacionGlobal = round(
    scoreCiencia * 0.2 +
      scoreDatos * 0.2 +
      scoreSupervivencia * 0.25 +
      scorePresupuesto * 0.1 +
      scoreTiempo * 0.05 +
      scoreNave * 0.1 +
      scoreRetorno * 0.1,
    1,
  )

  let finalId = 'supervivencia_mision_parcial'
  let numeroFinal = 2
  let tituloFinal = 'Final 2 — Supervivencia con Misión Parcial'
  let subtituloFinal =
    'La tripulación regresó sana y salva, pero el retorno de datos científicos quedó incompleto.'
  let dialogoApertura =
    'El jefe revisa las gráficas en su terminal ámbar: «La nave regresó de una pieza y tu gente está en casa, que es lo primero. Sin embargo, desde el punto de vista científico nos quedamos cortos respecto a lo prometido.»'
  let fraseDespedida =
    '«Traer a la tripulación con vida siempre es una victoria; lograr además toda la ciencia exige afinar el cuello de botella entre instrumentos y comunicaciones.»'

  if (falloTemprano || (huboBajas && estado.datos_transmitidos_gb <= 0.2)) {
    finalId = 'fallo_total'
    numeroFinal = 5
    tituloFinal = 'Final 5 — Fallo Total de la Misión'
    subtituloFinal = 'Pérdida de vehículo y ausencia de retorno científico.'
    dialogoApertura = `La oficina está a oscuras. El jefe te mira en silencio: «${estado.causa_fallo || 'Perdimos la misión por completo.'}»`
    fraseDespedida =
      '«La física no negocia con el optimismo, Director. Cuando vuelva a leer una ficha técnica, recuerde que cada número tiene peso.»'
  } else if (scoreCiencia >= 70 && scoreDatos >= 65 && !huboBajas) {
    finalId = 'exito_cientifico_pleno'
    numeroFinal = 1
    tituloFinal = 'Final 1 — Éxito Científico Pleno'
    subtituloFinal = 'Objetivos científicos cumplidos, datos transmitidos y retorno íntegro.'
    dialogoApertura =
      'El jefe se levanta al verte entrar en la oficina y extiende el informe encuadernado: «Un trabajo de ingeniería impecable. Equilibraste masa, impulso específico, energía y ancho de banda sin comprometer ni una sola vida.»'
    fraseDespedida =
      '«Así se construye la exploración espacial real: leyendo cada parámetro y respetando cada restricción. Enhorabuena, Director.»'
  }

  const dimensiones: DimensionEvaluacion[] = [
    {
      id: 'ciencia',
      nombre: 'Objetivos Científicos',
      puntuacion: scoreCiencia,
      estado_etiqueta: scoreCiencia >= 75 ? 'Óptimo' : scoreCiencia >= 40 ? 'Parcial' : 'Deficiente',
      comentario_jefe: `Generaste ${estado.puntos_ciencia_generados.toFixed(1)} puntos de ciencia frente a una meta de ${metaCiencia}.`,
      explicacion_tecnica:
        'Depende de los instrumentos instalados, la presencia del especialista afín y su estado de concentración.',
    },
    {
      id: 'supervivencia',
      nombre: 'Supervivencia y Tripulación',
      puntuacion: scoreSupervivencia,
      estado_etiqueta: !huboBajas ? 'Íntegra' : 'Pérdida Crítica',
      comentario_jefe: !huboBajas
        ? `Regresaron ${vivos.length}/${totalCrew} tripulantes en condiciones de retorno nominal.`
        : 'No lograste traer de vuelta a toda la tripulación a salvo.',
      explicacion_tecnica:
        'Condicionada por la autonomía de soporte vital (O2/comida), el aislamiento y el Delta-v de retorno.',
    },
    {
      id: 'datos',
      nombre: 'Calidad y Transmisión de Datos',
      puntuacion: scoreDatos,
      estado_etiqueta: scoreDatos >= 70 ? 'Fluida' : 'Cuello de Botella',
      comentario_jefe: `Transmitiste ${estado.datos_transmitidos_gb.toFixed(1)} GB de ${estado.datos_generados_gb.toFixed(1)} GB generados.`,
      explicacion_tecnica:
        'Los datos sin transmitir en las ventanas de comunicación fijas no puntúan.',
    },
    {
      id: 'presupuesto',
      nombre: 'Gestión de Presupuesto Global',
      puntuacion: scorePresupuesto,
      estado_etiqueta: estado.presupuesto_restante_usd >= 5000 ? 'Solvente' : 'Al Límite',
      comentario_jefe: `Saldo final: ${estado.presupuesto_restante_usd.toLocaleString()} USD de ${estado.presupuesto_inicial_usd.toLocaleString()} USD iniciales.`,
      explicacion_tecnica:
        'Límite duro que integra compra de componentes, salarios y gastos de contingencia en tiempo real.',
    },
    {
      id: 'tiempo',
      nombre: 'Tiempo y Planificación Orbital',
      puntuacion: scoreTiempo,
      estado_etiqueta: 'En Ventana',
      comentario_jefe: `Duración operativa acumulada: ${estado.dias_transcurridos} día(s) en ${estado.destino}.`,
      explicacion_tecnica:
        'La elección entre transferencia estándar o rápida intercambia tiempo por Delta-v.',
    },
    {
      id: 'nave',
      nombre: 'Estado Final de la Nave',
      puntuacion: scoreNave,
      estado_etiqueta: 'Nominal',
      comentario_jefe: `Integridad media de subsistemas al cierre: ${scoreNave}%.`,
      explicacion_tecnica:
        'Refleja los fallos aleatorios ocurridos y la eficacia de las reparaciones ejecutadas.',
    },
    {
      id: 'retorno',
      nombre: 'Capacidad de Retorno',
      puntuacion: scoreRetorno,
      estado_etiqueta: scoreRetorno > 0 ? 'Asegurado' : 'Fallido',
      comentario_jefe: `Delta-v remanente tras reentrada/retorno: ${estado.delta_v_disponible_ms.toFixed(1)} m/s.`,
      explicacion_tecnica:
        'Calculado por la ecuación de Tsiolkovsky descontando ascenso, inyección y retorno.',
    },
  ]

  return {
    mission_id: estado.id,
    final_id: finalId,
    numero_final: numeroFinal,
    titulo_final: tituloFinal,
    subtitulo_final: subtituloFinal,
    puntuacion_global: puntuacionGlobal,
    hubo_muertes_tripulacion: huboBajas,
    silencio_previo_segundos: huboBajas ? 4 : 0,
    dialogo_jefe_apertura: dialogoApertura,
    monologo_cuarta_pared: huboBajas
      ? '«Los números de las fichas técnicas estaban ahí desde el minuto uno: sabías cuánto pesaba la nave, cuánto oxígeno llevabas y cuántos metros por segundo exigía volver a casa. Tú pulsaste el botón de lanzamiento asumiendo ese riesgo.»'
      : null,
    dimensiones,
    trazabilidad_causal: estado.bitacora_decisiones.slice(-6),
    recomendaciones_ingenieria: [
      'Asegúrate de recolectar ciencia en el Laboratorio (Paso 1) y transmitirla en la Sala de Sistemas (Paso 2) antes del retorno.',
    ],
    frase_despedida: fraseDespedida,
    resumen_tecnico_datos: {
      destino: estado.destino,
      masa_final_kg: estado.masa_total_kg,
      delta_v_restante_ms: estado.delta_v_disponible_ms,
    },
  }
}
