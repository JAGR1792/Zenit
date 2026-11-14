<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import type { EstadoMision } from '../services/api'
import PixelSprite, { type AnimacionSprite } from './PixelSprite.vue'

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
  'Desplázate con [←/→] o [A/D] · Pulsa [E] frente a compuertas o consolas.',
)

const npcOffsets = reactive<Record<string, { x: number; dir: number; talking: boolean }>>({
  npc_0: { x: 30, dir: 1, talking: false },
  npc_1: { x: 68, dir: -1, talking: false },
})

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

const nearLeftDoor = computed(() => playerX.value <= 20 && !!currentRoom.value?.puerta_izquierda)
const nearRightDoor = computed(() => playerX.value >= 80 && !!currentRoom.value?.puerta_derecha)
const nearCenterStation = computed(() => playerX.value >= 33 && playerX.value <= 67)

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

function updatePhysicsLoop(): void {
  const left = keysHeld.has('ArrowLeft') || keysHeld.has('a') || keysHeld.has('A')
  const right = keysHeld.has('ArrowRight') || keysHeld.has('d') || keysHeld.has('D')

  if (left && !right) {
    playerX.value = Math.max(8, playerX.value - 0.65)
    facingLeft.value = true
    isMoving.value = true
  } else if (right && !left) {
    playerX.value = Math.min(92, playerX.value + 0.65)
    facingLeft.value = false
    isMoving.value = true
  } else {
    isMoving.value = false
  }

  for (const key of Object.keys(npcOffsets)) {
    const npc = npcOffsets[key]
    if (!npc.talking) {
      npc.x += npc.dir * 0.1
      if (npc.x > 74) npc.dir = -1
      if (npc.x < 26) npc.dir = 1
    }
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
      actionFeedback.value = 'Ejecutando campaña de instrumentos científicos en el Laboratorio...'
      emit('runScience')
    } else if (currentRoom.value.id === 'soporte_vital') {
      actionFeedback.value = 'Regulando soporte vital y estabilizando estado de ánimo...'
      emit('runCrewTask', 'estabilizar_animo')
    } else {
      if (props.mission.etapa_actual === 9) {
        actionFeedback.value = 'Transmitiendo paquete de datos por antena en ventana activa...'
        emit('useCommWindow')
      } else {
        actionFeedback.value = 'Mantenimiento preventivo ejecutado en Sala de Sistemas...'
        emit('runCrewTask', 'mantenimiento_general')
      }
    }
    return
  }

  actionFeedback.value = 'Camina hasta una compuerta lateral o la consola central antes de pulsar [E].'
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
          <span v-if="room.alerta_activa" class="blink-warning alert-triangle">▲</span>
        </button>
      </div>
    </div>

    <!-- 2. Escenario 2D Pixel Art amplio y despejado -->
    <div class="pixel-stage-canvas">
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
            <template v-else-if="currentRoom.id === 'laboratorio'">[E] INVESTIGAR</template>
            <template v-else-if="currentRoom.id === 'soporte_vital'">[E] ESTABILIZAR</template>
            <template v-else>[E] OPERAR SISTEMA</template>
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

        <!-- Especialistas de la tripulación en la sala -->
        <div
          v-for="(member, idx) in roomCrewMembers"
          :key="member.id"
          class="character-actor npc-actor"
          :style="{ left: `${npcOffsets[`npc_${idx % 2}`]?.x ?? 34 + idx * 22}%` }"
        >
          <PixelSprite
            :animacion="isInteracting ? 'gato_hablar' : 'gato_caminar'"
            :flip-x="(npcOffsets[`npc_${idx % 2}`]?.dir ?? 1) < 0"
            :width="84"
            :height="88"
            :fps="7"
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
      </div>

      <!-- Barra de mando táctil / teclado -->
      <div class="stage-control-strip">
        <div class="dpad-group">
          <button @click="stepWalk(-14)">◄ Izquierda [A]</button>
          <button class="btn-primary" @click="triggerInteractionE">
            [E] Interactuar / Abrir Compuerta
          </button>
          <button @click="stepWalk(14)">Derecha [D] ►</button>
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
          <button class="btn-primary" style="width: 100%" @click="emit('runScience')">
            [E] Operar Instrumentos Científicos
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
          <button class="btn-primary" style="flex: 1" @click="emit('useCommWindow')">
            Transmitir
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
  height: 100%;
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

.pixel-stage-canvas {
  background: var(--void-deep);
  border: 1px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
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
  height: 200px;
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
  padding: 0 14px 12px;
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

.player-actor {
  z-index: 5;
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
