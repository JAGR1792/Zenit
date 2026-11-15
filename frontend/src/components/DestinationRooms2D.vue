<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { EstadoMision, TripulanteEstado } from '../services/api'
import PixelSprite, {
  obtenerSpriteTripulante,
  type AnimacionSprite,
} from './PixelSprite.vue'

const props = defineProps<{
  mission: EstadoMision
}>()

const emit = defineEmits<{
  (e: 'moveRoom', roomId: string): void
  (e: 'runScience'): void
  (e: 'runCrewTask', subtipo: string): void
  (e: 'useCommWindow'): void
}>()

const playerX = ref<number>(48)
const facingLeft = ref<boolean>(false)
const isMoving = ref<boolean>(false)
const isInteracting = ref<boolean>(false)
const actionFeedback = ref<string>(
  'Desplázate con [←/→] o [A/D] · Pulsa [E] frente a compuertas, tripulantes o consolas.',
)

// Estado de la zona RPG / Novela Visual dentro de la nave
const activeDialogueMember = ref<TripulanteEstado | null>(null)
const dialogueMode = ref<'saludo' | 'diagnostico'>('saludo')

// Posiciones fijas (estáticas) para los tripulantes en la sala, separadas de puertas y consola
const POSICIONES_ESTATICAS_TRIPULACION = [26, 74, 19]

const keysHeld = new Set<string>()
let rafId: number | null = null
let interactTimeout: number | null = null

const currentRoom = computed(() => {
  return (
    props.mission.habitaciones_2d.find((h) => h.id === props.mission.habitacion_jugador) ??
    props.mission.habitaciones_2d[0]
  )
})

const playerAnimation = computed<AnimacionSprite>(() => {
  if (isInteracting.value) return 'perro_interactuar'
  if (isMoving.value) return 'perro_caminar'
  return 'perro_idle'
})

// Fondos pixel art por habitación (public/sprites/escenarios/nave).
// ar = proporción ancho/alto de la imagen; piso = altura (en % desde abajo) donde apoyan los pies.
interface FondoHabitacion {
  src: string
  ar: number
  piso: number
  ventana?: boolean
}
const FONDOS_HABITACION: Record<string, FondoHabitacion> = {
  cabina_mando: { src: '/sprites/escenarios/nave/cabina_mando.jpg', ar: 1364 / 768, piso: 12 },
  laboratorio: { src: '/sprites/escenarios/nave/laboratorio.jpg', ar: 1326 / 544, piso: 1 },
  soporte_vital: { src: '/sprites/escenarios/nave/sala_soporte_vital.jpg', ar: 1227 / 544, piso: 1 },
  sala_sistemas: {
    src: '/sprites/escenarios/nave/cabina_v2.png',
    ar: 752 / 544,
    piso: 2,
    ventana: true,
  },
}
const fondoActual = computed(() =>
  currentRoom.value ? (FONDOS_HABITACION[currentRoom.value.id] ?? null) : null,
)
const fondoHabitacion = computed(() => fondoActual.value?.src ?? null)

// Vista exterior (Tierra/Luna): órbita alta durante el tránsito, órbita baja al llegar al destino
const vistaExterior = computed(() => {
  const cuerpo = props.mission.destino === 'LUNA' ? 'luna' : 'tierra'
  const orbita = props.mission.etapa_actual >= 7 ? 'baja' : 'alta'
  return `/sprites/escenarios/vistas/${cuerpo}_orbita_${orbita}.png`
})

const nearLeftDoor = computed(() => playerX.value <= 16 && !!currentRoom.value?.puerta_izquierda)
const nearRightDoor = computed(() => playerX.value >= 84 && !!currentRoom.value?.puerta_derecha)
const nearCenterStation = computed(() => playerX.value >= 37 && playerX.value <= 63)

const directorMood = computed(() => {
  const dir = props.mission.tripulacion.find((t) => t.es_jugador)
  return dir?.estado_animo ?? 'sol'
})

const roomCrewMembers = computed(() => {
  if (!currentRoom.value) return []
  return props.mission.tripulacion.filter(
    (t) => !t.es_jugador && t.vivo && t.habitacion_actual === currentRoom.value?.id,
  )
})

const nearNpcMember = computed(() => {
  if (nearLeftDoor.value || nearRightDoor.value || nearCenterStation.value) return null
  for (let idx = 0; idx < roomCrewMembers.value.length; idx++) {
    const pos = POSICIONES_ESTATICAS_TRIPULACION[idx % POSICIONES_ESTATICAS_TRIPULACION.length]
    if (Math.abs(playerX.value - pos) <= 10) {
      return roomCrewMembers.value[idx]
    }
  }
  return null
})

watch(
  () => currentRoom.value?.id,
  () => {
    activeDialogueMember.value = null
  },
)

