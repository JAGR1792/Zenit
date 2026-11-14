<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import BossReportScene from '../components/BossReportScene.vue'
import DestinationRooms2D from '../components/DestinationRooms2D.vue'
import PixelSprite, { obtenerSpriteTripulante } from '../components/PixelSprite.vue'
import ShipSchematic from '../components/ShipSchematic.vue'
import {
  zenitApi,
  type CatalogoCompleto,
  type DestinoId,
  type DificultadId,
  type EstadoMision,
  type InformeFinal,
} from '../services/api'

const catalog = ref<CatalogoCompleto | null>(null)
const mission = ref<EstadoMision | null>(null)
const finalReport = ref<InformeFinal | null>(null)
const statusMessage = ref<string>('Inicializando consola de misión Zenit...')
const lastStatusType = ref<'allowed' | 'warning' | 'fail'>('allowed')
const loading = ref<boolean>(false)

// Menú de Inicio y Configuración de Dificultad (por defecto 'facil' para hacer más accesible la experiencia)
const showMainMenu = ref<boolean>(true)
const selectedDifficulty = ref<DificultadId>('facil')
const selectedInitialDest = ref<DestinoId>('OTB')
const customMissionName = ref<string>('Expedición Zenit-1')

const difficultyOptions: Array<{
  id: DificultadId
  title: string
  badge: string
  desc: string
  perks: string[]
}> = [
  {
    id: 'facil',
    title: 'Modo Cadete (Fácil · Recomendado)',
    badge: '+FÁCIL / GUIADO',
    desc: 'Ideal para aprender cómo funcionan los sistemas, recolectar ciencia y transmitir datos sin bloqueos frustrantes.',
    perks: [
      '+35% de presupuesto financiero inicial ($168.750 USD en plan estándar)',
      'Capacidad del lanzador ampliada a 1.480 kg (+180 kg de margen)',
      'Espectrómetro Científico ya preinstalado en el Laboratorio',
      '+800 Wh de batería, +6 días de O₂ y +3 ventanas de transmisión',
    ],
  },
  {
    id: 'normal',
    title: 'Modo Director (Estándar)',
    badge: 'EQUILIBRADO',
    desc: 'La experiencia clásica de diseño aeroespacial. Exige vigilar la masa máxima de 1.300 kg y comprar tus propios instrumentos.',
    perks: [
      'Presupuesto nominal ($125.000 USD en acuerdo estándar)',
      'Capacidad de lanzamiento fija en 1.300 kg',
      'Sensores base de respaldo si olvidas comprar instrumentos',
      'Frecuencia estándar de anomalías en vuelo',
    ],
  },
  {
    id: 'dificil',
    title: 'Modo Comandante (Simulación Dura)',
    badge: 'EXPERTO',
    desc: 'Para veteranos que buscan márgenes estrechos de masa, presupuesto reducido y alta presión de fallos en órbita.',
    perks: [
      '-10% de presupuesto financiero inicial',
      'Límite estricto de masa de lanzamiento (1.280 kg)',
      'Mayor probabilidad de fatiga anímica y fallos de subsistema',
    ],
  },
]

// Modos del visor izquierdo y sub-pestañas de la Etapa 3 para eliminar el scroll excesivo
const activeViewportTab = ref<'rooms2d' | 'schematic' | 'telemetry'>('rooms2d')
const stage3SubTab = ref<'hardware' | 'crew'>('hardware')
const activeCategory = ref<string>('instrumento')

