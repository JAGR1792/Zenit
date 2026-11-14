<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import BossReportScene from '../components/BossReportScene.vue'
import DestinationRooms2D from '../components/DestinationRooms2D.vue'
import PixelSprite from '../components/PixelSprite.vue'
import ShipSchematic from '../components/ShipSchematic.vue'
import {
  zenitApi,
  type CatalogoCompleto,
  type EstadoMision,
  type InformeFinal,
} from '../services/api'

const catalog = ref<CatalogoCompleto | null>(null)
const mission = ref<EstadoMision | null>(null)
const finalReport = ref<InformeFinal | null>(null)
const statusMessage = ref<string>('Inicializando consola de misión Zenit...')
const lastStatusType = ref<'allowed' | 'warning' | 'fail'>('allowed')
const loading = ref<boolean>(false)

// Modos del visor izquierdo y sub-pestañas de la Etapa 3 para eliminar el scroll excesivo
const activeViewportTab = ref<'rooms2d' | 'schematic' | 'telemetry'>('rooms2d')
const stage3SubTab = ref<'hardware' | 'crew'>('hardware')
const activeCategory = ref<string>('instrumento')

const categories = [
  { id: 'motor', label: 'Motores' },
  { id: 'energia', label: 'Energía' },
  { id: 'antena', label: 'Antenas' },
  { id: 'soporte_vital', label: 'Soporte Vital' },
  { id: 'instrumento', label: 'Ciencia' },
  { id: 'robot', label: 'Robots' },
]

const filteredComponents = computed(() => {
  if (!catalog.value) return []
  return catalog.value.componentes.filter((c) => c.categoria === activeCategory.value)
})

const currentDestinationInfo = computed(() => {
  if (!catalog.value || !mission.value) return null
  return catalog.value.destinos.find((d) => d.id === mission.value?.destino) ?? null
})

const nonZeroDeltas = computed(() => {
  if (!mission.value) return []
  return mission.value.ultimos_cambios_variables.filter((c) => Math.abs(c.delta) > 0.01)
})

// Cambiar automáticamente al visor más útil según la etapa, permitiendo siempre cambio manual
watch(
  () => mission.value?.etapa_actual,
  (etapa) => {
    if (etapa === 3 || etapa === 4 || etapa === 5) {
      activeViewportTab.value = 'schematic'
    } else if (etapa && etapa >= 6) {
      activeViewportTab.value = 'rooms2d'
    }
  },
)

async function startNewMission(): Promise<void> {
  loading.value = true
  finalReport.value = null
  try {
    if (!catalog.value) {
      catalog.value = await zenitApi.getCatalog()
    }
    mission.value = await zenitApi.createMission({
      nombre_mision: 'Expedición Zenit-1',
      destino: 'OTB',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })
    activeViewportTab.value = 'rooms2d'
    statusMessage.value =
      'Misión activa. Usa [←/→] y [E] en la cubierta 2D o toma decisiones en el panel derecho.'
    lastStatusType.value = 'allowed'
  } catch (err) {
    statusMessage.value = `Error al conectar con el backend: ${(err as Error).message}`
    lastStatusType.value = 'fail'
  } finally {
    loading.value = false
  }
}

async function executeDecision(decision: string, params: Record<string, unknown>): Promise<void> {
  if (!mission.value) return
  loading.value = true
  try {
    const resp = await zenitApi.sendDecision(mission.value.id, {
      stage: mission.value.etapa_actual,
      decision,
      params,
    })
    mission.value = resp.mission_state
    statusMessage.value = resp.message
    lastStatusType.value = resp.status
  } catch (err) {
    statusMessage.value = (err as Error).message
    lastStatusType.value = 'fail'
  } finally {
    loading.value = false
  }
}

async function advanceStage(): Promise<void> {
  if (!mission.value) return
  loading.value = true
  try {
    const resp = await zenitApi.advanceStage(mission.value.id)
    mission.value = resp.mission_state
    statusMessage.value = resp.message
    lastStatusType.value = resp.status
    if (
      mission.value.etapa_actual === 10 ||
      mission.value.estado_juego === 'fallo_inmediato' ||
      mission.value.estado_juego === 'perdida_mision'
    ) {
      finalReport.value = await zenitApi.getReport(mission.value.id)
    }
  } catch (err) {
    statusMessage.value = (err as Error).message
    lastStatusType.value = 'fail'
  } finally {
    loading.value = false
  }
}

async function handleResolveEvent(eventId: string, optionId: string): Promise<void> {
  if (!mission.value) return
  loading.value = true
  try {
    const resp = await zenitApi.resolveEvent(mission.value.id, eventId, optionId)
    mission.value = resp.mission_state
    statusMessage.value = resp.message
    lastStatusType.value = resp.status
  } catch (err) {
    statusMessage.value = (err as Error).message
    lastStatusType.value = 'fail'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void startNewMission()
})
</script>