function buildCrewRpgText(member: TripulanteEstado, mode: 'saludo' | 'diagnostico'): string {
  const roomId = currentRoom.value?.id ?? 'cabina_mando'
  const isLuna = props.mission.destino === 'LUNA'
  const moodTag =
    member.estado_animo === 'lluvia'
      ? 'Tengo la moral bajo mínimos (Lluvia); un descanso en Módulo de Vida vendría bien. '
      : member.estado_animo === 'nube'
        ? 'Algo fatigado, pero operativo. '
        : ''

  if (member.es_jugador) {
    if (mode === 'diagnostico') {
      return `Bitácora de Mando — Etapa ${props.mission.etapa_actual}/10 · Batería: ${props.mission.bateria_actual_wh} Wh · Delta-v: ${props.mission.delta_v_disponible_ms} m/s · Ciencia TX: ${props.mission.datos_transmitidos_gb}/${props.mission.datos_generados_gb} GB.`
    }
    return isLuna
      ? '«Viajamos rumbo al Cráter Shackleton en busca de la señal Helios-9. Cada maniobra cuenta.»'
      : '«Operando en Órbita Terrestre Baja (400 km). La prioridad es recolectar ciencia y enviarla a Tierra.»'
  }

  if (mode === 'diagnostico') {
    if (roomId === 'laboratorio') {
      return `${moodTag}En el Laboratorio llevamos ${props.mission.datos_generados_gb} GB y ${props.mission.puntos_ciencia_generados} pts (calidad ${props.mission.calidad_datos_promedio}%). ${
        props.mission.etapa_actual < 7
          ? 'Los sensores se activan al entrar en órbita del destino (Etapa 7).'
          : pendingDataGb.value > 0
            ? `Quedan ${pendingDataGb.value} GB en memoria listos para transmitir en Sala de Sistemas.`
            : 'Podemos capturar más muestras espectrales con [E] en la consola.'
      }`
    }
    if (roomId === 'soporte_vital') {
      return `${moodTag}Soporte vital marca ${props.mission.o2_dias_disponibles} días de O₂ y ${props.mission.comida_dias_disponibles} días de raciones. Mi salud es ${Math.round(member.salud)}% y mi moral ${Math.round(member.salud_mental)}%.`
    }
    if (roomId === 'sala_sistemas') {
      return `${moodTag}Balance eléctrico: ${props.mission.balance_potencia_w >= 0 ? '+' : ''}${props.mission.balance_potencia_w} W · Ventanas de enlace restantes: ${props.mission.ventanas_comm_restantes} (${Math.round(props.mission.probabilidad_enlace_comm * 100)}% señal).`
    }
    return `${moodTag}Propulsión con ${props.mission.delta_v_disponible_ms} m/s frente a ${props.mission.delta_v_requerido_total_ms} m/s requeridos para completar la ruta.`
  }

  if (roomId === 'laboratorio') {
    if (props.mission.etapa_actual >= 7 && props.mission.datos_generados_gb === 0) {
      return `${moodTag}«¡Capitán! Ya estamos sobre ${isLuna ? 'la Luna' : 'el objetivo'}. Acércate a la consola central del Laboratorio y pulsa [E] para registrar las lecturas de Helios-9.»`
    }
    return `${moodTag}«Los bancos ópticos están calibrados, Capitán. Revisa los espectros cuando gustes.»`
  }
  if (roomId === 'soporte_vital') {
    return `${moodTag}«Controlo las válvulas de reciclaje de oxígeno y la moral de la tripulación. Si alguien entra en Nube o Lluvia, estabiliza el ánimo aquí.»`
  }
  if (roomId === 'sala_sistemas') {
    if (pendingDataGb.value > 0) {
      return `${moodTag}«Capitán, tenemos ${pendingDataGb.value} GB sin enviar en disco. ¡Usa la antena de esta sala para transmitirlos a Tierra!»`
    }
    return `${moodTag}«Los buses de potencia y la antena direccional están en espera de paquetes científicos.»`
  }
  return `${moodTag}«Todo supervisado en mi estación, Capitán Perro. A la espera de tus órdenes.»`
}

const activeDialogueText = computed(() => {
  if (!activeDialogueMember.value) return ''
  return buildCrewRpgText(activeDialogueMember.value, dialogueMode.value)
})

function openCrewDialogue(member: TripulanteEstado): void {
  if (activeDialogueMember.value?.id === member.id) {
    activeDialogueMember.value = null
    return
  }
  activeDialogueMember.value = member
  dialogueMode.value = 'saludo'
  actionFeedback.value = `💬 Conversando con ${member.nombre} (${member.rol}).`
}

function openSoloLogDialogue(): void {
  const director = props.mission.tripulacion.find((t) => t.es_jugador)
  if (!director) return
  openCrewDialogue(director)
}

function closeDialogue(): void {
  activeDialogueMember.value = null
}

const pendingDataGb = computed(() => {
  return Math.max(
    0,
    Number((props.mission.datos_generados_gb - props.mission.datos_transmitidos_gb).toFixed(2)),
  )
})

function updatePhysicsLoop(): void {
  const left = keysHeld.has('ArrowLeft') || keysHeld.has('a') || keysHeld.has('A')
  const right = keysHeld.has('ArrowRight') || keysHeld.has('d') || keysHeld.has('D')

  if (left && !right) {
    playerX.value = Math.max(8, playerX.value - 0.62)
    facingLeft.value = true
    isMoving.value = true
  } else if (right && !left) {
    playerX.value = Math.min(92, playerX.value + 0.62)
    facingLeft.value = false
    isMoving.value = true
  } else {
    isMoving.value = false
  }

  rafId = window.requestAnimationFrame(updatePhysicsLoop)
}

