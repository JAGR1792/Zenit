<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
const statusMessage = ref<string>('Inicializando consola y escenario 2D de misión Zenit...')
const lastStatusType = ref<'allowed' | 'warning' | 'fail'>('allowed')
const loading = ref<boolean>(false)
const activeCategory = ref<string>('instrumento')
const showLive2DSimulator = ref<boolean>(true)

const categories = [
  { id: 'motor', label: 'Propulsión (Motores)' },
  { id: 'energia', label: 'Energía (Paneles/Baterías)' },
  { id: 'antena', label: 'Telecomunicaciones' },
  { id: 'soporte_vital', label: 'Soporte Vital (ECLSS)' },
  { id: 'instrumento', label: 'Instrumentos Científicos' },
  { id: 'robot', label: 'Sistemas Autónomos (Robots)' },
]

const filteredComponents = computed(() => {
  if (!catalog.value) return []
  return catalog.value.componentes.filter((c) => c.categoria === activeCategory.value)
})

const currentDestinationInfo = computed(() => {
  if (!catalog.value || !mission.value) return null
  return catalog.value.destinos.find((d) => d.id === mission.value?.destino) ?? null
})

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
    statusMessage.value =
      'Misión activa. Usa [←/→] o [A/D] y la tecla [E] en el escenario Pixel Art 2D para recorrer las habitaciones.'
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
  <div class="zenit-shell">
    <!-- Cabecera Principal -->
    <header class="top-header">
      <div>
        <h1 class="brand-title">ZENIT // SIMULADOR NARRATIVO DE MISIONES ESPACIALES</h1>
        <p class="brand-sub">
          Dirección de misión espacial tripulada · Exploración Pixel Art 2D + Ingeniería de Sistemas
        </p>
      </div>
      <div class="header-actions">
        <button
          class="btn-cyan"
          @click="showLive2DSimulator = !showLive2DSimulator"
        >
          {{ showLive2DSimulator ? 'Ocultar Escenario 2D Pixel Art' : 'Mostrar Escenario 2D Pixel Art' }}
        </button>
        <div v-if="mission" class="stage-indicator">
          <span class="stage-step">ETAPA {{ mission.etapa_actual }} / 10</span>
          <span class="stage-name">{{ mission.nombre_etapa }}</span>
        </div>
      </div>
    </header>

    <!-- Barra de Progreso de las 10 Etapas (Arco "La luz sube" de artboard.html) -->
    <div v-if="mission" class="stages-track">
      <div
        v-for="step in 10"
        :key="step"
        class="stage-segment"
        :class="{
          done: step < mission.etapa_actual,
          current: step === mission.etapa_actual,
        }"
      >
        {{ step }}
      </div>
    </div>

    <!-- Banner de estado / retroalimentación de la última decisión -->
    <div
      class="status-banner"
      :class="{
        'banner-ok': lastStatusType === 'allowed',
        'banner-warn': lastStatusType === 'warning',
        'banner-fail': lastStatusType === 'fail',
      }"
    >
      <strong>BITÁCORA DE CONTROL:</strong> {{ statusMessage }}
    </div>

    <!-- Vista Etapa 10 o Fallo Crítico: Escena del Despacho del Jefe e Informe Final -->
    <BossReportScene
      v-if="finalReport"
      :report="finalReport"
      @restart="startNewMission"
    />

    <!-- Cuerpo Principal del Juego (Etapas 1 a 9) -->
    <template v-else-if="mission && catalog">
      <!-- ESCENARIO 2D PIXEL ART EN TIEMPO REAL (DISPONIBLE DESDE EL INICIO PARA PROBAR SPRITES Y SALAS CON TECLA E) -->
      <DestinationRooms2D
        v-if="showLive2DSimulator"
        :mission="mission"
        @move-room="(roomId) => executeDecision('mover_habitacion', { habitacion_id: roomId })"
        @run-science="executeDecision('operacion_cientifica', {})"
        @run-crew-task="(subtipo) => executeDecision('tarea_tripulacion', { subtipo })"
        @use-comm-window="executeDecision('usar_ventana_comm', {})"
      />

      <div class="main-workspace">
        <!-- COLUMNA IZQUIERDA: Narrativa, Decisiones de Etapa, Catálogo y Eventos -->
        <div class="left-column">
          <!-- ETAPA 1: DEFINICIÓN DE LA MISIÓN (OTB vs LUNA) -->
          <section v-if="mission.etapa_actual === 1" class="panel-box stage-panel">
            <div class="stage-character-banner">
              <PixelSprite
                animacion="perro_interactuar"
                :width="84"
                :height="84"
                :fps="8"
                animo="sol"
                etiqueta="CMDT. DIRECTOR"
              />
              <div>
                <h2 class="stage-heading">ETAPA 1 — DEFINICIÓN DE LA MISIÓN</h2>
                <p class="serif-narrative narrative-lead" style="margin-bottom: 0">
                  En la oficina de planificación, los dos dossiers de expedición científica descansan
                  sobre la mesa metálica. La capacidad estructural máxima del lanzador es fija ({{
                    mission.masa_lanzamiento_max_kg
                  }}
                  kg). Elige el objetivo orbital de tu misión:
                </p>
              </div>
            </div>

            <div class="cards-grid">
              <div
                v-for="dest in catalog.destinos"
                :key="dest.id"
                class="choice-card"
                :class="{ selected: mission.destino === dest.id }"
                @click="executeDecision('seleccionar_destino', { destino: dest.id })"
              >
                <div class="choice-top">
                  <span class="choice-title">{{ dest.nombre }}</span>
                  <span class="badge">{{ dest.id }}</span>
                </div>
                <p class="serif-narrative choice-desc">{{ dest.descripcion }}</p>
                <div class="tech-specs-mini">
                  <span>Δv mín. requerido: {{ dest.delta_v_total_minimo_ms }} m/s</span>
                  <span>Tránsito estándar: {{ dest.dias_transito_estandar }} día(s)</span>
                  <span>Estancia: {{ dest.dias_operacion_destino }} días</span>
                  <span>Eclipse orbital: {{ Math.round(dest.fraccion_eclipse * 100) }}%</span>
                </div>
              </div>
            </div>
          </section>

          <!-- ETAPA 2: NEGOCIACIÓN Y FINANCIACIÓN CON EL JEFE ANIMADO -->
          <section v-if="mission.etapa_actual === 2" class="panel-box stage-panel">
            <div class="stage-character-banner">
              <PixelSprite
                animacion="gato_hablar"
                :width="88"
                :height="88"
                :fps="7"
                etiqueta="PATROCINADOR JEFE"
              />
              <div>
                <h2 class="stage-heading">ETAPA 2 — NEGOCIACIÓN Y FINANCIACIÓN</h2>
                <p class="serif-narrative narrative-lead" style="margin-bottom: 0">
                  El Jefe del Consorcio revisa su portapapeles mientras escucha tu propuesta para
                  {{ mission.destino }}. El presupuesto acordado será un límite duro durante el
                  diseño y se descontará en tiempo real en vuelo.
                </p>
              </div>
            </div>

            <div class="cards-grid">
              <div
                v-for="acuerdo in catalog.acuerdos_financiacion"
                :key="acuerdo.id"
                class="choice-card"
                :class="{ selected: mission.acuerdo_financiacion_id === acuerdo.id }"
                @click="executeDecision('seleccionar_financiacion', { acuerdo_id: acuerdo.id })"
              >
                <div class="choice-top">
                  <span class="choice-title">{{ acuerdo.nombre }}</span>
                  <span class="badge" style="color: var(--amber)">
                    ${{ acuerdo.presupuesto_usd.toLocaleString() }} USD
                  </span>
                </div>
                <p class="serif-narrative choice-desc">{{ acuerdo.descripcion }}</p>
                <div class="tech-specs-mini">
                  <span>Meta científica exigida: {{ acuerdo.exigencia_ciencia }} pts</span>
                </div>
              </div>
            </div>
          </section>

          <!-- ETAPA 3: DISEÑO DE LA NAVE Y SELECCIÓN DE PERSONAL -->
          <section v-if="mission.etapa_actual === 3" class="panel-box stage-panel">
            <h2 class="stage-heading">ETAPA 3 — DISEÑO DE LA NAVE Y SELECCIÓN DE PERSONAL</h2>
            <p class="serif-narrative narrative-lead">
              Examina las fichas técnicas antes de adquirir cada componente: el catálogo publica
              todos los valores nominales sin ocultar datos, pero no bloqueará ni advertirá si
              diseñas una configuración con sobrepeso o déficit energético.
            </p>

            <!-- Pestañas de Categorías del Catálogo -->
            <div class="cat-tabs">
              <button
                v-for="cat in categories"
                :key="cat.id"
                :class="{ 'btn-primary': activeCategory === cat.id }"
                @click="activeCategory = cat.id"
              >
                {{ cat.label }}
              </button>
            </div>

            <!-- Fichas Técnicas Visibles del Catálogo -->
            <div class="catalog-grid">
              <div
                v-for="comp in filteredComponents"
                :key="comp.id"
                class="comp-card"
                :class="{ installed: mission.componentes_instalados.includes(comp.id) }"
              >
                <div class="comp-header">
                  <span class="comp-title">{{ comp.nombre }}</span>
                  <span class="comp-price">${{ comp.costo_usd.toLocaleString() }} USD</span>
                </div>
                <p class="comp-desc">{{ comp.descripcion_ficha }}</p>
                <div class="ficha-tecnica">
                  <span>Masa: {{ comp.masa_kg }} kg</span>
                  <span v-if="comp.consumo_w > 0">Consumo: {{ comp.consumo_w }} W</span>
                  <span v-if="comp.generacion_w > 0">Generación: {{ comp.generacion_w }} W</span>
                  <span v-if="comp.capacidad_wh > 0">Batería: {{ comp.capacidad_wh }} Wh</span>
                  <span v-if="comp.isp_s > 0">Isp: {{ comp.isp_s }} s</span>
                  <span v-if="comp.combustible_kg > 0">Propelente: {{ comp.combustible_kg }} kg</span>
                  <span v-if="comp.tasa_kbps > 0">Tasa: {{ comp.tasa_kbps }} kbps</span>
                  <span v-if="comp.ventanas_dia > 0">Ventanas/día: {{ comp.ventanas_dia }}</span>
                  <span v-if="comp.dias_o2 > 0">O2/Comida: {{ comp.dias_o2 }} días-persona</span>
                  <span v-if="comp.puntos_ciencia_base > 0">
                    Ciencia: +{{ comp.puntos_ciencia_base }} pts ({{ comp.datos_gb_dia }} GB/día)
                  </span>
                </div>
                <div class="comp-actions">
                  <button
                    v-if="!mission.componentes_instalados.includes(comp.id)"
                    class="btn-primary"
                    @click="executeDecision('instalar_componente', { componente_id: comp.id })"
                  >
                    Instalar en Nave
                  </button>
                  <button
                    v-else-if="comp.categoria === 'instrumento' || comp.categoria === 'robot'"
                    @click="executeDecision('remover_componente', { componente_id: comp.id })"
                  >
                    Desinstalar (Reembolsar)
                  </button>
                  <span v-else class="installed-tag">✓ INSTALADO EN CHASIS</span>
                </div>
              </div>
            </div>

            <!-- Selección de Personal con Sprites (Máximo 4 incluido el jugador) -->
            <div class="crew-recruitment">
              <h3 class="sub-heading">
                POOL DE TRIPULACIÓN ({{ mission.tripulacion.length }} / 4 PLAZAS OCUPADAS)
              </h3>
              <p class="serif-narrative" style="font-size: 13px; color: var(--mist); margin-bottom: 8px">
                Al contratar un especialista, aparecerá inmediatamente caminando en su habitación
                asignada dentro del escenario 2D superior.
              </p>
              <div class="catalog-grid">
                <div
                  v-for="cand in catalog.candidatos_tripulacion"
                  :key="cand.id"
                  class="comp-card"
                  :class="{ installed: mission.tripulacion.some((t) => t.id === cand.id) }"
                >
                  <div class="cand-row">
                    <PixelSprite
                      animacion="gato_caminar"
                      :width="56"
                      :height="56"
                      :fps="7"
                      :animo="cand.estado_animo"
                    />
                    <div style="flex: 1">
                      <div class="comp-header">
                        <span class="comp-title">{{ cand.nombre }}</span>
                        <span class="comp-price">-${{ cand.salario_usd.toLocaleString() }} USD</span>
                      </div>
                      <div style="font-size: 10px; color: var(--cyan)">
                        {{ cand.rol }} · [{{ cand.especialidad.toUpperCase() }}] · Exp {{ cand.experiencia }}/5
                      </div>
                    </div>
                  </div>
                  <p class="comp-desc">{{ cand.biografia_corta }}</p>
                  <div class="comp-actions">
                    <button
                      v-if="!mission.tripulacion.some((t) => t.id === cand.id)"
                      class="btn-cyan"
                      :disabled="mission.tripulacion.length >= 4"
                      @click="executeDecision('contratar_tripulante', { crew_id: cand.id })"
                    >
                      Contratar Especialista
                    </button>
                    <button
                      v-else
                      @click="executeDecision('remover_tripulante', { crew_id: cand.id })"
                    >
                      Relevar del Puesto
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- ETAPA 4: PLANIFICACIÓN ORBITAL -->
          <section v-if="mission.etapa_actual === 4" class="panel-box stage-panel">
            <h2 class="stage-heading">ETAPA 4 — PLANIFICACIÓN ORBITAL</h2>
            <p class="serif-narrative narrative-lead">
              Calculando efemérides Tierra-{{ mission.destino }}. Una transferencia estándar (tipo
              Hohmann) minimiza el gasto de Delta-v pero prolonga la exposición en tránsito; una
              transferencia rápida reduce los días de vuelo a costa de un mayor impulso propulsivo.
            </p>
            <div class="cards-grid">
              <div
                class="choice-card"
                :class="{ selected: mission.perfil_trayectoria === 'estandar' }"
                @click="
                  executeDecision('configurar_trayectoria', {
                    perfil_trayectoria: 'estandar',
                    ventana_lanzamiento: mission.ventana_lanzamiento,
                  })
                "
              >
                <div class="choice-top">
                  <span class="choice-title">Transferencia Orbital Estándar (Mínima Energía)</span>
                </div>
                <p class="serif-narrative choice-desc">
                  Optimiza el consumo de propelente, pero exige más días de soporte vital en tránsito.
                </p>
              </div>

              <div
                class="choice-card"
                :class="{ selected: mission.perfil_trayectoria === 'rapida' }"
                @click="
                  executeDecision('configurar_trayectoria', {
                    perfil_trayectoria: 'rapida',
                    ventana_lanzamiento: mission.ventana_lanzamiento,
                  })
                "
              >
                <div class="choice-top">
                  <span class="choice-title">Transferencia Rápida Directa (+18% Δv)</span>
                </div>
                <p class="serif-narrative choice-desc">
                  Acorta el tránsito y el desgaste de consumibles, exigiendo mayor margen de Delta-v.
                </p>
              </div>
            </div>
          </section>

          <!-- ETAPA 5: LANZAMIENTO -->
          <section v-if="mission.etapa_actual === 5" class="panel-box stage-panel">
            <h2 class="stage-heading">ETAPA 5 — LANZAMIENTO E INSERCIÓN INICIAL</h2>
            <p class="serif-narrative narrative-lead">
              Secuencia de ignición principal activada. El motor comprobará la restricción física
              crítica de masa de lanzamiento ({{ mission.masa_total_kg }} kg frente al límite fijo de
              {{ mission.masa_lanzamiento_max_kg }} kg) y el Delta-v de ascenso ({{
                currentDestinationInfo?.delta_v_lanzamiento_ms
              }}
              m/s). Pulsa «Avanzar Etapa» para ejecutar el despegue.
            </p>
          </section>

          <!-- ETAPA 6: TRÁNSITO -->
          <section v-if="mission.etapa_actual === 6" class="panel-box stage-panel">
            <h2 class="stage-heading">ETAPA 6 — CRUCERO Y TRÁNSITO ORBITAL</h2>
            <p class="serif-narrative narrative-lead">
              La nave navega en el vacío hacia {{ mission.destino }}. Camina por las habitaciones en
              el escenario 2D superior y resuelve cualquier anomalía decidiendo si emplear trabajo de
              la tripulación, presupuesto de energía a bordo o presupuesto financiero desde Tierra.
            </p>
          </section>

          <!-- ETAPAS 7, 8, 9: GUÍA DE OPERACIONES EN EL ESCENARIO 2D -->
          <section v-if="mission.etapa_actual >= 7 && mission.etapa_actual <= 9" class="panel-box stage-panel">
            <h2 class="stage-heading">
              ETAPA {{ mission.etapa_actual }} — {{ mission.nombre_etapa.toUpperCase() }}
            </h2>
            <p class="serif-narrative narrative-lead">
              Usa el <strong>Escenario 2D Pixel Art</strong> de arriba: desplázate con
              <code>←</code> / <code>→</code> (o <code>A</code> / <code>D</code>) y pulsa la tecla
              <strong><code>E</code></strong> frente a las puertas para cambiar de sala o frente a
              las terminales del Laboratorio, Módulo de Vida y Sala de Sistemas.
            </p>
          </section>

          <!-- CONSOLA DE EVENTOS ACTIVOS Y ALERTAS SIN CUANTIFICAR -->
          <section v-if="mission.eventos_activos.length > 0" class="panel-box events-panel">
            <h3 class="event-heading">
              ▲ EVENTOS Y ANOMALÍAS ACTIVAS (MENSAJES DE ALERTA SIN CUANTIFICAR)
            </h3>
            <div v-for="ev in mission.eventos_activos" :key="ev.id" class="event-card">
              <div class="event-top">
                <span class="event-title">{{ ev.titulo }}</span>
                <span class="badge" style="border-color: var(--orange); color: var(--orange)">
                  Subsistema: {{ ev.subsistema_afectado.toUpperCase() }}
                </span>
              </div>
              <p class="serif-narrative event-alert">{{ ev.mensaje_alerta }}</p>
              <div v-if="ev.diagnosticado_por_tierra" class="earth-feedback">
                <strong>RETROALIMENTACIÓN DE TIERRA:</strong> {{ ev.diagnostico_detallado }}
              </div>
              <div class="event-options">
                <button
                  v-for="opt in ev.opciones"
                  :key="opt.id"
                  class="opt-btn"
                  @click="handleResolveEvent(ev.id, opt.id)"
                >
                  <div>{{ opt.texto }}</div>
                  <div class="opt-costs">
                    <span v-if="opt.costo_presupuesto_usd > 0">
                      -${{ opt.costo_presupuesto_usd.toLocaleString() }} USD
                    </span>
                    <span v-if="opt.costo_energia_wh > 0">-{{ opt.costo_energia_wh }} Wh</span>
                    <span v-if="opt.costo_delta_v_ms > 0">-{{ opt.costo_delta_v_ms }} m/s Δv</span>
                    <span v-if="opt.consume_ventana_comm">-1 Ventana Comm</span>
                  </div>
                </button>
              </div>
            </div>
          </section>

          <!-- Botón de Avance de Etapa -->
          <div class="stage-footer-bar">
            <button class="btn-primary advance-btn" :disabled="loading" @click="advanceStage">
              {{
                mission.etapa_actual < 9
                  ? `Confirmar y Avanzar a Etapa ${mission.etapa_actual + 1} ►`
                  : 'Ejecutar Maniobra de Retorno y Evaluación Final ►'
              }}
            </button>
          </div>
        </div>

        <!-- COLUMNA DERECHA: Nave Visual + Tabla Explícita de Variables Afectadas -->
        <div class="right-column">
          <ShipSchematic :mission="mission" :catalog="catalog.componentes" />

          <!-- TABLA DE VISIBILIDAD DE CONSECUENCIAS (Valores explícitos sin advertir del desastre) -->
          <div class="panel-box variables-panel">
            <div class="var-header">
              <span class="label-amber">TABLA DE VARIABLES DE LA NAVE (VALORES EXPLÍCITOS)</span>
              <p class="var-note">
                El simulador expone los datos físicos reales resultantes de tus decisiones sin emitir
                juicios preventivos. Interpreta las magnitudes antes de despegar.
              </p>
            </div>

            <table class="tech-table">
              <thead>
                <tr>
                  <th>Parámetro</th>
                  <th>Valor Actual</th>
                  <th>Referencia / Capacidad</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Presupuesto Global</td>
                  <td style="color: var(--gold)">
                    ${{ mission.presupuesto_restante_usd.toLocaleString() }} USD
                  </td>
                  <td>Inicial: ${{ mission.presupuesto_inicial_usd.toLocaleString() }} USD</td>
                </tr>
                <tr>
                  <td>Masa Total (m₀)</td>
                  <td>{{ mission.masa_total_kg }} kg</td>
                  <td>Máx. Lanzador: {{ mission.masa_lanzamiento_max_kg }} kg</td>
                </tr>
                <tr>
                  <td>Delta-v Disponible</td>
                  <td style="color: var(--cyan)">{{ mission.delta_v_disponible_ms }} m/s</td>
                  <td>Est. Misión: {{ mission.delta_v_requerido_total_ms }} m/s</td>
                </tr>
                <tr>
                  <td>Potencia (Gen / Cons)</td>
                  <td>
                    {{ mission.generacion_w }} W / {{ mission.consumo_w }} W ({{
                      mission.balance_potencia_w >= 0
                        ? `+${mission.balance_potencia_w}`
                        : mission.balance_potencia_w
                    }}
                    W)
                  </td>
                  <td>Batería: {{ mission.bateria_actual_wh }} Wh</td>
                </tr>
                <tr>
                  <td>Soporte Vital (O₂ / Raciones)</td>
                  <td>{{ mission.o2_dias_disponibles }} días</td>
                  <td>Tránsito + Destino: {{ mission.dias_transito + mission.dias_en_destino }} d</td>
                </tr>
                <tr>
                  <td>Datos y Ventanas Comm</td>
                  <td>
                    {{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB
                  </td>
                  <td>
                    {{ mission.ventanas_comm_restantes }} ventanas ({{
                      Math.round(mission.probabilidad_enlace_comm * 100)
                    }}% enlace)
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Último impacto de decisión (Delta explícito) -->
            <div v-if="mission.ultimos_cambios_variables.length > 0" class="delta-section">
              <div class="delta-title">IMPACTO DE LA ÚLTIMA DECISIÓN:</div>
              <table class="tech-table delta-table">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Antes</th>
                    <th>Después</th>
                    <th>Δ Cambio</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="chg in mission.ultimos_cambios_variables" :key="chg.variable">
                    <td>{{ chg.etiqueta }}</td>
                    <td>{{ chg.valor_anterior }} {{ chg.unidad }}</td>
                    <td>{{ chg.valor_nuevo }} {{ chg.unidad }}</td>
                    <td
                      :style="{
                        color:
                          chg.delta > 0
                            ? 'var(--cyan)'
                            : chg.delta < 0
                              ? 'var(--amber)'
                              : 'var(--mist)',
                      }"
                    >
                      {{ chg.delta > 0 ? `+${chg.delta}` : chg.delta }} {{ chg.unidad }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.zenit-shell {
  max-width: 1380px;
  margin: 0 auto;
  padding: 18px 22px 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  border-bottom: 1px solid var(--steel);
  padding-bottom: 10px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-title {
  color: var(--gold);
  font-size: 20px;
  letter-spacing: 0.03em;
}
.brand-sub {
  color: var(--mist);
  font-size: 12px;
}
.stage-indicator {
  background: var(--cabin);
  border: 1px solid var(--amber);
  border-radius: 5px;
  padding: 6px 12px;
  text-align: right;
}
.stage-step {
  font-size: 10px;
  color: var(--amber);
  display: block;
  font-weight: 700;
}
.stage-name {
  font-size: 13px;
  color: var(--bone);
  font-weight: 600;
}
.stages-track {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 5px;
}
.stage-segment {
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 3px;
  color: var(--mist);
}
.stage-segment.done {
  background: var(--cabin);
  border-color: var(--cyan);
  color: var(--cyan);
}
.stage-segment.current {
  background: var(--amber);
  border-color: var(--gold);
  color: var(--void);
  font-weight: 700;
}
.status-banner {
  padding: 9px 14px;
  border-radius: 5px;
  font-size: 12px;
  border-left: 4px solid var(--cyan);
  background: var(--cabin);
}
.banner-ok {
  border-left-color: var(--cyan);
}
.banner-warn {
  border-left-color: var(--orange);
  color: var(--gold);
}
.banner-fail {
  border-left-color: var(--red);
  color: var(--red);
}
.main-workspace {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 16px;
  align-items: start;
}
@media (max-width: 1024px) {
  .main-workspace {
    grid-template-columns: 1fr;
  }
}
.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.stage-character-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.stage-heading {
  color: var(--amber);
  font-size: 16px;
  margin-bottom: 6px;
}
.narrative-lead {
  font-size: 15px;
  color: var(--bone);
  margin-bottom: 14px;
  line-height: 1.6;
}
.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
.choice-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.choice-card:hover {
  border-color: var(--cyan);
}
.choice-card.selected {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.08);
}
.choice-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.choice-title {
  color: var(--gold);
  font-weight: 700;
  font-size: 14px;
}
.choice-desc {
  font-size: 14px;
  color: var(--bone);
  margin-bottom: 8px;
}
.tech-specs-mini {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: var(--cyan);
}
.cat-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}
.comp-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.comp-card.installed {
  border-color: var(--cyan);
}
.cand-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.comp-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 700;
}
.comp-title {
  color: var(--bone);
}
.comp-price {
  color: var(--amber);
}
.comp-desc {
  font-size: 11px;
  color: var(--mist);
  line-height: 1.4;
}
.ficha-tecnica {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 10px;
  color: var(--cyan);
  background: rgba(27, 35, 64, 0.6);
  padding: 6px;
  border-radius: 4px;
}
.comp-actions {
  margin-top: auto;
  padding-top: 6px;
}
.installed-tag {
  font-size: 11px;
  color: var(--green);
  font-weight: 700;
}
.crew-recruitment {
  margin-top: 18px;
  border-top: 1px solid var(--steel);
  padding-top: 14px;
}
.sub-heading {
  font-size: 13px;
  color: var(--amber);
  margin-bottom: 4px;
}
.events-panel {
  border-color: var(--orange);
}
.event-heading {
  color: var(--orange);
  font-size: 13px;
  margin-bottom: 10px;
}
.event-card {
  background: var(--void);
  border: 1px solid var(--orange);
  border-radius: 5px;
  padding: 12px;
  margin-bottom: 10px;
}
.event-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.event-title {
  color: var(--gold);
  font-weight: 700;
  font-size: 13px;
}
.event-alert {
  font-size: 14px;
  color: var(--bone);
  margin-bottom: 10px;
}
.earth-feedback {
  background: rgba(79, 209, 197, 0.12);
  border-left: 3px solid var(--cyan);
  padding: 8px;
  font-size: 11px;
  color: var(--cyan);
  margin-bottom: 10px;
}
.event-options {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}
.opt-btn {
  text-align: left;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.opt-costs {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: var(--amber);
  white-space: nowrap;
}
.stage-footer-bar {
  display: flex;
  justify-content: flex-end;
}
.advance-btn {
  padding: 10px 18px;
  font-size: 13px;
}
.label-amber {
  color: var(--amber);
  font-weight: 700;
  font-size: 13px;
}
.var-note {
  font-size: 11px;
  color: var(--mist);
  margin: 4px 0 10px;
}
.tech-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.tech-table th,
.tech-table td {
  border: 1px solid var(--steel);
  padding: 6px 8px;
  text-align: left;
}
.tech-table th {
  background: var(--void);
  color: var(--mist);
}
.delta-section {
  margin-top: 12px;
}
.delta-title {
  font-size: 11px;
  color: var(--cyan);
  font-weight: 700;
  margin-bottom: 6px;
}
</style>
