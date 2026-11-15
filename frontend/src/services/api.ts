/**
 * Cliente tipado para la API REST de Zenit (Simulador narrativo de misiones espaciales).
 */

export type DestinoId = 'OTB' | 'LUNA'
export type DificultadId = 'facil' | 'normal' | 'dificil'
export type EstadoAnimo = 'sol' | 'nube' | 'lluvia'
export type CategoriaComponente =
  | 'motor'
  | 'energia'
  | 'antena'
  | 'soporte_vital'
  | 'instrumento'
  | 'robot'

export interface ComponenteCatalogo {
  id: string
  nombre: string
  categoria: CategoriaComponente
  costo_usd: number
  masa_kg: number
  consumo_w: number
  generacion_w: number
  capacidad_wh: number
  isp_s: number
  combustible_kg: number
  alcance_km: number
  tasa_kbps: number
  ventanas_dia: number
  probabilidad_enlace: number
  dias_o2: number
  dias_comida: number
  puntos_ciencia_base: number
  datos_gb_dia: number
  especialidad_requerida: string | null
  fiabilidad_nominal: number
  slot_visual: string
  descripcion_ficha: string
}

export interface TripulanteEstado {
  id: string
  nombre: string
  rol: string
  especialidad: 'ingenieria' | 'geologia' | 'astrobiologia' | 'medicina' | 'comando'
  experiencia: number
  salario_usd: number
  estado_animo: EstadoAnimo
  salud: number
  salud_mental: number
  vivo: boolean
  es_jugador: boolean
  habitacion_actual: string
  biografia_corta: string
}

export interface ParametrosDestino {
  id: DestinoId
  nombre: string
  distancia_km: number
  delta_v_lanzamiento_ms: number
  delta_v_transito_insercion_ms: number
  delta_v_retorno_ms: number
  delta_v_total_minimo_ms: number
  dias_transito_estandar: number
  dias_transito_rapido: number
  dias_operacion_destino: number
  fraccion_eclipse: number
  entorno_riesgo: string
  descripcion: string
}

export interface AcuerdoFinanciacion {
  id: string
  nombre: string
  presupuesto_usd: number
  exigencia_ciencia: number
  descripcion: string
}

export interface CambioVariable {
  variable: string
  etiqueta: string
  valor_anterior: number
  valor_nuevo: number
  delta: number
  unidad: string
}

export interface OpcionEvento {
  id: string
  texto: string
  tipo_accion: string
  costo_presupuesto_usd: number
  costo_energia_wh: number
  costo_delta_v_ms: number
  consume_ventana_comm: boolean
  especialidad_ideal: string | null
}

export interface EventoMision {
  id: string
  titulo: string
  mensaje_alerta: string
  subsistema_afectado: string
  severidad_visual: 'normal' | 'advertencia' | 'grave' | 'incertidumbre'
  etapa_origen: number
  contexto: 'transito' | 'orbita_destino'
  resuelto: boolean
  diagnosticado_por_tierra: boolean
  diagnostico_detallado: string | null
  opciones: OpcionEvento[]
  resultado_narrativo: string | null
}

export interface EstadoHabitacion2D {
  id: string
  nombre: string
  orden: number
  puerta_izquierda: string | null
  puerta_derecha: string | null
  sistema_principal: string
  alerta_activa: boolean
  color_alerta: 'cyan' | 'green' | 'orange' | 'red' | 'lilac'
  mensaje_terminal: string
  requiere_visita_para_datos: boolean
}

export interface EstadoMision {
  id: string
  nombre_mision: string
  etapa_actual: number
  nombre_etapa: string
  estado_juego: 'en_curso' | 'completada' | 'fallo_inmediato' | 'perdida_mision'
  causa_fallo: string | null
  dificultad: DificultadId
  destino: DestinoId
  acuerdo_financiacion_id: string
  presupuesto_inicial_usd: number
  presupuesto_restante_usd: number
  masa_estructura_base_kg: number
  masa_lanzamiento_max_kg: number
  masa_seca_kg: number
  masa_combustible_kg: number
  masa_total_kg: number
  componentes_instalados: string[]
  rendimiento_subsistemas: Record<string, number>
  isp_efectivo_s: number
  delta_v_inicial_ms: number
  delta_v_disponible_ms: number
  delta_v_requerido_total_ms: number
  perfil_trayectoria: 'estandar' | 'rapida'
  ventana_lanzamiento: 'optima' | 'secundaria'
  dias_transito: number
  dias_en_destino: number
  dias_transcurridos: number
  generacion_w: number
  consumo_w: number
  balance_potencia_w: number
  bateria_capacidad_wh: number
  bateria_actual_wh: number
  autonomia_eclipse_h: number
  tripulacion: TripulanteEstado[]
  tiene_robot_autonomo: boolean
  o2_dias_disponibles: number
  comida_dias_disponibles: number
  velocidad_tarea_equipo: number
  calidad_tarea_equipo: number
  puntos_ciencia_generados: number
  calidad_datos_promedio: number
  datos_generados_gb: number
  datos_transmitidos_gb: number
  tasa_transmision_kbps: number
  ventanas_comm_por_dia: number
  ventanas_comm_restantes: number
  probabilidad_enlace_comm: number
  habitacion_jugador: string
  habitaciones_2d: EstadoHabitacion2D[]
  eventos_activos: EventoMision[]
  historial_eventos: EventoMision[]
  alertas_no_cuantificadas: string[]
  banderas_penalizacion_diferida: string[]
  ultimos_cambios_variables: CambioVariable[]
  bitacora_decisiones: string[]
}