<template>
  <div class="cockpit-layout">
    <!-- ======================================================================= -->
    <!-- 1. CINTA SUPERIOR DE TELEMETRÍA Y PROGRESO DE ETAPAS (FIJA Y COMPACTA)  -->
    <!-- ======================================================================= -->
    <header class="top-ribbon">
      <div class="brand-cluster">
        <span class="brand-mark">ZENIT</span>
        <div class="brand-titles">
          <span class="brand-main">DIRECCIÓN DE MISIÓN ESPACIAL</span>
          <span v-if="mission" class="brand-stage-sub">{{ mission.nombre_etapa }}</span>
        </div>
      </div>

      <!-- Línea de tiempo de las 10 etapas -->
      <nav v-if="mission" class="timeline-10" aria-label="Progreso de etapas de la misión">
        <div
          v-for="step in 10"
          :key="step"
          class="timeline-node"
          :class="{
            done: step < mission.etapa_actual,
            current: step === mission.etapa_actual,
          }"
          :title="`Etapa ${step}`"
        >
          {{ step }}
        </div>
      </nav>

      <!-- Telemetría clave en tiempo real (tabular-nums, sin advertir desastres) -->
      <div v-if="mission" class="telemetry-pills">
        <div class="tpill">
          <span class="tpill-label">PRESUPUESTO</span>
          <strong class="tpill-val" style="color: var(--gold)">
            ${{ mission.presupuesto_restante_usd.toLocaleString() }}
          </strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">MASA (MÁX {{ mission.masa_lanzamiento_max_kg }})</span>
          <strong class="tpill-val">{{ mission.masa_total_kg }} kg</strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">DELTA-V</span>
          <strong class="tpill-val" style="color: var(--cyan)">
            {{ mission.delta_v_disponible_ms }} m/s
          </strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">POTENCIA</span>
          <strong class="tpill-val">
            {{
              mission.balance_potencia_w >= 0
                ? `+${mission.balance_potencia_w}`
                : mission.balance_potencia_w
            }}
            W
          </strong>
        </div>
      </div>
    </header>

    <!-- ======================================================================= -->
    <!-- ESCENA FINAL (ETAPA 10 O FALLO DE MISIÓN): DESPACHO DEL JEFE            -->
    <!-- ======================================================================= -->
    <main v-if="finalReport" class="final-report-viewport">
      <BossReportScene :report="finalReport" @restart="startNewMission" />
    </main>

    <!-- ======================================================================= -->
    <!-- ESTACIÓN DE TRABAJO DE DOBLE PANEL (SIN SCROLL DE PÁGINA COMPLETA)      -->
    <!-- ======================================================================= -->
    <main v-else-if="mission && catalog" class="split-workstation">
      <!-- PANEL IZQUIERDO (58%): VISOR INTERACTIVO MULTIMODO + CHIPS DE IMPACTO -->
      <section class="left-viewport-column">
        <!-- Conmutador de Vista Principal -->
        <div class="viewport-switcher">
          <button
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'rooms2d' }"
            @click="activeViewportTab = 'rooms2d'"
          >
            🎮 Cubierta 2D Pixel Art [Tecla E]
          </button>
          <button
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'schematic' }"
            @click="activeViewportTab = 'schematic'"
          >
            🚀 Esquemático de Nave y Dotación
          </button>
          <button
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'telemetry' }"
            @click="activeViewportTab = 'telemetry'"
          >
            📊 Tabla Completa de Variables
          </button>
        </div>

        <!-- Contenido del Visor Activo -->
        <div class="viewport-stage-body">
          <DestinationRooms2D
            v-if="activeViewportTab === 'rooms2d'"
            :mission="mission"
            @move-room="(roomId) => executeDecision('mover_habitacion', { habitacion_id: roomId })"
            @run-science="executeDecision('operacion_cientifica', {})"
            @run-crew-task="(subtipo) => executeDecision('tarea_tripulacion', { subtipo })"
            @use-comm-window="executeDecision('usar_ventana_comm', {})"
          />

          <ShipSchematic
            v-else-if="activeViewportTab === 'schematic'"
            :mission="mission"
            :catalog="catalog.componentes"
          />

          <!-- Vista 3: Tabla Completa de Variables Explícitas -->
          <div v-else class="panel-box full-telemetry-sheet">
            <div class="sheet-header">
              <span class="sheet-title">MATRIZ DE VARIABLES INTERDEPENDIENTES DE LA NAVE</span>
              <p class="sheet-sub">
                Valores explícitos en tiempo real. El simulador muestra las magnitudes físicas sin
                predecir ni bloquear configuraciones deficientes.
              </p>
            </div>
            <table class="clean-table">
              <thead>
                <tr>
                  <th>Variable de Sistema</th>
                  <th>Valor Actual</th>
                  <th>Parámetro de Referencia</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Presupuesto Financiero Global</td>
                  <td style="color: var(--gold)">
                    ${{ mission.presupuesto_restante_usd.toLocaleString() }} USD
                  </td>
                  <td>Inicial: ${{ mission.presupuesto_inicial_usd.toLocaleString() }} USD</td>
                </tr>
                <tr>
                  <td>Masa Total al Lanzamiento (m₀)</td>
                  <td>{{ mission.masa_total_kg }} kg</td>
                  <td>Capacidad máxima fija: {{ mission.masa_lanzamiento_max_kg }} kg</td>
                </tr>
                <tr>
                  <td>Masa Seca / Propelente</td>
                  <td>{{ mission.masa_seca_kg }} kg / {{ mission.masa_combustible_kg }} kg</td>
                  <td>Impulso específico (Isp): {{ mission.isp_efectivo_s }} s</td>
                </tr>
                <tr>
                  <td>Delta-v Disponible</td>
                  <td style="color: var(--cyan)">{{ mission.delta_v_disponible_ms }} m/s</td>
                  <td>Requerido estimado ({{ mission.destino }}): {{ mission.delta_v_requerido_total_ms }} m/s</td>
                </tr>
                <tr>
                  <td>Balance Eléctrico (Gen / Cons)</td>
                  <td>
                    {{ mission.generacion_w }} W / {{ mission.consumo_w }} W ({{
                      mission.balance_potencia_w >= 0
                        ? `+${mission.balance_potencia_w}`
                        : mission.balance_potencia_w
                    }}
                    W)
                  </td>
                  <td>Batería acumulada: {{ mission.bateria_actual_wh }} / {{ mission.bateria_capacidad_wh }} Wh</td>
                </tr>
                <tr>
                  <td>Soporte Vital (O₂ / Raciones)</td>
                  <td>{{ mission.o2_dias_disponibles }} días / {{ mission.comida_dias_disponibles }} días</td>
                  <td>Duración misión: {{ mission.dias_transito + mission.dias_en_destino }} días</td>
                </tr>
                <tr>
                  <td>Ciencia y Transmisión de Datos</td>
                  <td>
                    {{ mission.puntos_ciencia_generados }} pts · {{ mission.datos_transmitidos_gb }} /
                    {{ mission.datos_generados_gb }} GB
                  </td>
                  <td>
                    {{ mission.ventanas_comm_restantes }} ventanas ({{
                      Math.round(mission.probabilidad_enlace_comm * 100)
                    }}% disp.)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Barra inferior del visor: Bitácora + Chips instantáneos de Variables Afectadas (Δ) -->
        <div
          class="live-delta-bar"
          :class="{
            'bar-ok': lastStatusType === 'allowed',
            'bar-warn': lastStatusType === 'warning',
            'bar-fail': lastStatusType === 'fail',
          }"
        >
          <div class="log-message-line">
            <span class="log-tag">BITÁCORA:</span>
            <span>{{ statusMessage }}</span>
          </div>

          <div v-if="nonZeroDeltas.length > 0" class="delta-chips-row">
            <span class="delta-label">IMPACTO Δ:</span>
            <span
              v-for="chg in nonZeroDeltas"
              :key="chg.variable"
              class="delta-chip"
            >
              {{ chg.etiqueta }}: {{ chg.valor_anterior }} →
              <strong>{{ chg.valor_nuevo }} {{ chg.unidad }}</strong>
              ({{ chg.delta > 0 ? `+${chg.delta}` : chg.delta }})
            </span>
          </div>
        </div>
      </section>

      <!-- PANEL DERECHO (42%): CONSOLA DE DECISIONES DE ETAPA + PIE DE AVANCE FIJO -->
      <aside class="right-command-column">
        <div class="command-scroll-area">
          <!-- ALERTAS Y EVENTOS ACTIVOS (PRIORIDAD ALTA CUANDO OCURREN) -->
          <div v-if="mission.eventos_activos.length > 0" class="events-drawer">
            <div class="event-drawer-header blink-warning">
              ▲ ALERTA DE SUBSISTEMA SIN CUANTIFICAR ({{ mission.eventos_activos.length }})
            </div>
            <div v-for="ev in mission.eventos_activos" :key="ev.id" class="event-item">
              <div class="event-item-top">
                <strong>{{ ev.titulo }}</strong>
                <span class="badge" style="border-color: var(--orange); color: var(--orange)">
                  {{ ev.subsistema_afectado.toUpperCase() }}
                </span>
              </div>
              <p class="serif-narrative event-copy">{{ ev.mensaje_alerta }}</p>
              <div v-if="ev.diagnosticado_por_tierra" class="earth-diag-box">
                <strong>DIAGNÓSTICO DE TIERRA:</strong> {{ ev.diagnostico_detallado }}
              </div>
              <div class="event-btn-stack">
                <button
                  v-for="opt in ev.opciones"
                  :key="opt.id"
                  class="event-opt-button"
                  @click="handleResolveEvent(ev.id, opt.id)"
                >
                  <span>{{ opt.texto }}</span>
                  <span class="opt-cost-pills">
                    <em v-if="opt.costo_presupuesto_usd > 0">
                      -${{ opt.costo_presupuesto_usd.toLocaleString() }}
                    </em>
                    <em v-if="opt.costo_energia_wh > 0">-{{ opt.costo_energia_wh }} Wh</em>
                    <em v-if="opt.costo_delta_v_ms > 0">-{{ opt.costo_delta_v_ms }} m/s</em>
                    <em v-if="opt.consume_ventana_comm">-1 Ventana</em>
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- ETAPA 1: DEFINICIÓN DE LA MISIÓN -->
          <div v-if="mission.etapa_actual === 1" class="stage-card">
            <div class="stage-hero-row">
              <PixelSprite
                animacion="perro_interactuar"
                :width="72"
                :height="92"
                :fps="8"
                animo="sol"
              />
              <div>
                <div class="stage-eyebrow">ETAPA 01 DE 10 · PLANIFICACIÓN</div>
                <h2 class="stage-title">Definición de la Misión</h2>
                <p class="serif-narrative stage-prose">
                  Selecciona el destino de referencia para la expedición científica. La masa máxima
                  de lanzamiento es fija ({{ mission.masa_lanzamiento_max_kg }} kg).
                </p>
              </div>
            </div>

            <div class="option-list">
              <div
                v-for="dest in catalog.destinos"
                :key="dest.id"
                class="option-tile"
                :class="{ selected: mission.destino === dest.id }"
                @click="executeDecision('seleccionar_destino', { destino: dest.id })"
              >
                <div class="option-tile-head">
                  <span class="option-name">{{ dest.nombre }}</span>
                  <span class="badge" style="color: var(--cyan)">{{ dest.id }}</span>
                </div>
                <p class="serif-narrative option-prose">{{ dest.descripcion }}</p>
                <div class="spec-chips">
                  <span>Δv mín: {{ dest.delta_v_total_minimo_ms }} m/s</span>
                  <span>Tránsito: {{ dest.dias_transito_estandar }} d</span>
                  <span>Operación: {{ dest.dias_operacion_destino }} d</span>
                  <span>Eclipse: {{ Math.round(dest.fraccion_eclipse * 100) }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ETAPA 2: NEGOCIACIÓN Y FINANCIACIÓN -->
          <div v-if="mission.etapa_actual === 2" class="stage-card">
            <div class="stage-hero-row">
              <PixelSprite animacion="gato_hablar" :width="78" :height="78" :fps="7" />
              <div>
                <div class="stage-eyebrow">ETAPA 02 DE 10 · PATROCINIO</div>
                <h2 class="stage-title">Negociación y Financiación</h2>
                <p class="serif-narrative stage-prose">
                  El presupuesto global actúa como límite duro tanto en el diseño como en los costes
                  de ejecución en tiempo real.
                </p>
              </div>
            </div>

            <div class="option-list">
              <div
                v-for="acuerdo in catalog.acuerdos_financiacion"
                :key="acuerdo.id"
                class="option-tile"
                :class="{ selected: mission.acuerdo_financiacion_id === acuerdo.id }"
                @click="executeDecision('seleccionar_financiacion', { acuerdo_id: acuerdo.id })"
              >
                <div class="option-tile-head">
                  <span class="option-name">{{ acuerdo.nombre }}</span>
                  <span class="badge" style="color: var(--amber)">
                    ${{ acuerdo.presupuesto_usd.toLocaleString() }} USD
                  </span>
                </div>
                <p class="serif-narrative option-prose">{{ acuerdo.descripcion }}</p>
                <div class="spec-chips">
                  <span>Exigencia científica: {{ acuerdo.exigencia_ciencia }} pts</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ETAPA 3: DISEÑO DE LA NAVE Y SELECCIÓN DE PERSONAL (CON SUB-PESTAÑAS LIMPIAS) -->
          <div v-if="mission.etapa_actual === 3" class="stage-card">
            <div class="stage-eyebrow">ETAPA 03 DE 10 · INGENIERÍA DE SISTEMAS</div>
            <h2 class="stage-title">Diseño de Nave y Tripulación</h2>
            <p class="serif-narrative stage-prose" style="margin-bottom: 10px">
              Revisa cada ficha técnica antes de comprar. El catálogo no avisa de incompatibilidades
              ni bloquea si superas la masa del lanzador.
            </p>

            <!-- Selector segmentado: Componentes vs Personal -->
            <div class="segmented-control">
              <button
                class="seg-btn"
                :class="{ active: stage3SubTab === 'hardware' }"
                @click="stage3SubTab = 'hardware'"
              >
                🔧 1. Catálogo de Componentes
              </button>
              <button
                class="seg-btn"
                :class="{ active: stage3SubTab === 'crew' }"
                @click="stage3SubTab = 'crew'"
              >
                👨‍🚀 2. Tripulación ({{ mission.tripulacion.length }}/4)
              </button>
            </div>

            <!-- Sub-pestaña A: Catálogo de Componentes por categoría -->
            <template v-if="stage3SubTab === 'hardware'">
              <div class="category-pills">
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  class="cat-pill"
                  :class="{ active: activeCategory === cat.id }"
                  @click="activeCategory = cat.id"
                >
                  {{ cat.label }}
                </button>
              </div>

              <div class="compact-catalog-list">
                <div
                  v-for="comp in filteredComponents"
                  :key="comp.id"
                  class="catalog-row-card"
                  :class="{ installed: mission.componentes_instalados.includes(comp.id) }"
                >
                  <div class="cat-row-top">
                    <span class="cat-item-name">{{ comp.nombre }}</span>
                    <span class="cat-item-cost">${{ comp.costo_usd.toLocaleString() }} USD</span>
                  </div>
                  <p class="cat-item-desc">{{ comp.descripcion_ficha }}</p>
                  <div class="cat-row-footer">
                    <div class="spec-chips">
                      <span>{{ comp.masa_kg }} kg</span>
                      <span v-if="comp.consumo_w > 0">-{{ comp.consumo_w }} W</span>
                      <span v-if="comp.generacion_w > 0">+{{ comp.generacion_w }} W</span>
                      <span v-if="comp.capacidad_wh > 0">{{ comp.capacidad_wh }} Wh</span>
                      <span v-if="comp.isp_s > 0">Isp {{ comp.isp_s }}s</span>
                      <span v-if="comp.tasa_kbps > 0">{{ comp.tasa_kbps }} kbps</span>
                      <span v-if="comp.dias_o2 > 0">{{ comp.dias_o2 }}d O₂</span>
                      <span v-if="comp.puntos_ciencia_base > 0">+{{ comp.puntos_ciencia_base }} pts</span>
                    </div>

                    <button
                      v-if="!mission.componentes_instalados.includes(comp.id)"
                      class="btn-primary btn-sm"
                      @click="executeDecision('instalar_componente', { componente_id: comp.id })"
                    >
                      + Instalar
                    </button>
                    <button
                      v-else-if="comp.categoria === 'instrumento' || comp.categoria === 'robot'"
                      class="btn-sm"
                      @click="executeDecision('remover_componente', { componente_id: comp.id })"
                    >
                      Retirar
                    </button>
                    <span v-else class="installed-badge">✓ ACTIVO</span>
                  </div>
                </div>
              </div>
            </template>

            <!-- Sub-pestaña B: Selección de Personal -->
            <template v-else>
              <div class="compact-catalog-list">
                <div
                  v-for="cand in catalog.candidatos_tripulacion"
                  :key="cand.id"
                  class="catalog-row-card"
                  :class="{ installed: mission.tripulacion.some((t) => t.id === cand.id) }"
                >
                  <div class="crew-row-layout">
                    <PixelSprite
                      animacion="gato_caminar"
                      :width="52"
                      :height="52"
                      :fps="7"
                      :animo="cand.estado_animo"
                    />
                    <div style="flex: 1">
                      <div class="cat-row-top">
                        <span class="cat-item-name">{{ cand.nombre }}</span>
                        <span class="cat-item-cost">-${{ cand.salario_usd.toLocaleString() }} USD</span>
                      </div>
                      <div class="spec-chips" style="margin: 3px 0">
                        <span>{{ cand.rol }}</span>
                        <span>Esp: {{ cand.especialidad.toUpperCase() }}</span>
                        <span>Exp: {{ cand.experiencia }}/5</span>
                      </div>
                      <p class="cat-item-desc">{{ cand.biografia_corta }}</p>
                    </div>
                  </div>
                  <div class="cat-row-footer" style="justify-content: flex-end">
                    <button
                      v-if="!mission.tripulacion.some((t) => t.id === cand.id)"
                      class="btn-cyan btn-sm"
                      :disabled="mission.tripulacion.length >= 4"
                      @click="executeDecision('contratar_tripulante', { crew_id: cand.id })"
                    >
                      + Contratar Especialista
                    </button>
                    <button
                      v-else
                      class="btn-sm"
                      @click="executeDecision('remover_tripulante', { crew_id: cand.id })"
                    >
                      Relevar
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- ETAPA 4: PLANIFICACIÓN ORBITAL -->
          <div v-if="mission.etapa_actual === 4" class="stage-card">
            <div class="stage-eyebrow">ETAPA 04 DE 10 · MECÁNICA ORBITAL</div>
            <h2 class="stage-title">Planificación de Trayectoria y Ventana</h2>
            <p class="serif-narrative stage-prose">
              Elige el perfil de transferencia hacia {{ mission.destino }}. Una ruta rápida consume
              un +18% de Delta-v pero ahorra días de soporte vital.
            </p>
            <div class="option-list">
              <div
                class="option-tile"
                :class="{ selected: mission.perfil_trayectoria === 'estandar' }"
                @click="
                  executeDecision('configurar_trayectoria', {
                    perfil_trayectoria: 'estandar',
                    ventana_lanzamiento: mission.ventana_lanzamiento,
                  })
                "
              >
                <div class="option-tile-head">
                  <span class="option-name">Transferencia Hohmann Estándar</span>
                  <span class="badge">Mínimo Δv</span>
                </div>
                <p class="serif-narrative option-prose">
                  Requiere {{ currentDestinationInfo?.delta_v_total_minimo_ms }} m/s totales y
                  {{ currentDestinationInfo?.dias_transito_estandar }} día(s) de tránsito.
                </p>
              </div>

              <div
                class="option-tile"
                :class="{ selected: mission.perfil_trayectoria === 'rapida' }"
                @click="
                  executeDecision('configurar_trayectoria', {
                    perfil_trayectoria: 'rapida',
                    ventana_lanzamiento: mission.ventana_lanzamiento,
                  })
                "
              >
                <div class="option-tile-head">
                  <span class="option-name">Transferencia Directa Rápida (+18% Δv)</span>
                  <span class="badge" style="color: var(--amber)">Menor Tiempo</span>
                </div>
                <p class="serif-narrative option-prose">
                  Reduce el viaje a {{ currentDestinationInfo?.dias_transito_rapido }} día(s) a
                  cambio de mayor gasto de propelente.
                </p>
              </div>
            </div>
          </div>

          <!-- ETAPA 5: LANZAMIENTO -->
          <div v-if="mission.etapa_actual === 5" class="stage-card">
            <div class="stage-eyebrow">ETAPA 05 DE 10 · ASCENSO E INSERCIÓN</div>
            <h2 class="stage-title">Verificación de Lanzamiento</h2>
            <p class="serif-narrative stage-prose">
              La nave está en la plataforma. Al confirmar el lanzamiento se verificará la
              restricción física crítica de masa máxima ({{ mission.masa_total_kg }} /
              {{ mission.masa_lanzamiento_max_kg }} kg) y el impulso de ascenso ({{
                currentDestinationInfo?.delta_v_lanzamiento_ms
              }}
              m/s).
            </p>
          </div>

          <!-- ETAPA 6: TRÁNSITO -->
          <div v-if="mission.etapa_actual === 6" class="stage-card">
            <div class="stage-eyebrow">ETAPA 06 DE 10 · NAVEGACIÓN</div>
            <h2 class="stage-title">Tránsito hacia {{ mission.destino }}</h2>
            <p class="serif-narrative stage-prose">
              Supervisa las anomalías en ruta y gestiona la separación entre el presupuesto
              financiero (soporte desde Tierra) y el presupuesto de energía a bordo (Wh).
            </p>
          </div>

          <!-- ETAPAS 7, 8, 9: OPERACIONES EN DESTINO -->
          <div v-if="mission.etapa_actual >= 7 && mission.etapa_actual <= 9" class="stage-card">
            <div class="stage-eyebrow">ETAPA 0{{ mission.etapa_actual }} DE 10 · EN ÓRBITA / DESTINO</div>
            <h2 class="stage-title">{{ mission.nombre_etapa }}</h2>
            <p class="serif-narrative stage-prose">
              Recorre las habitaciones en el visor 2D izquierdo usando <code>A</code>/<code>D</code>
              y la tecla <code>E</code>, o ejecuta órdenes directas desde esta consola:
            </p>

            <div class="quick-ops-stack">
              <button
                class="btn-primary op-big-btn"
                @click="executeDecision('operacion_cientifica', {})"
              >
                🔬 Operar Instrumentos del Laboratorio (+Ciencia / +Datos GB)
              </button>
              <button
                class="btn-cyan op-big-btn"
                @click="executeDecision('tarea_tripulacion', { subtipo: 'estabilizar_animo' })"
              >
                ☀ Estabilizar Estado de Ánimo en Módulo de Vida
              </button>
              <button
                class="op-big-btn"
                @click="executeDecision('tarea_tripulacion', { subtipo: 'mantenimiento_general' })"
              >
                🔧 Ejecutar Mantenimiento Común de Subsistemas
              </button>
              <button
                class="btn-primary op-big-btn"
                @click="executeDecision('usar_ventana_comm', {})"
              >
                📡 Transmitir Datos a Tierra ({{ mission.ventanas_comm_restantes }} ventanas disp.)
              </button>
            </div>
          </div>
        </div>

        <!-- PIE DE ACCIÓN PRIMARIA SIEMPRE VISIBLE (SIN HACER SCROLL) -->
        <footer class="command-footer-dock">
          <div class="footer-meta">
            <span>ETAPA {{ mission.etapa_actual }}/10</span>
            <span>TRIPULACIÓN: {{ mission.tripulacion.length }}/4</span>
          </div>
          <button
            class="btn-primary advance-cta-btn"
            :disabled="loading"
            @click="advanceStage"
          >
            {{
              mission.etapa_actual < 9
                ? `Avanzar a Etapa ${mission.etapa_actual + 1} ►`
                : 'Ejecutar Retorno e Informe Final ►'
            }}
          </button>
        </footer>
      </aside>
    </main>
  </div>
</template>

<style scoped>
/* ========================================================================= */
/* ARQUITECTURA DE ESTACIÓN DE VUELO (100VH EN ESCRITORIO, CERO FATIGA)      */
/* ========================================================================= */
.cockpit-layout {
  min-height: 100vh;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--void);
  overflow: hidden;
}

