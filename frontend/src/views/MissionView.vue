<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import TypewriterText from '../components/TypewriterText.vue'
import TutorialOverlay from '../components/TutorialOverlay.vue'
import type { PasoTutorial } from '../components/TutorialOverlay.vue'
import BossReportScene from '../components/BossReportScene.vue'
import DestinationRooms2D from '../components/DestinationRooms2D.vue'
import GameMainMenu from '../components/GameMainMenu.vue'
import PixelSprite, { obtenerSpriteTripulante } from '../components/PixelSprite.vue'
import ShipSchematic from '../components/ShipSchematic.vue'
import VisualNovelNegotiation from '../components/VisualNovelNegotiation.vue'
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

function leerPreferenciaTutorial(): boolean {
  try {
    return localStorage.getItem('zenit_tutorial_activo') !== '0'
  } catch {
    return true
  }
}

// Menú de Inicio y control de decisiones explícitas sin preselecciones visibles
const showMainMenu = ref<boolean>(true)
const tutorialActivo = ref<boolean>(leerPreferenciaTutorial())
const tutorialVisible = ref<boolean>(false)
const tutorialPaso = ref<number>(0)

const selectedDifficulty = ref<DificultadId>('facil')
const selectedInitialDest = ref<DestinoId>('OTB')
const customMissionName = ref<string>('Expedición Zenit-1')
const etapa1DestinoElegido = ref<boolean>(false)
const etapa4TrayectoriaElegida = ref<boolean>(false)