export interface DecisionResponse {
  allowed: boolean
  status: 'allowed' | 'warning' | 'fail'
  policy_triggered: string
  message: string
  warnings: string[]
  affected_variables: CambioVariable[]
  new_state_summary: Record<string, unknown>
  mission_state: EstadoMision
}

export interface DimensionEvaluacion {
  id: string
  nombre: string
  puntuacion: number
  estado_etiqueta: string
  comentario_jefe: string
  explicacion_tecnica: string
}

export interface InformeFinal {
  mission_id: string
  final_id: string
  numero_final: number
  titulo_final: string
  subtitulo_final: string
  puntuacion_global: number
  hubo_muertes_tripulacion: boolean
  silencio_previo_segundos: number
  dialogo_jefe_apertura: string
  monologo_cuarta_pared: string | null
  dimensiones: DimensionEvaluacion[]
  trazabilidad_causal: string[]
  recomendaciones_ingenieria: string[]
  frase_despedida: string
  resumen_tecnico_datos: Record<string, unknown>
}

export interface CatalogoCompleto {
  destinos: ParametrosDestino[]
  acuerdos_financiacion: AcuerdoFinanciacion[]
  componentes: ComponenteCatalogo[]
  candidatos_tripulacion: TripulanteEstado[]
  etapas: Record<string, string>
  masa_lanzamiento_max_kg: number
}

import {
  advanceStageLocal,
  createMissionLocal,
  getCatalogLocal,
  getReportLocal,
  guardarMisionEnCacheLocal,
  obtenerMisionDeCacheLocal,
  resolveEventLocal,
  sendDecisionLocal,
} from './localSimulationFallback'

const API_BASES = [
  '/api/v1',
  'http://127.0.0.1:8010/api/v1',
  'http://127.0.0.1:8000/api/v1',
  'http://localhost:8010/api/v1',
  'http://localhost:8000/api/v1',
]

let preferredApiBase = API_BASES[0]

async function requestJson<T>(endpointPath: string, options?: RequestInit): Promise<T> {
  const isLocalHost =
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

  const basesActivas = isLocalHost ? API_BASES : ['/api/v1']
  const candidateBases = [
    preferredApiBase,
    ...basesActivas.filter((b) => b !== preferredApiBase),
  ]

  let lastError: Error | null = null

  for (const base of candidateBases) {
    const url = `${base}${endpointPath}`
    try {
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (response.ok) {
        preferredApiBase = base
        return (await response.json()) as T
      }
      // Si es un error de validación de negocio (400/422), no reintentar en otro puerto
      if (response.status === 400 || response.status === 422) {
        const errText = await response.text()
        throw new Error(`Error HTTP ${response.status}: ${errText}`)
      }
      const errText = await response.text()
      lastError = new Error(`Error HTTP ${response.status}: ${errText}`)
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err))
      // Si fue un error 400/422 lanzado explícitamente arriba, propagar de inmediato
      if (
        lastError.message.startsWith('Error HTTP 400') ||
        lastError.message.startsWith('Error HTTP 422')
      ) {
        throw lastError
      }
    }
  }

  throw lastError ?? new Error('No se pudo conectar con el servidor de Zenit.')
}

export const zenitApi = {
  async getCatalog(): Promise<CatalogoCompleto> {
    try {
      return await requestJson<CatalogoCompleto>('/catalog')
    } catch {
      return getCatalogLocal()
    }
  },

  async createMission(payload: {
    nombre_mision: string
    destino: DestinoId
    dificultad?: DificultadId
    acuerdo_financiacion_id: string
    especialidad_director: string
  }): Promise<EstadoMision> {
    try {
      const estado = await requestJson<EstadoMision>('/missions', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      return guardarMisionEnCacheLocal(estado)
    } catch {
      return createMissionLocal(payload)
    }
  },

  async getMission(missionId: string): Promise<EstadoMision> {
    try {
      const estado = await requestJson<EstadoMision>(`/missions/${missionId}`)
      return guardarMisionEnCacheLocal(estado)
    } catch (err) {
      const cached = obtenerMisionDeCacheLocal(missionId)
      if (cached) return cached
      throw err
    }
  },

  async sendDecision(
    missionId: string,
    payload: { stage: number; decision: string; params: Record<string, unknown> },
  ): Promise<DecisionResponse> {
    try {
      const resp = await requestJson<DecisionResponse>(`/missions/${missionId}/decisions`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      guardarMisionEnCacheLocal(resp.mission_state)
      return resp
    } catch {
      return sendDecisionLocal(missionId, payload)
    }
  },

  async advanceStage(missionId: string): Promise<DecisionResponse> {
    try {
      const resp = await requestJson<DecisionResponse>(`/missions/${missionId}/advance`, {
        method: 'POST',
      })
      guardarMisionEnCacheLocal(resp.mission_state)
      return resp
    } catch {
      return advanceStageLocal(missionId)
    }
  },

  async resolveEvent(
    missionId: string,
    eventId: string,
    optionId: string,
  ): Promise<DecisionResponse> {
    try {
      const resp = await requestJson<DecisionResponse>(
        `/missions/${missionId}/events/${eventId}/resolve`,
        {
          method: 'POST',
          body: JSON.stringify({ option_id: optionId }),
        },
      )
      guardarMisionEnCacheLocal(resp.mission_state)
      return resp
    } catch {
      return resolveEventLocal(missionId, eventId, optionId)
    }
  },

  async getReport(missionId: string): Promise<InformeFinal> {
    try {
      return await requestJson<InformeFinal>(`/missions/${missionId}/report`)
    } catch {
      return getReportLocal(missionId)
    }
  },
}