@media (max-width: 1080px) {
  .cockpit-layout {
    max-height: none;
    overflow: visible;
  }
}

/* 1. CINTA SUPERIOR */
.top-ribbon {
  height: 58px;
  padding: 0 18px;
  background: var(--void-deep);
  border-bottom: 1px solid var(--steel);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-shrink: 0;
}

@media (max-width: 1080px) {
  .top-ribbon {
    height: auto;
    padding: 10px 14px;
    flex-wrap: wrap;
  }
}

.brand-cluster {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  background: rgba(255, 176, 0, 0.16);
  border: 1px solid var(--amber);
  color: var(--gold);
  font-weight: 700;
  font-size: 13px;
  padding: 4px 9px;
  border-radius: 4px;
  letter-spacing: 0.08em;
}

.brand-titles {
  display: flex;
  flex-direction: column;
}

.brand-main {
  font-size: 11px;
  font-weight: 700;
  color: var(--bone);
  letter-spacing: 0.04em;
}

.brand-stage-sub {
  font-size: 11px;
  color: var(--amber);
}

.timeline-10 {
  display: flex;
  gap: 4px;
}

.timeline-node {
  width: 24px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 3px;
  color: var(--mist);
}

.timeline-node.done {
  border-color: var(--cyan);
  color: var(--cyan);
  background: rgba(79, 209, 197, 0.1);
}