function handleKeyDown(ev: KeyboardEvent): void {
  const tag = (ev.target as HTMLElement | null)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  if (['ArrowLeft', 'ArrowRight', 'a', 'A', 'd', 'D'].includes(ev.key)) {
    keysHeld.add(ev.key)
  } else if (ev.key === 'e' || ev.key === 'E') {
    ev.preventDefault()
    triggerInteractionE()
  } else if (ev.key === 'Escape' && activeDialogueMember.value) {
    ev.preventDefault()
    closeDialogue()
  }
}

function handleKeyUp(ev: KeyboardEvent): void {
  keysHeld.delete(ev.key)
}

function triggerInteractionE(): void {
  if (!currentRoom.value) return

  isInteracting.value = true
  if (interactTimeout) window.clearTimeout(interactTimeout)
  interactTimeout = window.setTimeout(() => {
    isInteracting.value = false
  }, 900)

  if (nearLeftDoor.value && currentRoom.value.puerta_izquierda) {
    const targetRoom = currentRoom.value.puerta_izquierda
    playerX.value = 76
    facingLeft.value = true
    actionFeedback.value = `Compuerta abierta → Entrando a ${targetRoom.replace('_', ' ')}`
    emit('moveRoom', targetRoom)
    return
  }

  if (nearRightDoor.value && currentRoom.value.puerta_derecha) {
    const targetRoom = currentRoom.value.puerta_derecha
    playerX.value = 24
    facingLeft.value = false
    actionFeedback.value = `Compuerta abierta → Entrando a ${targetRoom.replace('_', ' ')}`
    emit('moveRoom', targetRoom)
    return
  }

  if (nearCenterStation.value) {
    if (currentRoom.value.id === 'cabina_mando') {
      actionFeedback.value =
        'Telemetría primaria verificada en Cabina de Mando: lecturas exactas de Energía (Wh) y Δv.'
    } else if (currentRoom.value.id === 'laboratorio') {
      if (props.mission.etapa_actual < 7) {
        actionFeedback.value =
          '⏳ En tránsito hacia el destino: el Laboratorio Científico se activará al entrar en órbita (Etapa 7).'
      } else {
        actionFeedback.value =
          '🔬 Recolectando datos científicos en el Laboratorio... ¡Luego ve a Sala de Sistemas para transmitirlos!'
        emit('runScience')
      }
    } else if (currentRoom.value.id === 'soporte_vital') {
      actionFeedback.value = '☀ Regulando soporte vital y estabilizando estado de ánimo...'
      emit('runCrewTask', 'estabilizar_animo')
    } else {
      if (props.mission.etapa_actual >= 7 && (pendingDataGb.value > 0 || props.mission.etapa_actual === 9)) {
        actionFeedback.value = '📡 Transmitiendo paquete de datos por antena hacia Tierra...'
        emit('useCommWindow')
      } else {
        actionFeedback.value = '🔧 Mantenimiento preventivo ejecutado en Sala de Sistemas...'
        emit('runCrewTask', 'mantenimiento_general')
      }
    }
    return
  }

  if (nearNpcMember.value) {
    openCrewDialogue(nearNpcMember.value)
    return
  }

  actionFeedback.value = 'Camina hasta una compuerta, tripulante o consola central antes de pulsar [E].'
}

function stepWalk(delta: number): void {
  facingLeft.value = delta < 0
  isMoving.value = true
  playerX.value = Math.min(92, Math.max(8, playerX.value + delta))
  window.setTimeout(() => {
    isMoving.value = false
  }, 320)
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
  rafId = window.requestAnimationFrame(updatePhysicsLoop)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
  if (rafId !== null) window.cancelAnimationFrame(rafId)
  if (interactTimeout !== null) window.clearTimeout(interactTimeout)
})
</script>