const difficultyOptions: Array<{
  id: DificultadId
  title: string
  badge: string
  desc: string
  perks: string[]
}> = [
  {
    id: 'facil',
    title: 'Modo Cadete (Fácil)',
    badge: 'ACCESIBLE',
    desc: 'Ideal para familiarizarse con los sistemas, recolectar ciencia y transmitir datos con mayor margen.',
    perks: [
      '+35% de presupuesto financiero inicial (168.750 CZ en plan estándar)',
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
      'Presupuesto nominal (125.000 CZ en acuerdo estándar)',
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

// Modos del visor izquierdo y sub-pestañas de la Etapa 3
// La negociación ('office_vn') solo aparece en la Etapa 2; Etapas 1 y 3-5 usan 'schematic' (Hangar); 6+ usa 'rooms2d'
const activeViewportTab = ref<'office_vn' | 'rooms2d' | 'schematic' | 'telemetry'>('schematic')
const isFullStageVn = computed(
  () => Boolean(mission.value && mission.value.etapa_actual === 2 && activeViewportTab.value === 'office_vn'),
)
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

const etiquetaContextoTutorial = computed<string>(() => {
  if (finalReport.value) return 'ETAPA 10 DE 10 · VEREDICTO FINAL'
  if (!mission.value) return 'GUÍA REACTIVA'
  return `ETAPA ${mission.value.etapa_actual} DE 10`
})

// Tutorial estrictamente coherente con la etapa y pestaña activas (sin adelantar etapas futuras)
const pasosTutorialActuales = computed<PasoTutorial[]>(() => {
  if (showMainMenu.value) return []
  if (finalReport.value) {
    return [
      {
        selector: '[data-tutorial="final"]',
        posicion: 'top',
        titulo: 'Veredicto del Comité Zenit',
        descripcion:
          'Revisa tu evaluación en las 7 dimensiones y consulta el dictamen del Gato Jefe y sus dos ayudantes.',
      },
    ]
  }
  const m = mission.value
  if (!m) return []

  if (m.etapa_actual === 1) {
    if (activeViewportTab.value === 'telemetry') {
      return [
        {
          selector: '[data-tutorial="variables-sheet"], [data-tutorial="viewport"]',
          posicion: 'right',
          titulo: 'Etapa 1 · Pestaña Variables',
          descripcion:
            'Aquí ves el detalle físico de la misión. Cambia a «🚀 Hangar: Nave y Perros» arriba o elige destino en el panel derecho para continuar.',
        },
      ]
    }
    if (!etapa1DestinoElegido.value) {
      return [
        {
          selector: '[data-tutorial="stage1-options"], [data-tutorial="command"]',
          posicion: 'left',
          titulo: 'Etapa 1 · Elige el destino de la misión',
          descripcion:
            'Selecciona OTB (400 km) o Luna (384.400 km) en este panel. Hasta que elijas un destino no se habilitará el avance a la Etapa 2.',
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="advance-btn"], [data-tutorial="telemetry"]',
        posicion: 'left',
        titulo: 'Etapa 1 · ¡Destino fijado!',
        descripcion:
          'Mira cómo se actualizó tu Delta-v requerido arriba. Cuando estés listo, pulsa «Avanzar a Etapa 2 ►» para ir a negociar presupuesto.',
      },
    ]
  }

  if (m.etapa_actual === 2) {
    if (activeViewportTab.value !== 'office_vn') {
      return [
        {
          selector: '[data-tutorial="tab-office"], [data-tutorial="viewport"]',
          posicion: 'bottom',
          titulo: 'Etapa 2 · Abre la Oficina de Planificación',
          descripcion:
            'Estás en otra pestaña del visor. Haz clic en «🏢 Oficina Planificación» arriba para negociar el presupuesto de la Etapa 2.',
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="telemetry"]',
        posicion: 'bottom',
        titulo: 'Etapa 2 · Negociación con el Comité',
        descripcion:
          'Responde en la escena de la Oficina (hasta 3 rondas). Tus argumentos reales suben o recortan tus Créditos Zenit (CZ) arriba antes de diseñar la nave.',
      },
    ]
  }

  if (m.etapa_actual === 3) {
    if (activeViewportTab.value === 'telemetry') {
      return [
        {
          selector: '[data-tutorial="variables-sheet"], [data-tutorial="viewport"]',
          posicion: 'right',
          titulo: 'Etapa 3 · Variables del diseño',
          descripcion:
            'Consulta aquí masa, Delta-v y balance eléctrico al instante, o vuelve a «🚀 Hangar: Nave y Perros» para ver el montaje en el chasis.',
        },
      ]
    }
    if (stage3SubTab.value === 'crew') {
      return [
        {
          selector: '[data-tutorial="stage3-panel"], [data-tutorial="command"]',
          posicion: 'left',
          titulo: 'Etapa 3 · Tripulación canina',
          descripcion:
            'Contrata especialistas según su rol (Ciencia, Ingeniería o Medicina), o viaja en solitario ahorrando masa y CZ. Al terminar, pulsa «Avanzar a Etapa 4 ►».',
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="stage3-panel"], [data-tutorial="command"]',
        posicion: 'left',
        titulo: 'Etapa 3 · Equipa tu nave en el Hangar',
        descripcion: `Instala motor, energía, antena e instrumentos sin superar ${m.masa_lanzamiento_max_kg} kg. Revisa también «🐶 2. Tripulación» antes de avanzar.`,
      },
    ]
  }

  if (m.etapa_actual === 4) {
    if (!etapa4TrayectoriaElegida.value) {
      return [
        {
          selector: '[data-tutorial="stage4-options"], [data-tutorial="command"]',
          posicion: 'left',
          titulo: 'Etapa 4 · Selecciona trayectoria',
          descripcion:
            'Elige Transferencia Estándar o Directa Rápida (+18% Δv). Hasta confirmar una trayectoria aquí no podrás avanzar al lanzamiento.',
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="advance-btn"], [data-tutorial="telemetry"]',
        posicion: 'left',
        titulo: 'Etapa 4 · Trayectoria confirmada',
        descripcion:
          'Verifica en la barra superior que tu Delta-v disponible cubra el requerido y pulsa «Avanzar a Etapa 5 ►».',
      },
    ]
  }

  if (m.etapa_actual === 5) {
    return [
      {
        selector: '[data-tutorial="advance-btn"], [data-tutorial="telemetry"]',
        posicion: 'left',
        titulo: 'Etapa 5 · Verificación de lanzamiento',
        descripcion: `Última revisión en plataforma: comprueba masa (≤ ${m.masa_lanzamiento_max_kg} kg) y Delta-v suficiente arriba, y pulsa «Avanzar a Etapa 6 ►» para despegar.`,
      },
    ]
  }

  if (m.etapa_actual === 6) {
    if (m.eventos_activos.length > 0) {
      return [
        {
          selector: '[data-tutorial="events-drawer"], [data-tutorial="command"]',
          posicion: 'left',
          titulo: 'Etapa 6 · Resuelve anomalías de vuelo',
          descripcion:
            'Tienes alertas activas en tránsito. Elige una respuesta del Capitán Perro gastando batería, tripulación o CZ antes de continuar.',
        },
      ]
    }
    if (activeViewportTab.value !== 'rooms2d') {
      return [
        {
          selector: '[data-tutorial="tab-rooms2d"], [data-tutorial="viewport"]',
          posicion: 'bottom',
          titulo: 'Etapa 6 · Cubierta 2D desbloqueada',
          descripcion:
            'La nave ya está en vuelo. Abre «🎮 Cubierta 2D en Vuelo [E]» arriba para recorrer las salas con A/D o avanza a Etapa 7 si no hay alertas.',
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="advance-btn"], [data-tutorial="viewport-body"]',
        posicion: 'left',
        titulo: 'Etapa 6 · Tránsito en ruta',
        descripcion:
          'Sin alertas activas: explora las salas en Cubierta 2D o pulsa «Avanzar a Etapa 7 ►» para entrar en órbita científica.',
      },
    ]
  }

  if (m.etapa_actual >= 7 && m.etapa_actual <= 9) {
    if (activeViewportTab.value !== 'rooms2d') {
      return [
        {
          selector: '[data-tutorial="tab-rooms2d"], [data-tutorial="viewport"]',
          posicion: 'bottom',
          titulo: `Etapa ${m.etapa_actual} · Vuelve a la Cubierta 2D`,
          descripcion:
            'Las operaciones en destino ocurren dentro de «🎮 Cubierta 2D en Vuelo [E]». Cambia a esa pestaña o usa los accesos rápidos de la derecha.',
        },
      ]
    }
    if (m.datos_generados_gb === 0) {
      return [
        {
          selector: '[data-tutorial="viewport-body"], [data-tutorial="command"]',
          posicion: 'right',
          titulo: `Etapa ${m.etapa_actual} · Paso 1: Recolecta ciencia`,
          descripcion:
            'Camina con A/D al Laboratorio Científico y pulsa [E] en la consola (o usa «PASO 1» a la derecha) para recolectar datos.',
        },
      ]
    }
    if (pendingDataToTransmitGb.value > 0) {
      return [
        {
          selector: '[data-tutorial="viewport-body"], [data-tutorial="command"]',
          posicion: 'right',
          titulo: `Etapa ${m.etapa_actual} · Paso 2: Transmite a Tierra`,
          descripcion: `Tienes ${pendingDataToTransmitGb.value} GB recolectados. Ve a Sala de Sistemas y pulsa [E] en la antena (o «PASO 2» a la derecha) para enviarlos.`,
        },
      ]
    }
    return [
      {
        selector: '[data-tutorial="advance-btn"], [data-tutorial="command"]',
        posicion: 'left',
        titulo: `Etapa ${m.etapa_actual} · Datos transmitidos`,
        descripcion: `Ya enviaste ${m.datos_transmitidos_gb} GB a Tierra. Puedes cuidar el ánimo del equipo o pulsar para avanzar a la siguiente etapa.`,
      },
    ]
  }

  return [
    {
      selector: '[data-tutorial="final"], [data-tutorial="deltabar"]',
      posicion: 'top',
      titulo: 'Etapa 10 · Cierre e informe final',
      descripcion:
        'Pulsa el botón de retorno para presentar el informe completo ante el Comité de los 3 Gatos.',
    },
  ]
})

const hasScientificInstrumentInstalled = computed(() => {
  if (!mission.value || !catalog.value) return false
  return mission.value.componentes_instalados.some((cid) => {
    const found = catalog.value?.componentes.find((c) => c.id === cid)
    return found && (found.categoria === 'instrumento' || found.categoria === 'robot')
  })
})

const hiredSpecialists = computed(() => {
  if (!mission.value) return []
  return mission.value.tripulacion.filter((t) => !t.es_jugador)
})

// Crónica narrativa reactiva (Trama "Expediente Helios-9") según etapa, destino y tripulación
const currentStoryBeat = computed(() => {
  if (!mission.value) return null
  const st = mission.value.etapa_actual
  const isLuna = mission.value.destino === 'LUNA'
  const crewNames = hiredSpecialists.value.map((t) => t.nombre).join(', ')
  const solo = hiredSpecialists.value.length === 0

  if (st === 1) {
    return {
      chapter: 'CAPÍTULO I · EL APAGÓN HELIOS-9',
      speaker: 'GATO JEFE · COMISIONADO FÉLIX VANCE',
      speakerIcon: '/sprites/iconos/icono_gato_jefe.png',
      quote: isLuna
        ? '«Tras la tormenta solar Helios-9 perdimos contacto con todas las sondas automáticas del polo sur lunar. Has elegido la Operación Cráter Shackleton: bajo ese hielo perpetuo hay una firma isotópica que ningún robot pudo descifrar. Necesito que vayas allá arriba y traigas la verdad.»'
        : '«La tormenta solar Helios-9 dejó ciega nuestra red de satélites automáticos y abrió una brecha en la magnetosfera superior. Con la Operación Escudo Ionosférico en OTB (400 km), tu misión es medir la anomalía desde primera línea antes de la siguiente llamarada.»',
    }
  }
  if (st === 2) {
    return null
  }
  if (st === 3) {
    return {
      chapter: 'CAPÍTULO III · ENSAMBLAJE EN EL HANGAR 04',
      speaker: solo ? 'CAPITÁN PERRO (EN SOLITARIO)' : `DOTACIÓN CANINA (${crewNames})`,
      speakerIcon: '/sprites/iconos/icono_perro_director.png',
      quote: solo
        ? 'Actualmente estás tú solo en el manifiesto de vuelo (1/4). Puedes despegar en solitario para ahorrar sueldos y masa, pero sufrirás fatiga psicológica por aislamiento y menor velocidad en el Laboratorio. ¡Revisa la pestaña "🐶 2. Tripulación" si deseas contratar especialistas!'
        : `Tu dotación canina (${crewNames}) ya revisa los planos en el hangar. Con ${mission.value.tripulacion.length} tripulantes a bordo, la nave registra ${mission.value.masa_total_kg} kg frente al límite estructural de ${mission.value.masa_lanzamiento_max_kg} kg.`,
    }
  }
  if (st === 4) {
    return {
      chapter: 'CAPÍTULO IV · VENTANA DE TRANSFERENCIA',
      speaker: 'ASESOR NEGRO (RIESGO Y ASTRODINÁMICA)',
      speakerIcon: '/sprites/iconos/icono_gato_asistente_negro.png',
      quote: isLuna
        ? `La Luna se alinea sobre el plano orbital. La inyección translunar exige al menos ${mission.value.delta_v_requerido_total_ms} m/s totales; tu propulsor cuenta con ${mission.value.delta_v_disponible_ms} m/s.`
        : `Ventana de inserción hacia la termosfera (400 km) calculada. Se requieren ${mission.value.delta_v_requerido_total_ms} m/s para completar ascenso, órbita y reentrada.`,
    }
  }
  if (st === 5) {
    return {
      chapter: 'CAPÍTULO V · CUENTA REGRESIVA EN RAMPA',
      speaker: 'AUDITORA BLANCA (CONTROL DE TIERRA)',
      speakerIcon: '/sprites/iconos/icono_gato_asistente_blanco.png',
      quote: solo
        ? '«Torre de lanzamiento despejada. El Director despega en misión en solitario. Presurización de cabina nominal; motores listos para ignición.»'
        : `«Torre de lanzamiento despejada. Dotación completa (${crewNames}) asegurada en cabina. Todos los sistemas listos para ignición.»`,
    }
  }
  if (st === 6) {
    return {
      chapter: 'CAPÍTULO VI · EL SILENCIO DEL CRUCERO',
      speaker: solo ? 'CAPITÁN PERRO (EN SOLITARIO)' : 'CAPITÁN PERRO Y TRIPULACIÓN',
      speakerIcon: '/sprites/iconos/icono_captain_dog_casco.png',
      quote: solo
        ? `Viajas completamente solo a través del vacío rumbo a ${mission.value.destino}. El zumbido del soporte vital es tu única compañía mientras vigilas las alertas de los subsistemas.`
        : `La Tierra se empequeñece tras la ventanilla mientras ${crewNames} supervisan la presión de los conductos y la carga de baterías rumbo a ${mission.value.destino}.`,
    }
  }
  if (st === 7) {
    return {
      chapter: 'CAPÍTULO VII · EL HALLAZGO EN ÓRBITA',
      speaker: 'CAPITÁN PERRO · LABORATORIO DE LA NAVE',
      speakerIcon: '/sprites/iconos/icono_captain_dog_casco.png',
      quote:
        mission.value.datos_generados_gb > 0
          ? `¡Los sensores han capturado la firma del fenómeno Helios-9 (${mission.value.datos_generados_gb} GB en memoria y ${mission.value.puntos_ciencia_generados} pts de ciencia)! El siguiente paso crítico es enviarlos por antena a Tierra.`
          : isLuna
            ? 'Bajo la sombra perpetua del Cráter Shackleton, los sensores detectan ecos cristalinos e isótopos solares atrapados en el hielo. ¡Activa el Laboratorio (Paso 1) para registrar el hallazgo!'
            : 'Las auroras de alta energía envuelven el casco a 400 km de altitud. Las partículas del evento Helios-9 están justo frente a nosotros. ¡Activa el Laboratorio (Paso 1) para capturar los datos!',
    }
  }
  if (st === 8) {
    return {
      chapter: 'CAPÍTULO VIII · DESGASTE EN EL ESPACIO PROFUNDO',
      speaker: solo ? 'MONITOR BIOMÉDICO (SOLITARIO)' : 'MÓDULO DE VIDA Y OPERACIONES',
      speakerIcon: '/sprites/iconos/icono_perro_director.png',
      quote: solo
        ? 'El aislamiento de operar toda la nave sin ayuda empieza a pesar en tus reflejos. Mantén el ánimo en Sol y asegúrate de no dejar datos sin transmitir.'
        : `Tras intensas jornadas en órbita, el equipo (${crewNames}) ajusta el reciclaje de oxígeno y calibra las válvulas antes de la última ventana de enlace con Tierra.`,
    }
  }
  return {
    chapter: 'CAPÍTULO IX · ÚLTIMO ENLACE ANTES DE REENTRADA',
    speaker: 'GATO JEFE · COMISIONADO FÉLIX VANCE',
    speakerIcon: '/sprites/iconos/icono_gato_jefe.png',
    quote:
      mission.value.datos_transmitidos_gb > 0 && pendingDataToTransmitGb.value <= 0
        ? `«Aquí el Comisionado Vance desde Tierra: hemos recibido los ${mission.value.datos_transmitidos_gb} GB íntegros en nuestros servidores centrales. Enciendan motores de retorno y vuelvan a casa.»`
        : pendingDataToTransmitGb.value > 0
          ? `«¡Director, aún tienes ${pendingDataToTransmitGb.value} GB de datos guardados en la memoria de la nave! Usa la antena (Paso 2) ahora mismo; lo que no se transmita antes de reentrar no servirá para el informe.»`
          : '«Director, nuestras antenas en Tierra siguen esperando tus paquetes de telemetría científica. Recolecta en el Laboratorio (Paso 1) y transmite (Paso 2) antes de regresar.»',
  }
})

// Cambiar automáticamente al visor correspondiente según la etapa:
// Etapa 2: Oficina de Planificación (negociación novela visual con los 3 gatos); solo en esta etapa
// Etapas 1 y 3-5: Hangar en Tierra (Esquemático de Nave y Perros)
// Etapas 6+: Cubierta 2D en Vuelo
watch(
  () => mission.value?.etapa_actual,
  (etapa) => {
    if (etapa === 2) {
      activeViewportTab.value = 'office_vn'
    } else if (etapa && etapa >= 6) {
      activeViewportTab.value = 'rooms2d'
    } else {
      activeViewportTab.value = 'schematic'
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

async function handleMenuStart(payload: {
  nombre_mision: string
  destino: DestinoId
  dificultad: DificultadId
}): Promise<void> {
  customMissionName.value = payload.nombre_mision
  selectedInitialDest.value = payload.destino
  selectedDifficulty.value = payload.dificultad
  await startNewMission(true)
}

function iniciarTutorial(): void {
  tutorialActivo.value = true
  try {
    localStorage.setItem('zenit_tutorial_activo', '1')
  } catch {
    // Ignorar entornos sin localStorage.
  }
  sincronizarTutorial()
}

function sincronizarTutorial(): void {
  if (!tutorialActivo.value || showMainMenu.value) {
    tutorialVisible.value = false
    return
  }
  tutorialPaso.value = 0
  if (finalReport.value || mission.value) {
    tutorialVisible.value = true
  }
}

function desactivarTutorial(): void {
  tutorialActivo.value = false
  tutorialVisible.value = false
  try {
    localStorage.setItem('zenit_tutorial_activo', '0')
  } catch {
    // Ignorar entornos sin localStorage.
  }
}

watch(showMainMenu, () => sincronizarTutorial())
watch(() => mission.value?.etapa_actual, () => sincronizarTutorial(), { immediate: true })
watch(() => Boolean(finalReport.value), () => sincronizarTutorial())
watch(pasosTutorialActuales, () => {
  tutorialPaso.value = 0
})

async function startNewMission(fromMenu = false): Promise<void> {
  loading.value = true
  finalReport.value = null
  etapa1DestinoElegido.value = false
  etapa4TrayectoriaElegida.value = false
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
    activeViewportTab.value = 'schematic'
    if (fromMenu) {
      showMainMenu.value = false
    }
    statusMessage.value = `Misión iniciada en dificultad ${selectedDifficulty.value.toUpperCase()}.`
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
    <!-- MENÚ PRINCIPAL ESTILO VIDEOJUEGO PIXEL ART                              -->
    <!-- ======================================================================= -->
    <GameMainMenu
      v-if="showMainMenu"
      :loading="loading"
      :has-active-mission="Boolean(mission)"
      :error-message="lastStatusType === 'fail' ? statusMessage : null"
      :initial-mission-name="customMissionName"
      :initial-destination="selectedInitialDest"
      :initial-difficulty="selectedDifficulty"
      :difficulty-options="difficultyOptions"
      @start="handleMenuStart"
      @resume="showMainMenu = false"
    />

    <!-- ======================================================================= -->
    <!-- 1. CINTA SUPERIOR DE TELEMETRÍA Y PROGRESO DE ETAPAS (FIJA Y COMPACTA)  -->
    <!-- ======================================================================= -->
    <header class="top-ribbon">
      <div class="brand-cluster">
        <button class="menu-trigger-btn" @click="showMainMenu = true">
          ☰ MENÚ / DIFICULTAD
        </button>
        <button v-if="mission" class="menu-trigger-btn" @click="iniciarTutorial">
          AYUDA / TUTORIAL
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
      <nav v-if="mission" class="timeline-10" data-tutorial="timeline" aria-label="Progreso de etapas de la misión">
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
      <div v-if="mission" class="telemetry-pills" data-tutorial="telemetry">
        <div class="tpill">
          <span class="tpill-label">CRÉDITOS ZENIT</span>
          <strong class="tpill-val" style="color: var(--gold)">
            {{ mission.presupuesto_restante_usd.toLocaleString() }} CZ
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
    <main v-if="finalReport" class="final-report-viewport" data-tutorial="final">
      <BossReportScene :report="finalReport" @restart="showMainMenu = true" />
    </main>

    <!-- ======================================================================= -->
    <!-- ESTACIÓN DE TRABAJO DE DOBLE PANEL (SIN SCROLL DE PÁGINA COMPLETA)      -->
    <!-- ======================================================================= -->
    <main
      v-else-if="mission && catalog"
      class="split-workstation"
      :class="{ 'full-vn-focus': isFullStageVn }"
    >
      <!-- PANEL IZQUIERDO (58%): VISOR INTERACTIVO MULTIMODO + CHIPS DE IMPACTO -->
      <section class="left-viewport-column">
        <!-- Conmutador de Vista Principal -->
        <div class="viewport-switcher" data-tutorial="viewport">
          <button
            v-if="mission.etapa_actual === 2"
            data-tutorial="tab-office"
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'office_vn' }"
            @click="activeViewportTab = 'office_vn'"
          >
            🏢 Oficina Planificación (Gato Jefe y 2 Ayudantes)
          </button>
          <button
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'schematic' }"
            @click="activeViewportTab = 'schematic'"
          >
            🚀 {{ mission.etapa_actual <= 5 ? 'Hangar: Nave y Perros' : 'Esquemático de Nave y Perros' }}
          </button>
          <button
            data-tutorial="tab-rooms2d"
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'rooms2d' }"
            :disabled="mission.etapa_actual < 6"
            :title="
              mission.etapa_actual < 6
                ? 'La cubierta interior 2D se habilita cuando la nave despega (Etapa 6 en adelante)'
                : 'Recorre el interior de la nave en vuelo con A/D y E'
            "
            @click="mission.etapa_actual >= 6 && (activeViewportTab = 'rooms2d')"
          >
            {{
              mission.etapa_actual < 6
                ? '🔒 Cubierta 2D (Etapa 6+)'
                : '🎮 Cubierta 2D en Vuelo [E]'
            }}
          </button>
          <button
            class="vtab-btn"
            :class="{ active: activeViewportTab === 'telemetry' }"
            @click="activeViewportTab = 'telemetry'"
          >
            📊 Variables
          </button>
        </div>

        <!-- Contenido del Visor Activo -->
        <div class="viewport-stage-body" data-tutorial="viewport-body">
          <VisualNovelNegotiation
            v-if="activeViewportTab === 'office_vn' && mission.etapa_actual === 2"
            :mission="mission"
            @negotiate="(payload) => executeDecision('negociar_presupuesto', payload)"
            @finish-negotiation="advanceStage"
          />

          <DestinationRooms2D
            v-else-if="activeViewportTab === 'rooms2d'"
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
          <div v-else class="panel-box full-telemetry-sheet" data-tutorial="variables-sheet">
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
                  <td>Presupuesto Global (Créditos Zenit)</td>
                  <td style="color: var(--gold)">
                    {{ mission.presupuesto_restante_usd.toLocaleString() }} CZ
                  </td>
                  <td>Inicial: {{ mission.presupuesto_inicial_usd.toLocaleString() }} CZ</td>
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
          data-tutorial="deltabar"
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

      <!-- PANEL DERECHO (42%): CONSOLA DE DECISIONES DE ETAPA (oculta durante novela visual enfocada) -->
      <aside v-if="!isFullStageVn" class="right-command-column" data-tutorial="command">
        <div class="command-scroll-area">
          <!-- CRÓNICA NARRATIVA DE LA TRAMA (solo cuando no estorba al visor 2D RPG) -->
          <div v-if="!showMainMenu && currentStoryBeat && activeViewportTab !== 'rooms2d'" class="story-chapter-box" data-tutorial="story">
            <div class="story-head">
              <span class="story-chapter-tag">{{ currentStoryBeat.chapter }}</span>
              <span class="story-speaker">{{ currentStoryBeat.speaker }}</span>
            </div>
            <div class="story-bubble-row">
              <img
                :src="currentStoryBeat.speakerIcon"
                :alt="currentStoryBeat.speaker"
                class="story-speaker-icon"
              />
              <p class="serif-narrative story-quote">
                <TypewriterText :text="currentStoryBeat.quote" :key="`story-${mission?.etapa_actual}-${mission?.destino}`" skip-hint="(clic para saltar)" />
              </p>
            </div>
          </div>

          <!-- ALERTAS Y EVENTOS ACTIVOS CON ICONO DE QUIÉN TOMA LA DECISIÓN (CAPTAIN DOG) -->
          <div v-if="mission.eventos_activos.length > 0" class="events-drawer" data-tutorial="events-drawer">
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
              <div class="event-decision-layout">
                <div class="event-btn-stack" style="flex: 1">
                  <div class="event-decision-tag">CAPITÁN PERRO · ELIGE ACCIÓN DE MANDO:</div>
                  <button
                    v-for="opt in ev.opciones"
                    :key="opt.id"
                    class="event-opt-button"
                    @click="handleResolveEvent(ev.id, opt.id)"
                  >
                    <span>&gt; {{ opt.texto }}</span>
                    <span class="opt-cost-pills">
                      <em v-if="opt.costo_presupuesto_usd > 0">
                        -{{ opt.costo_presupuesto_usd.toLocaleString() }} CZ
                      </em>
                      <em v-if="opt.costo_energia_wh > 0">-{{ opt.costo_energia_wh }} Wh</em>
                      <em v-if="opt.costo_delta_v_ms > 0">-{{ opt.costo_delta_v_ms }} m/s</em>
                      <em v-if="opt.consume_ventana_comm">-1 Ventana</em>
                    </span>
                  </button>
                </div>
                <div class="event-player-badge">
                  <img
                    src="/sprites/iconos/icono_captain_dog_casco.png"
                    alt="Captain Dog"
                    class="event-player-icon"
                  />
                  <span>CAPTAIN DOG</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ETAPA 1: DEFINICIÓN DE LA MISIÓN -->
          <div v-if="mission.etapa_actual === 1" class="stage-card">
            <div class="stage-hero-row">
              <img
                src="/sprites/iconos/icono_perro_director.png"
                alt="Capitán Perro"
                class="stage-framed-icon"
              />
              <div>
                <div class="stage-eyebrow">ETAPA 01 DE 10 · OFICINA DE PLANIFICACIÓN</div>
                <h2 class="stage-title">Definición de la Misión</h2>
                <p class="serif-narrative stage-prose">
                  Selecciona el destino de referencia para la expedición científica. La masa máxima
                  de lanzamiento es de {{ mission.masa_lanzamiento_max_kg }} kg.
                </p>
              </div>
            </div>

            <div class="option-list" data-tutorial="stage1-options">
              <div
                v-for="dest in catalog.destinos"
                :key="dest.id"
                class="option-tile"
                :class="{ selected: etapa1DestinoElegido && mission.destino === dest.id }"
                @click="
                  etapa1DestinoElegido = true;
                  executeDecision('seleccionar_destino', { destino: dest.id })
                "
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

          <!-- ETAPA 2: NEGOCIACIÓN TIPO NOVELA VISUAL (CON EL GATO JEFE Y SUS 2 AYUDANTES) -->
          <div v-if="mission.etapa_actual === 2" class="stage-card">
            <div class="stage-hero-row">
              <div class="cat-trio-icons">
                <img
                  src="/sprites/iconos/icono_gato_jefe.png"
                  alt="Gato Jefe"
                  class="stage-framed-icon"
                />
                <img
                  src="/sprites/iconos/icono_gato_asistente_blanco.png"
                  alt="Auditora Blanca"
                  class="stage-framed-icon"
                />
                <img
                  src="/sprites/iconos/icono_gato_asistente_negro.png"
                  alt="Asesor Negro"
                  class="stage-framed-icon"
                />
              </div>
              <div>
                <div class="stage-eyebrow">ETAPA 02 DE 10 · NOVELA VISUAL DE NEGOCIACIÓN</div>
                <h2 class="stage-title">Audiencia con el Gato Jefe y sus 2 Ayudantes</h2>
                <p class="serif-narrative stage-prose">
                  En la <strong>Oficina de Planificación (visor izquierdo)</strong>, argumenta ante el
                  <strong>Gato Jefe</strong>, la <strong>Auditora Blanca</strong> y el
                  <strong>Asesor Negro</strong> para convencerlos de subir tu presupuesto antes de
                  pasar al diseño de la nave.
                </p>
              </div>
            </div>

            <div class="vn-stage2-summary-card">
              <div class="vn-sum-row">
                <span>FONDOS NEGOCIADOS ACTUALES:</span>
                <strong style="color: var(--gold); font-size: 16px">
                  {{ mission.presupuesto_restante_usd.toLocaleString() }} CZ
                </strong>
              </div>
              <p class="vn-sum-hint">
                👈 Usa las opciones de diálogo <code>&gt; ...</code> en la escena de la
                <strong>Oficina de Planificación</strong> a la izquierda para persuadir a los 3
                gatos y sumar fondos adicionales.
              </p>
              <button
                v-if="activeViewportTab !== 'office_vn'"
                class="btn-primary btn-sm"
                @click="activeViewportTab = 'office_vn'"
              >
                🏢 Abrir Escena de Oficina de Planificación
              </button>
            </div>
          </div>

          <!-- ETAPA 3: DISEÑO DE LA NAVE Y SELECCIÓN DE PERSONAL (PERROS ESPECIALISTAS) -->
          <div v-if="mission.etapa_actual === 3" class="stage-card" data-tutorial="stage3-panel">
            <div class="stage-eyebrow">ETAPA 03 DE 10 · INGENIERÍA DE SISTEMAS</div>
            <h2 class="stage-title">Diseño de Nave y Tripulación Canina</h2>

            <!-- Indicador rápido de preparación de ciencia, tripulación y masa -->
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
                :class="mission.tripulacion.length > 1 ? 'pill-ok' : 'pill-warn'"
                style="cursor: pointer"
                @click="stage3SubTab = 'crew'"
              >
                {{
                  mission.tripulacion.length > 1
                    ? `✓ Dotación: ${mission.tripulacion.length}/4 Perros`
                    : '⚠ En Solitario (1/4) · Clic para contratar tripulación'
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
                    <span class="cat-item-cost">{{ comp.costo_usd.toLocaleString() }} CZ</span>
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
                      :animar="false"
                      :animo="cand.estado_animo"
                    />
                    <div style="flex: 1">
                      <div class="cat-row-top">
                        <span class="cat-item-name">{{ cand.nombre }}</span>
                        <span class="cat-item-cost">-{{ cand.salario_usd.toLocaleString() }} CZ</span>
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
            <div class="option-list" data-tutorial="stage4-options">
              <div
                class="option-tile"
                :class="{ selected: etapa4TrayectoriaElegida && mission.perfil_trayectoria === 'estandar' }"
                @click="
                  etapa4TrayectoriaElegida = true;
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
                :class="{ selected: etapa4TrayectoriaElegida && mission.perfil_trayectoria === 'rapida' }"
                @click="
                  etapa4TrayectoriaElegida = true;
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
            data-tutorial="advance-btn"
            class="btn-primary advance-cta-btn"
            :disabled="
              loading ||
              (mission.etapa_actual === 1 && !etapa1DestinoElegido) ||
              (mission.etapa_actual === 4 && !etapa4TrayectoriaElegida)
            "
            @click="advanceStage"
          >
            {{
              mission.etapa_actual === 1 && !etapa1DestinoElegido
                ? 'Selecciona un destino para continuar'
                : mission.etapa_actual === 4 && !etapa4TrayectoriaElegida
                  ? 'Selecciona una trayectoria para continuar'
                  : mission.etapa_actual < 9
                    ? `Avanzar a Etapa ${mission.etapa_actual + 1} ►`
                    : 'Ejecutar Retorno e Informe con el Gato Jefe ►'
            }}
          </button>
        </footer>
      </aside>
    </main>

    <!-- ESTADO DE RESPALDO SI LA CONEXIÓN ESTÁ CARGANDO O REINTENTANDO -->
    <main v-else class="fallback-workstation">
      <div class="panel-box fallback-card">
        <h2 class="stage-title">Inicializando Consola de Control Zenit</h2>
        <p class="serif-narrative stage-prose">{{ statusMessage }}</p>
        <div class="fallback-actions">
          <button class="btn-primary" :disabled="loading" @click="startNewMission(true)">
            {{ loading ? 'Conectando...' : '🔄 Reintentar e Iniciar Expedición' }}
          </button>
          <button @click="showMainMenu = true">Volver al Menú de Inicio</button>
        </div>
      </div>
    </main>

    <TutorialOverlay
      v-model:paso-inicial="tutorialPaso"
      :pasos="pasosTutorialActuales"
      :activo="tutorialVisible"
      :etiqueta-contexto="etiquetaContextoTutorial"
      @finish="tutorialVisible = false"
      @skip="desactivarTutorial()"
    />
  </div>
</template>

<style scoped>
/* ========================================================================= */
/* ARQUITECTURA DE ESTACIÓN DE VUELO ADAPTABLE (SIN RECORTES VERTICALES)     */
/* ========================================================================= */
.cockpit-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--void);
  overflow-x: hidden;
  overflow-y: auto;
  position: relative;
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

.split-workstation.full-vn-focus {
  grid-template-columns: 1fr;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
}

@media (max-width: 1080px) {
  .split-workstation {
    grid-template-columns: 1fr;
  }
}

.final-report-viewport {
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px;
  max-width: 1240px;
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

.fallback-workstation {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.fallback-card {
  max-width: 540px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: center;
}

.fallback-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* COLUMNA DERECHA: CONSOLA DE DECISIONES */
.right-command-column {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  min-height: 480px;
  max-height: calc(100vh - 82px);
  position: sticky;
  top: 12px;
  overflow: hidden;
}

@media (max-width: 1080px) {
  .right-command-column {
    max-height: none;
    position: static;
  }
}

.command-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* CRÓNICA NARRATIVA DE LA TRAMA */
.story-chapter-box {
  background: linear-gradient(135deg, rgba(27, 35, 64, 0.92), rgba(11, 14, 26, 0.96));
  border: 1px solid var(--steel);
  border-left: 4px solid var(--gold);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.story-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.story-chapter-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.06em;
}

.story-speaker {
  font-size: 9px;
  font-weight: 700;
  color: var(--cyan);
  background: rgba(79, 209, 197, 0.12);
  padding: 2px 6px;
  border-radius: 3px;
}

.story-quote {
  font-size: 13px;
  color: var(--bone);
  line-height: 1.5;
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

/* ICONOS ENMARCADOS DE PERSONAJES Y NOVELA VISUAL */
.cat-icon-showcase {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  font-weight: 700;
  color: var(--gold);
}

.story-bubble-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 2px;
}

.story-speaker-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  image-rendering: pixelated;
  flex-shrink: 0;
  border-radius: 4px;
}

.event-decision-layout {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.event-decision-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.event-player-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(8, 11, 20, 0.94);
  border: 2px solid #d6c59a;
  border-radius: 5px;
  padding: 4px;
  flex-shrink: 0;
}

.event-player-icon {
  width: 58px;
  height: 58px;
  object-fit: cover;
  image-rendering: pixelated;
  border-radius: 3px;
}

.event-player-badge span {
  font-size: 8px;
  font-weight: 700;
  color: var(--bone);
  margin-top: 3px;
}

.stage-framed-icon {
  width: 56px;
  height: 56px;
  object-fit: contain;
  image-rendering: pixelated;
  border-radius: 4px;
  flex-shrink: 0;
}

.cat-trio-icons {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.cat-trio-icons .stage-framed-icon {
  width: 44px;
  height: 44px;
}

.vn-stage2-summary-card {
  background: rgba(20, 27, 45, 0.9);
  border: 1px solid var(--amber);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vn-sum-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--mist);
}

.vn-sum-hint {
  font-size: 12px;
  color: var(--bone);
  line-height: 1.45;
}
</style>