.timeline-node.current {
  background: var(--amber);
  border-color: var(--gold);
  color: var(--void);
  font-weight: 700;
}

.telemetry-pills {
  display: flex;
  gap: 8px;
}

@media (max-width: 760px) {
  .telemetry-pills {
    flex-wrap: wrap;
  }
}

.tpill {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 4px;
  padding: 4px 10px;
  display: flex;
  flex-direction: column;
  min-width: 108px;
}

.tpill-label {
  font-size: 9px;
  color: var(--mist);
}

.tpill-val {
  font-size: 12px;
  color: var(--bone);
}

/* 2. ESTACIÓN DIVIDIDA EN 2 COLUMNAS */
.split-workstation {
  flex: 1;
  display: grid;
  grid-template-columns: 1.38fr 1fr;
  gap: 14px;
  padding: 12px 18px;
  min-height: 0;
}

@media (max-width: 1080px) {
  .split-workstation {
    grid-template-columns: 1fr;
  }
}

.final-report-viewport {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* COLUMNA IZQUIERDA: VISOR MULTIMODO */
.left-viewport-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

.viewport-switcher {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.vtab-btn {
  flex: 1;
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 600;
  background: var(--void-deep);
  border: 1px solid var(--steel);
  color: var(--mist);
}

.vtab-btn.active {
  background: var(--cabin);
  border-color: var(--amber);
  color: var(--gold);
}

.viewport-stage-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.full-telemetry-sheet {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sheet-title {
  color: var(--amber);
  font-weight: 700;
  font-size: 13px;
}

.sheet-sub {
  font-size: 11px;
  color: var(--mist);
  margin-top: 2px;
}

.clean-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.clean-table th,
.clean-table td {
  border: 1px solid var(--steel);
  padding: 8px 10px;
  text-align: left;
}

.clean-table th {
  background: var(--void);
  color: var(--mist);
}

/* BARRA DE BITÁCORA Y CHIPS DE IMPACTO (Δ) */
.live-delta-bar {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-left: 4px solid var(--cyan);
  border-radius: 5px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.live-delta-bar.bar-warn {
  border-left-color: var(--orange);
}

.live-delta-bar.bar-fail {
  border-left-color: var(--red);
}

.log-message-line {
  font-size: 11px;
  color: var(--bone);
  display: flex;
  gap: 6px;
}

.log-tag {
  color: var(--amber);
  font-weight: 700;
  flex-shrink: 0;
}

.delta-chips-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.delta-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--cyan);
}

.delta-chip {
  font-size: 10px;
  background: var(--void);
  border: 1px solid var(--steel);
  padding: 2px 7px;
  border-radius: 3px;
  color: var(--mist);
}

.delta-chip strong {
  color: var(--bone);
}

/* COLUMNA DERECHA: CONSOLA DE DECISIONES */
.right-command-column {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.command-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stage-hero-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stage-eyebrow {
  font-size: 10px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 0.06em;
}

.stage-title {
  font-size: 17px;
  color: var(--gold);
  margin: 2px 0 4px;
}

.stage-prose {
  font-size: 14px;
  color: var(--bone);
  line-height: 1.55;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-tile {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 11px 12px;
  cursor: pointer;
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.option-tile:hover {
  border-color: var(--cyan);
}

.option-tile.selected {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.09);
}

.option-tile-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.option-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--gold);
}

.option-prose {
  font-size: 13px;
  color: var(--bone);
  margin-bottom: 8px;
}

.spec-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.spec-chips span {
  font-size: 10px;
  color: var(--cyan);
  background: rgba(27, 35, 64, 0.75);
  border: 1px solid var(--steel);
  padding: 1px 6px;
  border-radius: 3px;
}

/* CONTROLES DE ETAPA 3 (CATÁLOGO Y PERSONAL) */
.segmented-control {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  background: var(--void-deep);
  padding: 4px;
  border-radius: 5px;
  border: 1px solid var(--steel);
}

.seg-btn {
  border: none;
  background: transparent;
  color: var(--mist);
  font-size: 11px;
  font-weight: 600;
  padding: 6px 8px;
}

.seg-btn.active {
  background: var(--cabin);
  color: var(--gold);
  border: 1px solid var(--amber);
}

.category-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.cat-pill {
  padding: 4px 9px;
  font-size: 11px;
  background: var(--void);
}

.cat-pill.active {
  border-color: var(--amber);
  color: var(--gold);
  background: rgba(255, 176, 0, 0.16);
}

.compact-catalog-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.catalog-row-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.catalog-row-card.installed {
  border-color: var(--cyan);
}

.cat-row-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.cat-item-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--bone);
}