<template>
  <div v-if="currentRoom" class="deck-viewport-card">
    <!-- 1. Mapa lineal de habitaciones contiguas -->
    <div class="corridor-nav">
      <div class="corridor-eyebrow">CUBIERTA DE NAVEGACIÓN INTERNA</div>
      <div class="corridor-Chain">
        <button
          v-for="(room, idx) in mission.habitaciones_2d"
          :key="room.id"
          class="corridor-step"
          :class="{
            active: room.id === mission.habitacion_jugador,
            alert: room.alerta_activa,
          }"
          @click="emit('moveRoom', room.id)"
        >
          <span class="room-idx">0{{ idx + 1 }}</span>
          <span>{{ room.nombre }}</span>
          <span
            v-if="
              room.id === 'laboratorio' &&
              mission.etapa_actual >= 7 &&
              mission.datos_generados_gb === 0
            "
            class="step-hint-pill"
          >
            🔬 1º Recolectar
          </span>
          <span
            v-if="room.id === 'sala_sistemas' && pendingDataGb > 0"
            class="step-hint-pill tx-ready"
          >
            📡 2º Transmitir ({{ pendingDataGb }} GB)
          </span>
          <span v-if="room.alerta_activa" class="blink-warning alert-triangle">▲</span>
        </button>
      </div>
    </div>

    <!-- 2. Escenario 2D Pixel Art amplio y despejado -->
    <div class="pixel-stage-canvas" :class="{ 'con-fondo': !!fondoHabitacion }">
      <div
        class="scene-box"
        :class="{ 'scene-plain': !fondoActual }"
        :style="
          fondoActual
            ? { '--ar': fondoActual.ar, '--piso': `${fondoActual.piso}%` }
            : undefined
        "
      >
      <img
        v-if="fondoActual?.ventana"
        :src="vistaExterior"
        alt=""
        class="room-bg-img room-window-view"
      />
      <img
        v-if="fondoHabitacion"
        :key="fondoHabitacion"
        :src="fondoHabitacion"
        alt=""
        class="room-bg-img"
      />
      <div v-if="!fondoActual?.ventana" class="vista-orbital" :title="`Vista exterior: ${mission.destino === 'LUNA' ? 'Luna' : 'Tierra'}`">
        <img :src="vistaExterior" alt="Vista exterior" class="vista-orbital-img" />
        <span class="vista-orbital-tag">
          {{ mission.destino === 'LUNA' ? 'LUNA' : 'TIERRA' }} ·
          {{ mission.etapa_actual >= 7 ? 'ÓRBITA BAJA' : 'ÓRBITA ALTA' }}
        </span>
      </div>
      <div
        class="backdrop-layer"
        :class="mission.destino === 'LUNA' ? 'dest-luna' : 'dest-otb'"
      >
        <div class="pixel-stars"></div>

        <!-- Ventanal panorámico -->
        <div class="observation-window">
          <div v-if="mission.destino === 'OTB'" class="planet-earth"></div>
          <div v-else class="planet-moon"></div>
          <div class="window-hud">
            {{
              mission.destino === 'LUNA'
                ? 'SECTOR CISLUNAR · 384.400 KM'
                : 'ÓRBITA TERRESTRE BAJA · 400 KM'
            }}
          </div>
        </div>

        <!-- Indicador ambiental del módulo -->
        <div class="bulkhead-badge">
          <span
            class="status-lamp"
            :class="currentRoom.alerta_activa ? 'lamp-alert blink-warning' : 'lamp-ok'"
          ></span>
          <span>{{ currentRoom.nombre.toUpperCase() }}</span>
        </div>
      </div>

      <!-- Piso caminable con compuertas contiguas, terminal central y personajes -->
      <div class="deck-floor">
        <!-- Compuerta Izquierda -->
        <div
          class="airlock-door left"
          :class="{ active: nearLeftDoor, sealed: !currentRoom.puerta_izquierda }"
          @click="currentRoom.puerta_izquierda && emit('moveRoom', currentRoom.puerta_izquierda)"
        >
          <div v-if="nearLeftDoor && currentRoom.puerta_izquierda" class="key-e-floating">
            [E] ABRIR PUERTA
          </div>
          <div class="door-arch">
            <span class="door-arrow">◄</span>
            <span>{{
              currentRoom.puerta_izquierda
                ? currentRoom.puerta_izquierda.replace('_', ' ').toUpperCase()
                : 'MAMPARO'
            }}</span>
          </div>
        </div>

        <!-- Estación Central de la Sala -->
        <div
          class="room-workstation"
          :class="{ active: nearCenterStation, alert: currentRoom.alerta_activa }"
          @click="triggerInteractionE"
        >
          <div v-if="nearCenterStation" class="key-e-floating">
            <template v-if="currentRoom.id === 'cabina_mando'">[E] TELEMETRÍA</template>
            <template v-else-if="currentRoom.id === 'laboratorio'">[E] 🔬 RECOLECTAR DATOS</template>
            <template v-else-if="currentRoom.id === 'soporte_vital'">[E] ☀ ESTABILIZAR ÁNIMO</template>
            <template v-else-if="pendingDataGb > 0">
              [E] 📡 TRANSMITIR ({{ pendingDataGb }} GB)
            </template>
            <template v-else>[E] 🔧 OPERAR / TRANSMITIR</template>
          </div>

          <div class="console-screen">
            <div class="screen-title">{{ currentRoom.sistema_principal }}</div>
            <div class="screen-sub">
              <template v-if="currentRoom.id === 'cabina_mando'">
                BATERÍA: {{ mission.bateria_actual_wh }} Wh · Δv: {{ mission.delta_v_disponible_ms }} m/s
              </template>
              <template v-else-if="currentRoom.id === 'laboratorio'">
                CIENCIA: {{ mission.puntos_ciencia_generados }} pts · DATOS: {{ mission.datos_generados_gb }} GB
              </template>
              <template v-else-if="currentRoom.id === 'soporte_vital'">
                O₂: {{ mission.o2_dias_disponibles }} días · RACIONES: {{ mission.comida_dias_disponibles }} días
              </template>
              <template v-else>
                VENTANAS COMM: {{ mission.ventanas_comm_restantes }} · TX: {{ mission.datos_transmitidos_gb }} GB
              </template>
            </div>
          </div>
        </div>

        <!-- Compuerta Derecha -->
        <div
          class="airlock-door right"
          :class="{ active: nearRightDoor, sealed: !currentRoom.puerta_derecha }"
          @click="currentRoom.puerta_derecha && emit('moveRoom', currentRoom.puerta_derecha)"
        >
          <div v-if="nearRightDoor && currentRoom.puerta_derecha" class="key-e-floating">
            [E] ABRIR PUERTA
          </div>
          <div class="door-arch">
            <span class="door-arrow">►</span>
            <span>{{
              currentRoom.puerta_derecha
                ? currentRoom.puerta_derecha.replace('_', ' ').toUpperCase()
                : 'ESCLUSA'
            }}</span>
          </div>
        </div>

        <!-- Perros Especialistas de la tripulación en la sala (ESTÁTICOS en su puesto, clicables para diálogo RPG) -->
        <div
          v-for="(member, idx) in roomCrewMembers"
          :key="member.id"
          class="character-actor npc-actor"
          :class="{ 'npc-near': nearNpcMember?.id === member.id, 'npc-talking': activeDialogueMember?.id === member.id }"
          :style="{ left: `${POSICIONES_ESTATICAS_TRIPULACION[idx % POSICIONES_ESTATICAS_TRIPULACION.length]}%` }"
          :title="`Conversar con ${member.nombre}`"
          @click="openCrewDialogue(member)"
        >
          <div v-if="nearNpcMember?.id === member.id" class="key-e-floating npc-talk-pill">
            [E] 💬 HABLAR
          </div>
          <PixelSprite
            :animacion="obtenerSpriteTripulante(member.especialidad, false)"
            :flip-x="idx % 2 === 1"
            :width="78"
            :height="96"
            :animar="false"
            :animo="member.estado_animo"
            :etiqueta="`${member.nombre.split(' ')[1] || member.nombre} · ${member.especialidad.toUpperCase()}`"
          />
        </div>

        <!-- Perro Astronauta del Jugador (PERRO1.zip) -->
        <div class="character-actor player-actor" :style="{ left: `${playerX}%` }">
          <PixelSprite
            :animacion="playerAnimation"
            :flip-x="facingLeft"
            :width="86"
            :height="110"
            :fps="9"
            :animo="directorMood"
            etiqueta="DIRECTOR [TÚ]"
          />
        </div>

        <!-- Cuadro de Diálogo RPG / Novela Visual con la Tripulación Canina -->
        <div v-if="activeDialogueMember" class="rpg-dialogue-overlay">
          <div class="rpg-dialogue-box">
            <div class="rpg-portrait-col">
              <PixelSprite
                :animacion="obtenerSpriteTripulante(activeDialogueMember.especialidad, activeDialogueMember.es_jugador)"
                :width="56"
                :height="68"
                :animar="false"
                :animo="activeDialogueMember.estado_animo"
              />
              <span class="rpg-stats-chip">
                Salud {{ Math.round(activeDialogueMember.salud) }}% · Moral {{ Math.round(activeDialogueMember.salud_mental) }}%
              </span>
            </div>

            <div class="rpg-copy-col">
              <div class="rpg-header-row">
                <div>
                  <strong class="rpg-speaker-name">{{ activeDialogueMember.nombre.toUpperCase() }}</strong>
                  <span class="rpg-speaker-role">{{ activeDialogueMember.rol }} · Exp {{ activeDialogueMember.experiencia }}/5</span>
                </div>
                <button class="rpg-close-btn" title="Cerrar diálogo [Esc]" @click="closeDialogue">✕ [Esc]</button>
              </div>
              <p class="serif-narrative rpg-dialogue-copy">{{ activeDialogueText }}</p>
              <div class="rpg-choices-row">
                <button
                  class="rpg-choice-btn"
                  :class="{ active: dialogueMode === 'diagnostico' }"
                  @click="dialogueMode = dialogueMode === 'diagnostico' ? 'saludo' : 'diagnostico'"
                >
                  &gt; {{ dialogueMode === 'diagnostico' ? 'Volver al saludo' : 'Pedir diagnóstico de esta sala' }}
                </button>
                <button
                  v-if="currentRoom.id === 'laboratorio' && mission.etapa_actual >= 7"
                  class="rpg-choice-btn accent"
                  @click="emit('runScience'); closeDialogue()"
                >
                  &gt; 🔬 Recolectar datos ahora
                </button>
                <button
                  v-else-if="currentRoom.id === 'soporte_vital'"
                  class="rpg-choice-btn accent"
                  @click="emit('runCrewTask', 'estabilizar_animo'); closeDialogue()"
                >
                  &gt; ☀ Estabilizar ánimo de la dotación
                </button>
                <button
                  v-else-if="currentRoom.id === 'sala_sistemas' && mission.etapa_actual >= 7 && pendingDataGb > 0"
                  class="rpg-choice-btn accent"
                  @click="emit('useCommWindow'); closeDialogue()"
                >
                  &gt; 📡 Transmitir {{ pendingDataGb }} GB a Tierra
                </button>
              </div>
            </div>

            <div class="rpg-captain-badge">
              <img
                src="/sprites/iconos/icono_captain_dog_casco.png"
                alt="Capitán Perro"
                class="rpg-captain-img"
              />
              <span>CAPITÁN [TÚ]</span>
            </div>
          </div>
        </div>
      </div>

      </div>

      <!-- Barra de mando táctil / teclado -->
      <div class="stage-control-strip">
        <div class="dpad-group">
          <button @click="stepWalk(-10)">◄ Izquierda [A]</button>
          <button class="btn-primary" @click="triggerInteractionE">
            [E] Interactuar / Abrir Compuerta
          </button>
          <button @click="stepWalk(10)">Derecha [D] ►</button>
          <button
            v-for="member in roomCrewMembers"
            :key="`talk-${member.id}`"
            class="btn-cyan"
            @click="openCrewDialogue(member)"
          >
            💬 {{ member.nombre.split(' ')[1] || member.nombre }}
          </button>
          <button
            v-if="roomCrewMembers.length === 0"
            class="btn-cyan"
            @click="openSoloLogDialogue"
          >
            💬 Bitácora de Mando
          </button>
        </div>
        <div class="feedback-line">{{ actionFeedback }}</div>
      </div>
    </div>

    <!-- 3. Dock de Telemetría Asimétrica (Solo muestra lo disponible en la habitación actual) -->
    <div class="asymmetric-telemetry-dock">
      <template v-if="currentRoom.id === 'cabina_mando'">
        <div class="dock-cell">
          <span class="dock-label">RESERVA ELÉCTRICA (CABINA)</span>
          <strong class="dock-val" style="color: var(--cyan)">
            {{ mission.bateria_actual_wh }} / {{ mission.bateria_capacidad_wh }} Wh
          </strong>
        </div>
        <div class="dock-cell">
          <span class="dock-label">BALANCE DE POTENCIA</span>
          <strong
            class="dock-val"
            :style="{ color: mission.balance_potencia_w >= 0 ? 'var(--green)' : 'var(--orange)' }"
          >
            {{ mission.balance_potencia_w >= 0 ? `+${mission.balance_potencia_w}` : mission.balance_potencia_w }} W
          </strong>
        </div>
        <div class="dock-cell">
          <span class="dock-label">DELTA-V DISPONIBLE</span>
          <strong class="dock-val" style="color: var(--amber)">
            {{ mission.delta_v_disponible_ms }} m/s (Req: {{ mission.delta_v_requerido_total_ms }} m/s)
          </strong>
        </div>
      </template>

      <template v-else-if="currentRoom.id === 'laboratorio'">
        <div class="dock-cell">
          <span class="dock-label">CIENCIA RECOLECTADA</span>
          <strong class="dock-val" style="color: var(--cyan)">{{ mission.puntos_ciencia_generados }} pts</strong>
        </div>
        <div class="dock-cell">
          <span class="dock-label">DATOS EN MEMORIA</span>
          <strong class="dock-val" style="color: var(--amber)">
            {{ mission.datos_generados_gb }} GB (Calidad {{ mission.calidad_datos_promedio }}%)
          </strong>
        </div>
        <div class="dock-cell dock-action">
          <button
            class="btn-primary"
            style="width: 100%"
            :disabled="mission.etapa_actual < 7"
            @click="emit('runScience')"
          >
            {{
              mission.etapa_actual < 7
                ? '⏳ Ciencia disponible al llegar al Destino (Etapa 7)'
                : '[E] 🔬 Operar Instrumentos Científicos'
            }}
          </button>
        </div>
      </template>

      <template v-else-if="currentRoom.id === 'soporte_vital'">
        <div class="dock-cell">
          <span class="dock-label">AUTONOMÍA OXÍGENO (O₂)</span>
          <strong class="dock-val" style="color: var(--green)">{{ mission.o2_dias_disponibles }} días</strong>
        </div>
        <div class="dock-cell">
          <span class="dock-label">AGUA Y RACIONES</span>
          <strong class="dock-val" style="color: var(--green)">{{ mission.comida_dias_disponibles }} días</strong>
        </div>
        <div class="dock-cell dock-action">
          <button class="btn-cyan" style="width: 100%" @click="emit('runCrewTask', 'estabilizar_animo')">
            [E] Estabilizar Ánimo de Tripulación
          </button>
        </div>
      </template>

      <template v-else>
        <div class="dock-cell">
          <span class="dock-label">VENTANAS DE COMUNICACIÓN</span>
          <strong class="dock-val" style="color: var(--lilac)">
            {{ mission.ventanas_comm_restantes }} disp. ({{ Math.round(mission.probabilidad_enlace_comm * 100) }}% enlace)
          </strong>
        </div>
        <div class="dock-cell">
          <span class="dock-label">DATOS TRANSMITIDOS</span>
          <strong class="dock-val" style="color: var(--cyan)">
            {{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB
          </strong>
        </div>
        <div class="dock-cell dock-action" style="display: flex; gap: 6px">
          <button class="btn-cyan" style="flex: 1" @click="emit('runCrewTask', 'mantenimiento_general')">
            Reparar
          </button>
          <button
            class="btn-primary"
            style="flex: 1"
            :disabled="mission.etapa_actual < 7"
            @click="emit('useCommWindow')"
          >
            {{ mission.etapa_actual < 7 ? '⏳ Etapa 7+' : 'Transmitir' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.deck-viewport-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: auto;
  min-height: 460px;
}

.corridor-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 8px 12px;
}

.corridor-eyebrow {
  font-size: 10px;
  font-weight: 700;
  color: var(--mist);
  letter-spacing: 0.06em;
}

.corridor-Chain {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.corridor-step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  font-size: 11px;
  background: var(--void);
  border: 1px solid var(--steel);
}

.corridor-step.active {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.16);
  color: var(--gold);
  font-weight: 600;
}

.corridor-step.alert {
  border-color: var(--orange);
}

.room-idx {
  font-size: 9px;
  color: var(--mist);
}

.alert-triangle {
  color: var(--orange);
  font-size: 10px;
}

.step-hint-pill {
  background: rgba(79, 209, 197, 0.18);
  border: 1px solid var(--cyan);
  color: var(--cyan);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 700;
}

.step-hint-pill.tx-ready {
  background: rgba(255, 176, 0, 0.22);
  border-color: var(--amber);
  color: var(--gold);
}

.pixel-stage-canvas {
  position: relative;
  background: var(--void-deep);
  border: 1px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.vista-orbital {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 150px;
  z-index: 4;
  border: 2px solid #d6c59a;
  border-radius: 4px;
  background: #060810;
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.7);
}

.vista-orbital-img {
  display: block;
  width: 100%;
  height: 82px;
  object-fit: cover;
  image-rendering: pixelated;
}

.vista-orbital-tag {
  display: block;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-align: center;
  color: var(--gold);
  padding: 2px 4px;
  background: rgba(8, 11, 20, 0.92);
}

.airlock-door.left {
  background: #1f2947 url('/sprites/escenarios/nave/puerta_izquierda.jpg') center / cover no-repeat;
  image-rendering: pixelated;
}

.airlock-door.right {
  background: #1f2947 url('/sprites/escenarios/nave/puerta_derecha.jpg') center / cover no-repeat;
  image-rendering: pixelated;
}

.airlock-door .door-arch {
  background: rgba(8, 11, 20, 0.82);
  border-radius: 3px;
}

.room-bg-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center bottom;
  image-rendering: pixelated;
  z-index: 0;
}