const categories = [
  { id: 'instrumento', label: '🔬 Ciencia (Payload)' },
  { id: 'motor', label: '🚀 Motores' },
  { id: 'energia', label: '⚡ Energía' },
  { id: 'antena', label: '📡 Antenas' },
  { id: 'soporte_vital', label: '🌱 Soporte Vital' },
  { id: 'robot', label: '🤖 Robots' },
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

const pendingDataToTransmitGb = computed(() => {
  if (!mission.value) return 0
  return Math.max(
    0,
    Number((mission.value.datos_generados_gb - mission.value.datos_transmitidos_gb).toFixed(2)),
  )
})

const hasScientificInstrumentInstalled = computed(() => {
  if (!mission.value || !catalog.value) return false
  return mission.value.componentes_instalados.some((cid) => {
    const found = catalog.value?.componentes.find((c) => c.id === cid)
    return found && (found.categoria === 'instrumento' || found.categoria === 'robot')
  })
})

// Guía contextual paso a paso por etapa para que el jugador siempre entienda qué hacer
const currentStageGuide = computed(() => {
  if (!mission.value) return null
  const st = mission.value.etapa_actual
  if (st === 1) {
    return {
      objective: 'Elige tu destino espacial (OTB es más cercano y sencillo; Luna exige más Delta-v y antena potente).',
      tip: 'Cuando estés listo, pulsa el botón ámbar "Avanzar a Etapa 2 ►" abajo a la derecha.',
    }
  }
  if (st === 2) {
    return {
      objective: 'Negocia tu presupuesto con el Gato Jefe de la Agencia.',
      tip: 'El presupuesto es un límite duro: de aquí saldrán tanto las compras en diseño como los gastos en vuelo.',
    }
  }
  if (st === 3) {
    return {
      objective: 'Equipa tu nave y contrata hasta 3 perros especialistas (máximo 4 tripulantes contigo).',
      tip: `Vigila que la Masa Total (${mission.value.masa_total_kg} kg) NO supere ${mission.value.masa_lanzamiento_max_kg} kg y asegúrate de llevar al menos 1 instrumento en la pestaña "🔬 Ciencia".`,
    }
  }
  if (st === 4) {
    return {
      objective: 'Selecciona la trayectoria orbital hacia el destino.',
      tip: `Verifica que tu Delta-v disponible (${mission.value.delta_v_disponible_ms} m/s) sea mayor o igual al requerido (${mission.value.delta_v_requerido_total_ms} m/s).`,
    }
  }
  if (st === 5) {
    return {
      objective: 'Verificación en rampa de lanzamiento.',
      tip: 'Pulsa "Avanzar a Etapa 6 ►" para encender motores. Si no superaste la masa máxima, entrarás en órbita.',
    }
  }
  if (st === 6) {
    return {
      objective: 'Crucero de tránsito espacial hacia el destino.',
      tip: 'Si aparece una alerta naranja arriba, elige una opción para resolverla (puedes usar la tripulación, batería o dinero) antes de avanzar.',
    }
  }
  return {
    objective: 'Operaciones en Destino: 1º Recolecta datos en el Laboratorio → 2º Transmítelos a Tierra con la Antena.',
    tip: 'Puedes usar los botones numerados de abajo o caminar con [A/D] y pulsar [E] en las salas 2D de la izquierda.',
  }
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

async function loadCatalogOnly(): Promise<void> {
  try {
    if (!catalog.value) {
      catalog.value = await zenitApi.getCatalog()
    }
  } catch (err) {
    statusMessage.value = `Error cargando catálogo: ${(err as Error).message}`
  }
}

async function startNewMission(fromMenu = false): Promise<void> {
  loading.value = true
  finalReport.value = null
  try {
    if (!catalog.value) {
      catalog.value = await zenitApi.getCatalog()
    }
    mission.value = await zenitApi.createMission({
      nombre_mision: customMissionName.value.trim() || 'Expedición Zenit-1',
      destino: selectedInitialDest.value,
      dificultad: selectedDifficulty.value,
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })
    activeViewportTab.value = 'rooms2d'
    if (fromMenu) {
      showMainMenu.value = false
    }
    statusMessage.value = `Misión iniciada en dificultad ${selectedDifficulty.value.toUpperCase()}. Sigue la guía paso a paso del panel derecho.`
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

onMounted(async () => {
  await loadCatalogOnly()
  await startNewMission(false)
})
</script>

<template>
  <div class="cockpit-layout">
    <!-- ======================================================================= -->
    <!-- MENÚ DE INICIO, DIFICULTAD Y GUÍA RÁPIDA DE ORGANIZACIÓN                -->
    <!-- ======================================================================= -->
    <div v-if="showMainMenu" class="main-menu-overlay">
      <div class="menu-container">
        <!-- Encabezado con el Gato Jefe y la Tripulación de Perros -->
        <div class="menu-hero-banner">
          <div class="menu-title-block">
            <span class="menu-eyebrow">SIMULADOR NARRATIVO DE INGENIERÍA ESPACIAL</span>
            <h1 class="menu-main-title">PROYECTO ZENIT</h1>
            <p class="serif-narrative menu-subtitle">
              Planifica, diseña, lanza y opera una expedición científica tripulada. Tú y tu equipo
              de perros astronautas operan la nave; el Gato Director General evalúa cada decisión.
            </p>
          </div>

          <!-- Escaparate de Sprites Oficiales: Perros = Tripulación | Gato = Jefe -->
          <div class="cast-showcase">
            <div class="cast-group">
              <span class="cast-group-label">TRIPULACIÓN CANINA (A BORDO)</span>
              <div class="cast-row">
                <PixelSprite
                  animacion="perro_caminar"
                  :width="56"
                  :height="72"
                  animo="sol"
                  etiqueta="DIRECTOR"
                />
                <PixelSprite
                  animacion="perro_cientifico"
                  :width="56"
                  :height="72"
                  animo="sol"
                  etiqueta="CIENTÍFICO"
                />
                <PixelSprite
                  animacion="perro_ingeniero"
                  :width="56"
                  :height="72"
                  animo="sol"
                  etiqueta="INGENIERO"
                />
                <PixelSprite
                  animacion="perro_medico"
                  :width="56"
                  :height="72"
                  animo="nube"
                  etiqueta="MÉDICO"
                />
                <PixelSprite
                  animacion="perro_comunicaciones"
                  :width="56"
                  :height="72"
                  animo="lluvia"
                  etiqueta="COMMS"
                />
              </div>
            </div>

            <div class="cast-divider"></div>

            <div class="cast-group boss-cast">
              <span class="cast-group-label" style="color: var(--amber)">EL JEFE (PATROCINADOR)</span>
              <PixelSprite
                animacion="gato_hablar"
                :width="72"
                :height="76"
                etiqueta="GATO JEFE"
              />
            </div>
          </div>
        </div>

        <!-- Cuerpo del Menú en 2 Columnas: Configuración + Cómo Jugar -->
        <div class="menu-grid">
          <!-- Columna 1: Elegir Dificultad y Destino -->
          <div class="menu-card">
            <div class="menu-section-title">1. CONFIGURA TU EXPEDICIÓN Y DIFICULTAD</div>

            <div class="menu-form-row">
              <label class="menu-label">
                Nombre de la Misión:
                <input
                  v-model="customMissionName"
                  type="text"
                  class="menu-input"
                  placeholder="Expedición Zenit-1"
                />
              </label>

              <div class="menu-label">
                Destino Inicial:
                <div class="dest-toggle-row">
                  <button
                    class="dest-toggle-btn"
                    :class="{ active: selectedInitialDest === 'OTB' }"
                    @click="selectedInitialDest = 'OTB'"
                  >
                    🌍 Órbita Terrestre Baja (Más accesible)
                  </button>
                  <button
                    class="dest-toggle-btn"
                    :class="{ active: selectedInitialDest === 'LUNA' }"
                    @click="selectedInitialDest = 'LUNA'"
                  >
                    🌕 Cráter Lunar Shackleton (Reto mayor)
                  </button>
                </div>
              </div>
            </div>

            <div class="difficulty-cards">
              <div
                v-for="diff in difficultyOptions"
                :key="diff.id"
                class="diff-card"
                :class="{ selected: selectedDifficulty === diff.id }"
                @click="selectedDifficulty = diff.id"
              >
                <div class="diff-head">
                  <span class="diff-title">{{ diff.title }}</span>
                  <span class="badge" style="color: var(--amber)">{{ diff.badge }}</span>
                </div>
                <p class="diff-desc">{{ diff.desc }}</p>
                <ul class="diff-perks">
                  <li v-for="(perk, i) in diff.perks" :key="i">{{ perk }}</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Columna 2: Guía Clara de 4 Pasos (Cómo Jugar y Transmitir Datos) -->
          <div class="menu-card guide-card">
            <div class="menu-section-title">2. GUÍA RÁPIDA: ¿CÓMO FUNCIONA EL JUEGO?</div>

            <div class="howto-steps">
              <div class="howto-step">
                <div class="step-num">1</div>
                <div>
                  <strong>Diseña sin pasarte de Masa ni Presupuesto (Etapas 1 a 4)</strong>
                  <p>
                    Elige componentes y contrata perros especialistas. Cuida que la
                    <strong>Masa Total</strong> no supere el límite del lanzador y que tu
                    <strong>Delta-v</strong> alcance para el destino.
                  </p>
                </div>
              </div>

              <div class="howto-step">
                <div class="step-num">2</div>
                <div>
                  <strong>Despega y Resuelve Anomalías en Tránsito (Etapas 5 y 6)</strong>
                  <p>
                    Durante el viaje ocurrirán eventos sin cuantificar. Decide si repararlos con tu
                    tripulación, gastar energía de baterías (Wh) o pagar soporte desde Tierra ($).
                  </p>
                </div>
              </div>

              <div class="howto-step highlight-step">
                <div class="step-num">3</div>
                <div>
                  <strong>🔬 Paso Clave A: Recolectar Datos en el Laboratorio (Etapa 7)</strong>
                  <p>
                    Al llegar al destino, primero debes <strong>generar los datos</strong>. Camina
                    con <code>A</code>/<code>D</code> hasta el <strong>Laboratorio Científico</strong>
                    y pulsa <code>E</code> (o haz clic en el botón
                    <em>"1º Recolectar Datos en Laboratorio"</em>).
                  </p>
                </div>
              </div>

              <div class="howto-step highlight-step">
                <div class="step-num">4</div>
                <div>
                  <strong>📡 Paso Clave B: Transmitir la Info a Tierra (Etapas 7 a 9)</strong>
                  <p>
                    Una vez tengas GB de datos en memoria, ve a la
                    <strong>Sala de Sistemas (Antena)</strong> y pulsa <code>E</code> (o haz clic en
                    <em>"2º Transmitir Datos a Tierra"</em>) para enviarlos usando tus ventanas de
                    comunicación antes de volver al despacho del <strong>Gato Jefe</strong>.
                  </p>
                </div>
              </div>
            </div>

            <div class="menu-cta-row">
              <button
                class="btn-primary start-mission-btn"
                :disabled="loading"
                @click="startNewMission(true)"
              >
                🚀 JUGAR NUEVA EXPEDICIÓN ({{ selectedDifficulty.toUpperCase() }})
              </button>
              <button
                v-if="mission"
                class="resume-btn"
                @click="showMainMenu = false"
              >
                Continuar partida en curso ►
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 1. CINTA SUPERIOR DE TELEMETRÍA Y PROGRESO DE ETAPAS (FIJA Y COMPACTA)  -->
    <!-- ======================================================================= -->
    <header class="top-ribbon">
      <div class="brand-cluster">
        <button class="menu-trigger-btn" @click="showMainMenu = true">
          ☰ MENÚ / DIFICULTAD
        </button>
        <span class="brand-mark">ZENIT</span>
        <div class="brand-titles">
          <span class="brand-main">
            {{ mission?.nombre_mision?.toUpperCase() || 'DIRECCIÓN DE MISIÓN' }}
            <em v-if="mission" class="diff-pill-tag">[{{ mission.dificultad.toUpperCase() }}]</em>
          </span>
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

      <!-- Telemetría clave en tiempo real -->
      <div v-if="mission" class="telemetry-pills">
        <div class="tpill">
          <span class="tpill-label">PRESUPUESTO</span>
          <strong class="tpill-val" style="color: var(--gold)">
            ${{ mission.presupuesto_restante_usd.toLocaleString() }}
          </strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">MASA (MÁX {{ mission.masa_lanzamiento_max_kg }})</span>
          <strong
            class="tpill-val"
            :style="{
              color:
                mission.masa_total_kg > mission.masa_lanzamiento_max_kg
                  ? 'var(--orange)'
                  : 'var(--bone)',
            }"
          >
            {{ mission.masa_total_kg }} kg
          </strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">DELTA-V (REQ {{ mission.delta_v_requerido_total_ms }})</span>
          <strong class="tpill-val" style="color: var(--cyan)">
            {{ mission.delta_v_disponible_ms }} m/s
          </strong>
        </div>
        <div class="tpill">
          <span class="tpill-label">DATOS TX / MEMORIA</span>
          <strong class="tpill-val" style="color: var(--green)">
            {{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB
          </strong>
        </div>
      </div>
    </header>

    <!-- ======================================================================= -->
    <!-- ESCENA FINAL (ETAPA 10 O FALLO DE MISIÓN): DESPACHO DEL GATO JEFE       -->
    <!-- ======================================================================= -->
    <main v-if="finalReport" class="final-report-viewport">
      <BossReportScene :report="finalReport" @restart="showMainMenu = true" />
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
            🚀 Esquemático de Nave y Perros
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
                Valores explícitos en tiempo real. El simulador muestra las magnitudes físicas para
                que evalúes tus márgenes operativos.
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
          <!-- GUÍA CONTEXTUAL PASO A PASO DE LA ETAPA ACTUAL -->
          <div v-if="currentStageGuide" class="stage-guide-banner">
            <div class="guide-banner-head">
              <span class="guide-badge">🧭 QUÉ HACER EN ESTA ETAPA</span>
              <span class="guide-stage-num">ETAPA {{ mission.etapa_actual }} / 10</span>
            </div>
            <p class="guide-objective">{{ currentStageGuide.objective }}</p>
            <p class="guide-tip">{{ currentStageGuide.tip }}</p>
          </div>

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
                etiqueta="DIRECTOR"
              />
              <div>
                <div class="stage-eyebrow">ETAPA 01 DE 10 · PLANIFICACIÓN</div>
                <h2 class="stage-title">Definición de la Misión</h2>
                <p class="serif-narrative stage-prose">
                  Selecciona el destino de referencia para la expedición científica. La masa máxima
                  de lanzamiento es de {{ mission.masa_lanzamiento_max_kg }} kg.
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

          <!-- ETAPA 2: NEGOCIACIÓN Y FINANCIACIÓN (CON EL GATO JEFE) -->
          <div v-if="mission.etapa_actual === 2" class="stage-card">
            <div class="stage-hero-row">
              <PixelSprite
                animacion="gato_hablar"
                :width="82"
                :height="86"
                :fps="6"
                etiqueta="GATO JEFE"
              />
              <div>
                <div class="stage-eyebrow">ETAPA 02 DE 10 · DESPACHO DEL JEFE</div>
                <h2 class="stage-title">Negociación y Financiación</h2>
                <p class="serif-narrative stage-prose">
                  El Gato Jefe presenta los fondos disponibles. El presupuesto actúa como límite
                  duro tanto en el diseño como en los costes de ejecución en tiempo real.
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
                    Base: ${{ acuerdo.presupuesto_usd.toLocaleString() }} USD
                  </span>
                </div>
                <p class="serif-narrative option-prose">{{ acuerdo.descripcion }}</p>
                <div class="spec-chips">
                  <span>Exigencia científica: {{ acuerdo.exigencia_ciencia }} pts</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ETAPA 3: DISEÑO DE LA NAVE Y SELECCIÓN DE PERSONAL (PERROS ESPECIALISTAS) -->
          <div v-if="mission.etapa_actual === 3" class="stage-card">
            <div class="stage-eyebrow">ETAPA 03 DE 10 · INGENIERÍA DE SISTEMAS</div>
            <h2 class="stage-title">Diseño de Nave y Tripulación Canina</h2>

            <!-- Indicador rápido de preparación de ciencia y masa -->
            <div class="design-readiness-strip">
              <span
                class="readiness-pill"
                :class="hasScientificInstrumentInstalled ? 'pill-ok' : 'pill-warn'"
              >
                {{
                  hasScientificInstrumentInstalled
                    ? '✓ Instrumento Científico Instalado'
                    : '⚠ Sin instrumento extra (usará sensores base)'
                }}
              </span>
              <span
                class="readiness-pill"
                :class="
                  mission.masa_total_kg <= mission.masa_lanzamiento_max_kg ? 'pill-ok' : 'pill-warn'
                "
              >
                Masa: {{ mission.masa_total_kg }} / {{ mission.masa_lanzamiento_max_kg }} kg
              </span>
            </div>

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
                🐶 2. Tripulación ({{ mission.tripulacion.length }}/4)
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
                      <span v-if="comp.datos_gb_dia > 0">+{{ comp.datos_gb_dia }} GB/día</span>
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

            <!-- Sub-pestaña B: Selección de Personal (TODOS SON PERROS ESPECIALISTAS) -->
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
                      :animacion="obtenerSpriteTripulante(cand.especialidad, false)"
                      :width="58"
                      :height="72"
                      :fps="6"
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

          <!-- ETAPAS 7, 8, 9: OPERACIONES EN DESTINO CON FLUJO GUIADO DE CIENCIA Y TRANSMISIÓN -->
          <div v-if="mission.etapa_actual >= 7 && mission.etapa_actual <= 9" class="stage-card">
            <div class="stage-eyebrow">ETAPA 0{{ mission.etapa_actual }} DE 10 · EN ÓRBITA / DESTINO</div>
            <h2 class="stage-title">{{ mission.nombre_etapa }}</h2>

            <!-- Rastreador visual de los 2 pasos para que el jugador siempre sepa cómo transmitir info -->
            <div class="pipeline-tracker">
              <div
                class="pipeline-step"
                :class="{
                  active: mission.datos_generados_gb === 0,
                  done: mission.datos_generados_gb > 0,
                }"
              >
                <div class="p-step-head">
                  <strong>PASO 1 · LABORATORIO</strong>
                  <span>{{ mission.datos_generados_gb }} GB generados</span>
                </div>
                <p>Recolecta ciencia e información con tus instrumentos.</p>
              </div>

              <div class="pipeline-arrow">➔</div>

              <div
                class="pipeline-step"
                :class="{
                  active: pendingDataToTransmitGb > 0,
                  done:
                    mission.datos_generados_gb > 0 &&
                    mission.datos_transmitidos_gb >= mission.datos_generados_gb,
                }"
              >
                <div class="p-step-head">
                  <strong>PASO 2 · ANTENA (TIERRA)</strong>
                  <span>{{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB enviados</span>
                </div>
                <p>
                  {{
                    pendingDataToTransmitGb > 0
                      ? `¡Tienes ${pendingDataToTransmitGb} GB listos para transmitir!`
                      : mission.datos_generados_gb > 0
                        ? '¡Todos los datos enviados con éxito!'
                        : 'Esperando datos del Paso 1...'
                  }}
                </p>
              </div>
            </div>

            <div class="quick-ops-stack">
              <button
                class="btn-primary op-big-btn"
                :class="{ 'pulse-highlight': mission.datos_generados_gb === 0 }"
                @click="executeDecision('operacion_cientifica', {})"
              >
                <div class="op-btn-row">
                  <span>🔬 <strong>PASO 1:</strong> Recolectar Datos en Laboratorio Científico</span>
                  <span class="op-status-tag">+Ciencia / +GB</span>
                </div>
              </button>

              <button
                class="op-big-btn"
                :class="{
                  'btn-primary pulse-highlight': pendingDataToTransmitGb > 0,
                  'btn-cyan': pendingDataToTransmitGb === 0,
                }"
                @click="executeDecision('usar_ventana_comm', {})"
              >
                <div class="op-btn-row">
                  <span>
                    📡 <strong>PASO 2:</strong> Transmitir Datos a Tierra ({{
                      mission.ventanas_comm_restantes
                    }}
                    ventanas disp.)
                  </span>
                  <span class="op-status-tag">
                    {{
                      pendingDataToTransmitGb > 0
                        ? `ENVIAR ${pendingDataToTransmitGb} GB AHORA`
                        : `${mission.datos_transmitidos_gb}/${mission.datos_generados_gb} GB TX`
                    }}
                  </span>
                </div>
              </button>

              <button
                class="btn-cyan op-big-btn"
                @click="executeDecision('tarea_tripulacion', { subtipo: 'estabilizar_animo' })"
              >
                <div class="op-btn-row">
                  <span>☀ <strong>OPCIONAL:</strong> Estabilizar Estado de Ánimo (Sol) en Módulo de Vida</span>
                  <span class="op-status-tag">+Salud Mental</span>
                </div>
              </button>

              <button
                class="op-big-btn"
                @click="executeDecision('tarea_tripulacion', { subtipo: 'mantenimiento_general' })"
              >
                <div class="op-btn-row">
                  <span>🔧 <strong>OPCIONAL:</strong> Mantenimiento Preventivo de Subsistemas</span>
                  <span class="op-status-tag">+Integridad</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- PIE DE ACCIÓN PRIMARIA SIEMPRE VISIBLE (SIN HACER SCROLL) -->
        <footer class="command-footer-dock">
          <div class="footer-meta">
            <span>ETAPA {{ mission.etapa_actual }}/10</span>
            <span>TRIPULACIÓN: {{ mission.tripulacion.length }}/4 PERROS</span>
          </div>
          <button
            class="btn-primary advance-cta-btn"
            :disabled="loading"
            @click="advanceStage"
          >
            {{
              mission.etapa_actual < 9
                ? `Avanzar a Etapa ${mission.etapa_actual + 1} ►`
                : 'Ejecutar Retorno e Informe con el Gato Jefe ►'
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
  position: relative;
}

@media (max-width: 1080px) {
  .cockpit-layout {
    max-height: none;
    overflow: visible;
  }
}

/* ========================================================================= */
/* MENÚ DE INICIO Y SELECCIÓN DE DIFICULTAD                                  */
/* ========================================================================= */
.main-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: radial-gradient(circle at 50% 15%, #1b2340 0%, #070a14 85%);
  overflow-y: auto;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-container {
  max-width: 1180px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.menu-hero-banner {
  background: rgba(27, 35, 64, 0.85);
  border: 1px solid var(--amber);
  border-radius: 8px;
  padding: 18px 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.65);
}

.menu-title-block {
  max-width: 520px;
}

.menu-eyebrow {
  font-size: 11px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 0.08em;
}

.menu-main-title {
  font-size: 28px;
  color: var(--gold);
  letter-spacing: 0.05em;
  margin: 4px 0 6px;
}

.menu-subtitle {
  font-size: 15px;
  color: var(--bone);
  line-height: 1.5;
}

.cast-showcase {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--void-deep);
  border: 1px solid var(--steel);
  border-radius: 8px;
  padding: 12px 16px;
  flex-wrap: wrap;
}

.cast-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.cast-group-label {
  font-size: 9px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 0.06em;
}

.cast-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.cast-divider {
  width: 1px;
  height: 78px;
  background: var(--steel);
}

.menu-grid {
  display: grid;
  grid-template-columns: 1.08fr 1fr;
  gap: 16px;
}

@media (max-width: 980px) {
  .menu-grid {
    grid-template-columns: 1fr;
  }
}

.menu-card {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 8px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.menu-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--amber);
  letter-spacing: 0.06em;
  border-bottom: 1px solid var(--steel);
  padding-bottom: 6px;
}

.menu-form-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-label {
  font-size: 11px;
  color: var(--mist);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.menu-input {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 4px;
  padding: 7px 10px;
  color: var(--bone);
  font-family: inherit;
  font-size: 12px;
}

.dest-toggle-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.dest-toggle-btn {
  padding: 8px 10px;
  font-size: 11px;
  background: var(--void);
  border: 1px solid var(--steel);
  color: var(--mist);
}

.dest-toggle-btn.active {
  border-color: var(--cyan);
  background: rgba(79, 209, 197, 0.14);
  color: var(--bone);
  font-weight: 700;
}

.difficulty-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diff-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 10px 12px;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
}

.diff-card:hover {
  border-color: var(--cyan);
}

.diff-card.selected {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.11);
}

.diff-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.diff-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--gold);
}

.diff-desc {
  font-size: 11px;
  color: var(--bone);
  margin-bottom: 6px;
}

.diff-perks {
  padding-left: 16px;
  font-size: 10px;
  color: var(--cyan);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.howto-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.howto-step {
  display: flex;
  gap: 10px;
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 11px;
  color: var(--mist);
}

.howto-step strong {
  color: var(--bone);
  display: block;
  margin-bottom: 2px;
}

.howto-step.highlight-step {
  border-color: var(--cyan);
  background: rgba(79, 209, 197, 0.07);
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--amber);
  color: var(--void);
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-cta-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.start-mission-btn {
  padding: 12px 16px;
  font-size: 13px;
  letter-spacing: 0.04em;
}

.resume-btn {
  padding: 8px 12px;
  font-size: 11px;
  background: var(--void);
  color: var(--cyan);
  border-color: var(--cyan);
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

.menu-trigger-btn {
  padding: 5px 10px;
  font-size: 10px;
  font-weight: 700;
  background: var(--cabin);
  border: 1px solid var(--cyan);
  color: var(--cyan);
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

.diff-pill-tag {
  font-style: normal;
  color: var(--cyan);
  font-size: 10px;
  margin-left: 4px;
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

/* BANNER DE GUÍA DE ETAPA */
.stage-guide-banner {
  background: rgba(79, 209, 197, 0.09);
  border: 1px solid var(--cyan);
  border-left: 4px solid var(--amber);
  border-radius: 6px;
  padding: 9px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.guide-banner-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guide-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--amber);
  letter-spacing: 0.05em;
}

.guide-stage-num {
  font-size: 10px;
  color: var(--cyan);
  font-weight: 700;
}

.guide-objective {
  font-size: 12px;
  font-weight: 600;
  color: var(--bone);
}

.guide-tip {
  font-size: 11px;
  color: var(--mist);
}

.design-readiness-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.readiness-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--steel);
}

.readiness-pill.pill-ok {
  background: rgba(123, 216, 143, 0.12);
  border-color: var(--green);
  color: var(--green);
}

.readiness-pill.pill-warn {
  background: rgba(255, 176, 0, 0.14);
  border-color: var(--amber);
  color: var(--gold);
}

/* RASTREADOR DE 2 PASOS (LABORATORIO -> ANTENA) */
.pipeline-tracker {
  display: flex;
  align-items: stretch;
  gap: 8px;
  background: var(--void-deep);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 10px;
}

.pipeline-step {
  flex: 1;
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 8px 10px;
  font-size: 11px;
  color: var(--mist);
}

.pipeline-step.active {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.12);
  color: var(--bone);
}

.pipeline-step.done {
  border-color: var(--green);
  background: rgba(123, 216, 143, 0.1);
}

.p-step-head {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  margin-bottom: 4px;
  color: var(--gold);
}

.pipeline-arrow {
  display: flex;
  align-items: center;
  color: var(--amber);
  font-weight: 700;
}

.op-btn-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.op-status-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(11, 14, 26, 0.45);
  white-space: nowrap;
}

.pulse-highlight {
  box-shadow: 0 0 14px rgba(255, 176, 0, 0.45);
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