.cat-item-cost {
  font-size: 11px;
  font-weight: 700;
  color: var(--amber);
  white-space: nowrap;
}

.cat-item-desc {
  font-size: 11px;
  color: var(--mist);
  line-height: 1.4;
}

.cat-row-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 11px;
  white-space: nowrap;
}

.installed-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--green);
  white-space: nowrap;
}

.crew-row-layout {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* EVENTOS ACTIVOS */
.events-drawer {
  background: rgba(255, 122, 61, 0.08);
  border: 1px solid var(--orange);
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-drawer-header {
  font-size: 11px;
  font-weight: 700;
  color: var(--orange);
}

.event-item {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-item-top {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--gold);
}

.event-copy {
  font-size: 13px;
  color: var(--bone);
}

.earth-diag-box {
  font-size: 11px;
  color: var(--cyan);
  background: rgba(79, 209, 197, 0.1);
  border-left: 3px solid var(--cyan);
  padding: 6px 8px;
}

.event-btn-stack {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.event-opt-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: left;
  font-size: 11px;
  gap: 8px;
}

.opt-cost-pills {
  display: flex;
  gap: 6px;
  font-size: 10px;
  color: var(--amber);
  white-space: nowrap;
}

.opt-cost-pills em {
  font-style: normal;
}

.quick-ops-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
}

.op-big-btn {
  text-align: left;
  padding: 10px 12px;
}

/* PIE FIJO DE LA CONSOLA DERECHA */
.command-footer-dock {
  background: var(--void-deep);
  border-top: 1px solid var(--steel);
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.footer-meta {
  display: flex;
  flex-direction: column;
  font-size: 10px;
  color: var(--mist);
}

.advance-cta-btn {
  padding: 10px 16px;
  font-size: 12px;
}
</style>