.scene-box {
  position: relative;
  width: min(100%, calc(52vh * var(--ar, 2)));
  aspect-ratio: var(--ar, 2);
  margin: 0 auto;
  overflow: hidden;
  background: #060810;
}

.scene-box.scene-plain {
  display: contents;
}

.room-window-view {
  z-index: 0;
  object-fit: cover;
}

.scene-box::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(8, 11, 20, 0.3), rgba(8, 11, 20, 0) 45%, rgba(8, 11, 20, 0.35));
  z-index: 1;
  pointer-events: none;
}

.scene-box > .room-bg-img:not(.room-window-view) {
  z-index: 1;
}

.scene-box > .backdrop-layer {
  position: absolute;
  inset: 0;
  height: auto;
  background: transparent;
  border: 0;
  pointer-events: none;
  z-index: 2;
}

.scene-box > .backdrop-layer .pixel-stars,
.scene-box > .backdrop-layer .observation-window {
  display: none;
}

.scene-box > .deck-floor {
  position: absolute;
  inset: 0;
  min-height: 0;
  padding: 0;
  background: transparent;
  border: 0;
  z-index: 3;
}

/* Compuertas: zonas sensibles transparentes en los extremos (las puertas ya están dibujadas en el fondo) */
.scene-box .airlock-door {
  position: absolute;
  bottom: var(--piso, 6%);
  width: 12%;
  height: 62%;
  background: transparent;
  border: 2px dashed transparent;
  border-radius: 6px;
}

