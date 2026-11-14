"""Esquemas Pydantic para el estado de misión, catálogo, decisiones e informe final."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class DestinoId(str, Enum):
    """Destinos seleccionables en el MVP."""

    OTB = "OTB"
    LUNA = "LUNA"


class DificultadId(str, Enum):
    """Niveles de dificultad para equilibrar el aprendizaje y el margen operativo."""

    FACIL = "facil"
    NORMAL = "normal"
    DIFICIL = "dificil"


class EstadoAnimo(str, Enum):
    """Estados de ánimo visibles sobre cada tripulante."""

    SOL = "sol"
    NUBE = "nube"
    LLUVIA = "lluvia"


class CategoriaComponente(str, Enum):
    """Categorías del catálogo de componentes de la nave."""

    MOTOR = "motor"
    ENERGIA = "energia"
    ANTENA = "antena"
    SOPORTE_VITAL = "soporte_vital"
    INSTRUMENTO = "instrumento"
    ROBOT = "robot"


class PoliticaConsecuencia(str, Enum):
    """Política de consecuencias según el tipo de restricción."""

    FALLO_INMEDIATO = "fallo_inmediato"
    DEGRADACION_PROGRESIVA = "degradacion_progresiva"
    PENALIZACION_DIFERIDA = "penalizacion_diferida"
    NOMINAL = "nominal"


class ComponenteCatalogo(BaseModel):
    """Ficha técnica pública de un componente en el catálogo (sin valores ocultos)."""

    id: str
    nombre: str
    categoria: CategoriaComponente
    costo_usd: float = Field(ge=0, description="Coste financiero de adquisición en USD")
    masa_kg: float = Field(ge=0, description="Masa añadida a la nave en kg")
    consumo_w: float = Field(
        default=0.0, ge=0, description="Consumo eléctrico nominal en W"
    )
    generacion_w: float = Field(
        default=0.0, ge=0, description="Generación eléctrica nominal en W"
    )
    capacidad_wh: float = Field(
        default=0.0, ge=0, description="Capacidad de batería en Wh"
    )
    isp_s: float = Field(
        default=0.0, ge=0, description="Impulso específico en segundos (motores)"
    )
    combustible_kg: float = Field(
        default=0.0, ge=0, description="Masa de propelente incluido en kg"
    )
    alcance_km: float = Field(
        default=0.0, ge=0, description="Alcance de telecomunicaciones en km"
    )
    tasa_kbps: float = Field(
        default=0.0, ge=0, description="Tasa de transmisión en kbps"
    )
    ventanas_dia: int = Field(
        default=0, ge=0, description="Ventanas de comunicación fijas por día/órbita"
    )
    probabilidad_enlace: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probabilidad de disponibilidad por ventana",
    )
    dias_o2: float = Field(
        default=0.0, ge=0, description="Suministro de oxígeno en días-persona"
    )
    dias_comida: float = Field(
        default=0.0, ge=0, description="Suministro de agua y raciones en días-persona"
    )
    puntos_ciencia_base: float = Field(
        default=0.0, ge=0, description="Potencial científico base"
    )
    datos_gb_dia: float = Field(
        default=0.0, ge=0, description="Volumen de datos generados en GB/día"
    )
    especialidad_requerida: str | None = Field(
        default=None, description="Especialidad que habilita su operación óptima"
    )
    fiabilidad_nominal: float = Field(
        default=0.92,
        ge=0.0,
        le=1.0,
        description="Fiabilidad publicada frente a fallos aleatorios",
    )
    slot_visual: str = Field(
        description="Identificador de representación visual en el esquemático y sala 2D"
    )
    descripcion_ficha: str = Field(
        description="Descripción técnica visible en el catálogo"
    )


class TripulanteEstado(BaseModel):
    """Perfil y estado determinista de un miembro de la tripulación."""

    id: str
    nombre: str
    rol: str
    especialidad: Literal[
        "ingenieria", "geologia", "astrobiologia", "medicina", "comando"
    ]
    experiencia: int = Field(
        ge=1, le=5, description="Nivel de experiencia laboral (1 a 5)"
    )
    salario_usd: float = Field(
        ge=0, description="Coste salarial descontado del presupuesto"
    )
    estado_animo: EstadoAnimo = EstadoAnimo.SOL
    salud: float = Field(default=100.0, ge=0.0, le=100.0)
    salud_mental: float = Field(default=100.0, ge=0.0, le=100.0)
    vivo: bool = True
    es_jugador: bool = False
    habitacion_actual: str = "cabina_mando"
    biografia_corta: str = ""


class ParametrosDestino(BaseModel):
    """Parámetros físicos y operativos del destino seleccionado."""

    id: DestinoId
    nombre: str
    distancia_km: float
    delta_v_lanzamiento_ms: float
    delta_v_transito_insercion_ms: float
    delta_v_retorno_ms: float
    delta_v_total_minimo_ms: float
    dias_transito_estandar: int
    dias_transito_rapido: int
    dias_operacion_destino: int
    fraccion_eclipse: float
    entorno_riesgo: str
    descripcion: str


class CambioVariable(BaseModel):
    """Fila de la tabla de visibilidad de consecuencias mostrada tras cada decisión."""

    variable: str
    etiqueta: str
    valor_anterior: float
    valor_nuevo: float
    delta: float
    unidad: str


class OpcionEvento(BaseModel):
    """Opción de respuesta ante una anomalía, fallo o emergencia."""

    id: str
    texto: str
    tipo_accion: Literal[
        "reparacion_tripulacion",
        "consultar_tierra",
        "maniobra_energia",
        "soporte_financiero_tierra",
        "robot_autonomo",
        "asumir_degradacion",
    ]
    costo_presupuesto_usd: float = 0.0
    costo_energia_wh: float = 0.0
    costo_delta_v_ms: float = 0.0
    consume_ventana_comm: bool = False
    especialidad_ideal: str | None = None


class EventoMision(BaseModel):
    """Evento contextual o fallo de componente (comunicado sin cuantificar)."""

    id: str
    titulo: str
    mensaje_alerta: str
    subsistema_afectado: str
    severidad_visual: Literal["normal", "advertencia", "grave", "incertidumbre"] = (
        "advertencia"
    )
    etapa_origen: int
    contexto: Literal["transito", "orbita_destino"] = "orbita_destino"
    resuelto: bool = False
    diagnosticado_por_tierra: bool = False
    diagnostico_detallado: str | None = None
    impacto_oculto_rendimiento: float = 0.15
    opciones: list[OpcionEvento] = Field(default_factory=list)
    resultado_narrativo: str | None = None


class EstadoHabitacion2D(BaseModel):
    """Representación de cada sala contigua en la vista 2D del destino (tecla E)."""

    id: str
    nombre: str
    orden: int
    puerta_izquierda: str | None = None
    puerta_derecha: str | None = None
    sistema_principal: str
    alerta_activa: bool = False
    color_alerta: Literal["cyan", "green", "orange", "red", "lilac"] = "cyan"
    mensaje_terminal: str
    requiere_visita_para_datos: bool = True


class EstadoMision(BaseModel):
    """Fuente de verdad completa del estado de la misión."""

    id: str
    nombre_mision: str = "Expedición Zenit-1"
    etapa_actual: int = Field(default=1, ge=1, le=10)
    nombre_etapa: str = "1. Definición de la misión"
    estado_juego: Literal[
        "en_curso", "completada", "fallo_inmediato", "perdida_mision"
    ] = "en_curso"
    causa_fallo: str | None = None

    # Etapa 1 y 2: Destino, Dificultad y Financiación
    dificultad: DificultadId = DificultadId.NORMAL
    destino: DestinoId = DestinoId.OTB
    acuerdo_financiacion_id: str = "estandar"
    presupuesto_inicial_usd: float = 120000.0
    presupuesto_restante_usd: float = 120000.0

    # Etapa 3: Diseño de nave (Masas y Componentes)
    masa_estructura_base_kg: float = 155.0
    masa_lanzamiento_max_kg: float = 1300.0
    masa_seca_kg: float = 405.0
    masa_combustible_kg: float = 795.0
    masa_total_kg: float = 1200.0
    componentes_instalados: list[str] = Field(default_factory=list)
    rendimiento_subsistemas: dict[str, float] = Field(
        default_factory=lambda: {
            "motor": 1.0,
            "energia": 1.0,
            "antena": 1.0,
            "soporte_vital": 1.0,
            "cientifico": 1.0,
            "robot": 1.0,
        }
    )

    # Propulsión y Mecánica Orbital (Etapa 4, 5, 6, 10)
    isp_efectivo_s: float = 0.0
    delta_v_inicial_ms: float = 0.0
    delta_v_disponible_ms: float = 0.0
    delta_v_requerido_total_ms: float = 2400.0
    perfil_trayectoria: Literal["estandar", "rapida"] = "estandar"
    ventana_lanzamiento: Literal["optima", "secundaria"] = "optima"
    dias_transito: int = 2
    dias_en_destino: int = 4
    dias_transcurridos: int = 0

    # Energía (Fidelidad Real)
    generacion_w: float = 0.0
    consumo_w: float = 120.0
    balance_potencia_w: float = -120.0
    bateria_capacidad_wh: float = 1200.0
    bateria_actual_wh: float = 1200.0
    autonomia_eclipse_h: float = 10.0

    # Soporte Vital Simplificado y Tripulación (Etapa 3 y 8)
    tripulacion: list[TripulanteEstado] = Field(default_factory=list)
    tiene_robot_autonomo: bool = False
    o2_dias_disponibles: float = 0.0
    comida_dias_disponibles: float = 0.0
    velocidad_tarea_equipo: float = 1.0
    calidad_tarea_equipo: float = 1.0

    # Ciencia y Telecomunicaciones (Etapa 7 y 9)
    puntos_ciencia_generados: float = 0.0
    calidad_datos_promedio: float = 100.0
    datos_generados_gb: float = 0.0
    datos_transmitidos_gb: float = 0.0
    tasa_transmision_kbps: float = 0.0
    ventanas_comm_por_dia: int = 0
    ventanas_comm_restantes: int = 0
    probabilidad_enlace_comm: float = 0.0

    # Vista 2D en el Destino (Interacción tecla E)
    habitacion_jugador: str = "cabina_mando"
    habitaciones_2d: list[EstadoHabitacion2D] = Field(default_factory=list)

    # Eventos, Alertas y Registro Causal
    eventos_activos: list[EventoMision] = Field(default_factory=list)
    historial_eventos: list[EventoMision] = Field(default_factory=list)
    alertas_no_cuantificadas: list[str] = Field(default_factory=list)
    banderas_penalizacion_diferida: list[str] = Field(default_factory=list)
    ultimos_cambios_variables: list[CambioVariable] = Field(default_factory=list)
    bitacora_decisiones: list[str] = Field(default_factory=list)


class CrearMisionRequest(BaseModel):
    """Petición para crear una nueva misión."""

    nombre_mision: str = "Expedición Zenit-1"
    destino: DestinoId = DestinoId.OTB
    dificultad: DificultadId = DificultadId.NORMAL
    acuerdo_financiacion_id: str = "estandar"
    especialidad_director: Literal[
        "ingenieria", "geologia", "astrobiologia", "medicina", "comando"
    ] = "comando"


class DecisionRequest(BaseModel):
    """Petición para ejecutar una decisión en una etapa."""

    stage: int = Field(ge=1, le=10, description="Etapa de la misión (1 a 10)")
    decision: str = Field(description="Tipo de decisión a ejecutar")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Parámetros de la decisión"
    )


class DecisionResponse(BaseModel):
    """Respuesta del motor tras validar y aplicar consecuencias de una decisión."""

    allowed: bool
    status: Literal["allowed", "warning", "fail"]
    policy_triggered: PoliticaConsecuencia = PoliticaConsecuencia.NOMINAL
    message: str
    warnings: list[str] = Field(default_factory=list)
    affected_variables: list[CambioVariable] = Field(default_factory=list)
    new_state_summary: dict[str, Any] = Field(default_factory=dict)
    mission_state: EstadoMision


class ResolverEventoRequest(BaseModel):
    """Petición para resolver un evento activo con una opción."""

    option_id: str
    crew_id: str | None = None


class DimensionEvaluacion(BaseModel):
    """Puntuación y comentario de una dimensión en el informe final."""

    id: str
    nombre: str
    puntuacion: float = Field(ge=0.0, le=100.0)
    estado_etiqueta: str
    comentario_jefe: str
    explicacion_tecnica: str


class InformeFinal(BaseModel):
    """Informe final multidimensional y escena del despacho del jefe."""

    mission_id: str
    final_id: Literal[
        "exito_cientifico_pleno",
        "supervivencia_mision_parcial",
        "retorno_emergencia",
        "perdida_tripulacion_datos_recuperados",
        "fallo_total",
    ]
    numero_final: int = Field(ge=1, le=5)
    titulo_final: str
    subtitulo_final: str
    puntuacion_global: float
    hubo_muertes_tripulacion: bool
    silencio_previo_segundos: int = 0
    dialogo_jefe_apertura: str
    monologo_cuarta_pared: str | None = None
    dimensiones: list[DimensionEvaluacion]
    trazabilidad_causal: list[str]
    recomendaciones_ingenieria: list[str]
    frase_despedida: str
    resumen_tecnico_datos: dict[str, Any]