.scene-box .airlock-door.left {
  left: 0.5%;
  background: transparent;
}

.scene-box .airlock-door.right {
  right: 0.5%;
  background: transparent;
}

.scene-box .airlock-door.active {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.1);
  box-shadow: 0 0 14px rgba(255, 176, 0, 0.45);
}

.scene-box .airlock-door.sealed {
  display: none;
}

.scene-box .airlock-door .door-arch {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  padding: 2px 6px;
  white-space: nowrap;
  font-size: 8px;
}

.scene-box .airlock-door .key-e-floating {
  top: -26px;
}

/* Consola informativa compacta, arriba al centro, para no tapar al perro */
.scene-box .room-workstation {
  position: absolute;
  top: 5%;
  left: 50%;
  transform: translateX(-50%);
  width: min(250px, 34%);
  height: auto;
  margin: 0;
  padding: 5px 9px;
  background: rgba(8, 11, 20, 0.78);
}

.scene-box .room-workstation .key-e-floating {
  top: auto;
  bottom: -26px;
}

.scene-box .character-actor {
  bottom: var(--piso, 6%);
}

.pixel-stage-canvas.con-fondo {
  background: #060810;
}

.vista-orbital {
  display: none;
}

.scene-box > .vista-orbital {
  display: block;
}

.backdrop-layer {
  height: 130px;
  position: relative;
  border-bottom: 2px solid var(--steel);
  overflow: hidden;
  background: linear-gradient(180deg, #0b0e1a 0%, #1b2340 100%);
}

.pixel-stars {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(#e8e4d8 1px, transparent 1px),
    radial-gradient(#4fd1c5 1px, transparent 1px);
  background-size: 44px 44px;
  background-position:
    0 0,
    22px 22px;
  opacity: 0.25;
}

.observation-window {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 88px;
  background: #060810;
  border: 2px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
}

.planet-earth {
  position: absolute;
  bottom: -58px;
  left: 25%;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #4fd1c5, #2e6fd8 60%, #1b2340);
  box-shadow: 0 0 20px rgba(79, 209, 197, 0.4);
}

.planet-moon {
  position: absolute;
  top: 12px;
  right: 28%;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #e8e4d8, #b8b2a7 55%, #6e6a66);
  box-shadow: 0 0 14px rgba(232, 228, 216, 0.35);
}

.window-hud {
  position: absolute;
  bottom: 5px;
  left: 10px;
  font-size: 9px;
  color: var(--cyan);
  letter-spacing: 0.06em;
}

.bulkhead-badge {
  position: absolute;
  top: 10px;
  left: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(11, 14, 26, 0.85);
  padding: 4px 9px;
  border-radius: 4px;
  border: 1px solid var(--steel);
  font-size: 10px;
  font-weight: 700;
  color: var(--bone);
}

.status-lamp {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.lamp-ok {
  background: var(--green);
  box-shadow: 0 0 6px var(--green);
}

.lamp-alert {
  background: var(--orange);
  box-shadow: 0 0 8px var(--orange);
}

.deck-floor {
  position: relative;
  min-height: 220px;
  padding-top: 28px;
  background: repeating-linear-gradient(
    90deg,
    #141c34 0px,
    #141c34 52px,
    #10172b 52px,
    #10172b 56px
  );
  border-bottom: 5px solid #2b3550;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-left: 14px;
  padding-right: 14px;
  padding-bottom: 12px;
}

.airlock-door {
  width: 96px;
  height: 142px;
  background: #1f2947;
  border: 2px solid var(--steel);
  border-radius: 6px 6px 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.airlock-door.active {
  border-color: var(--amber);
  box-shadow: 0 0 14px rgba(255, 176, 0, 0.4);
}

.airlock-door.sealed {
  opacity: 0.3;
  cursor: default;
}

.door-arch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  font-weight: 700;
  color: var(--gold);
  text-align: center;
  padding: 6px;
}

.door-arrow {
  font-size: 13px;
  color: var(--amber);
}

.room-workstation {
  width: 260px;
  height: 118px;
  margin-bottom: 10px;
  background: #0c1120;
  border: 2px solid var(--steel);
  border-radius: 6px;
  padding: 10px 12px;
  position: relative;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.room-workstation.active {
  border-color: var(--amber);
  box-shadow: 0 0 16px rgba(255, 176, 0, 0.32);
}

.room-workstation.alert {
  border-color: var(--orange);
}

.key-e-floating {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--amber);
  color: var(--void);
  font-size: 10px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 4px;
  white-space: nowrap;
  box-shadow: 0 2px 10px rgba(255, 176, 0, 0.55);
  z-index: 6;
}

.console-screen {
  text-align: center;
}

.screen-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--amber);
  margin-bottom: 5px;
}

.screen-sub {
  font-size: 11px;
  color: var(--cyan);
}

.character-actor {
  position: absolute;
  bottom: 6px;
  transform: translateX(-50%);
  z-index: 4;
  pointer-events: none;
}

.npc-actor {
  pointer-events: auto;
  cursor: pointer;
  transition: filter 0.14s ease;
}

.npc-actor:hover,
.npc-actor.npc-near,
.npc-actor.npc-talking {
  filter: drop-shadow(0 0 8px rgba(79, 209, 197, 0.75));
}

.npc-talk-pill {
  background: var(--cyan);
  color: var(--void);
}

.player-actor {
  z-index: 5;
}

/* CUADRO DE DIÁLOGO RPG / NOVELA VISUAL DENTRO DE LA NAVE */
.rpg-dialogue-overlay {
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 8px;
  z-index: 8;
}

.rpg-dialogue-box {
  background: rgba(8, 11, 20, 0.96);
  border: 2px solid #d6c59a;
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.85);
}

.rpg-portrait-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  background: rgba(20, 27, 45, 0.9);
  border: 1px solid var(--steel);
  border-radius: 4px;
  padding: 4px 6px;
  flex-shrink: 0;
}

.rpg-stats-chip {
  font-size: 8px;
  color: var(--green);
  white-space: nowrap;
}

.rpg-copy-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.rpg-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
}

.rpg-speaker-name {
  font-size: 11px;
  color: var(--gold);
  margin-right: 6px;
}

.rpg-speaker-role {
  font-size: 9px;
  color: var(--cyan);
}

.rpg-close-btn {
  padding: 2px 6px;
  font-size: 9px;
  background: var(--void);
  border: 1px solid var(--steel);
  color: var(--mist);
}

.rpg-dialogue-copy {
  font-size: 13px;
  color: var(--bone);
  line-height: 1.45;
}

.rpg-choices-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.rpg-choice-btn {
  padding: 4px 8px;
  font-size: 10px;
  background: rgba(27, 35, 64, 0.78);
  border: 1px solid var(--steel);
  color: var(--bone);
}

.rpg-choice-btn.active,
.rpg-choice-btn:hover {
  border-color: var(--cyan);
  color: var(--cyan);
}

.rpg-choice-btn.accent {
  border-color: var(--amber);
  color: var(--gold);
}

.rpg-captain-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(20, 27, 45, 0.95);
  border: 2px solid #d6c59a;
  border-radius: 4px;
  padding: 4px;
  flex-shrink: 0;
}

.rpg-captain-img {
  width: 50px;
  height: 50px;
  object-fit: cover;
  image-rendering: pixelated;
  border-radius: 3px;
}

.rpg-captain-badge span {
  font-size: 8px;
  font-weight: 700;
  color: var(--gold);
  margin-top: 2px;
}

.stage-control-strip {
  background: var(--cabin);
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.dpad-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feedback-line {
  font-size: 11px;
  color: var(--mist);
}

.asymmetric-telemetry-dock {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

@media (max-width: 720px) {
  .asymmetric-telemetry-dock {
    grid-template-columns: 1fr;
  }
}

.dock-cell {
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 9px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
}

.dock-label {
  font-size: 10px;
  color: var(--mist);
  letter-spacing: 0.04em;
}

.dock-val {
  font-size: 13px;
}
</style>
