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

// Estado físico continuo a 60 FPS para el personaje del jugador en la habitación
const playerX = ref<number>(48) // Porcentaje 8% a 92%
const facingLeft = ref<boolean>(false)
const isMoving = ref<boolean>(false)
const isInteracting = ref<boolean>(false)
const actionFeedback = ref<string>('Camina con [←/→] o [A/D] y pulsa [E] frente a puertas o terminales.')

// Patrulla autónoma de los compañeros de tripulación / Gato Jefe en la sala
const npcOffsets = reactive<Record<string, { x: number; dir: number; talking: boolean }>>({
  npc_0: { x: 32, dir: 1, talking: false },
  npc_1: { x: 66, dir: -1, talking: false },
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
const nearCenterStation = computed(() => playerX.value >= 34 && playerX.value <= 66)

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

  // Movimiento suave de los especialistas en la habitación
  for (const key of Object.keys(npcOffsets)) {
    const npc = npcOffsets[key]
    if (!npc.talking) {
      npc.x += npc.dir * 0.12
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

  // Reproducir animación de interacción del sprite (Fila 1 del spritesheet)
  isInteracting.value = true
  if (interactTimeout) window.clearTimeout(interactTimeout)
  interactTimeout = window.setTimeout(() => {
    isInteracting.value = false
  }, 900)

  // 1. Si está frente a la compuerta izquierda -> cambiar de habitación
  if (nearLeftDoor.value && currentRoom.value.puerta_izquierda) {
    const targetRoom = currentRoom.value.puerta_izquierda
    playerX.value = 76
    facingLeft.value = true
    actionFeedback.value = `Compuerta izquierda abierta → Entrando a ${targetRoom.replace('_', ' ')}`
    emit('moveRoom', targetRoom)
    return
  }

  // 2. Si está frente a la compuerta derecha -> cambiar de habitación
  if (nearRightDoor.value && currentRoom.value.puerta_derecha) {
    const targetRoom = currentRoom.value.puerta_derecha
    playerX.value = 24
    facingLeft.value = false
    actionFeedback.value = `Compuerta derecha abierta → Entrando a ${targetRoom.replace('_', ' ')}`
    emit('moveRoom', targetRoom)
    return
  }

  // 3. Si está frente a la consola central de la habitación
  if (nearCenterStation.value) {
    if (currentRoom.value.id === 'cabina_mando') {
      actionFeedback.value =
        'Consultando telemetría primaria en Cabina de Mando: lecturas de Energía (Wh) y Combustible/Δv actualizadas.'
    } else if (currentRoom.value.id === 'laboratorio') {
      actionFeedback.value = 'Operando banco de instrumentos científicos en el Laboratorio...'
      emit('runScience')
    } else if (currentRoom.value.id === 'soporte_vital') {
      actionFeedback.value = 'Regulando reciclaje de O₂ y estabilizando ánimo de la tripulación...'
      emit('runCrewTask', 'estabilizar_animo')
    } else {
      if (props.mission.etapa_actual === 9) {
        actionFeedback.value = 'Activando antena de alta ganancia en ventana de comunicación...'
        emit('useCommWindow')
      } else {
        actionFeedback.value = 'Ejecutando mantenimiento preventivo de subsistemas...'
        emit('runCrewTask', 'mantenimiento_general')
      }
    }
    return
  }

  actionFeedback.value = 'Acércate más a una puerta lateral o a la consola central para interactuar con [E].'
}

function stepWalk(delta: number): void {
  facingLeft.value = delta < 0
  isMoving.value = true
  playerX.value = Math.min(92, Math.max(8, playerX.value + delta))
  window.setTimeout(() => {
    isMoving.value = false
  }, 350)
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
  <div class="panel-box interactive-room-wrapper">
    <!-- Barra superior de navegación entre salas contiguas -->
    <div class="room-header-bar">
      <div>
        <span class="badge-live">● SIMULACIÓN 2D PIXEL ART EN TIEMPO REAL</span>
        <span class="room-title-main">
          SALA ACTUAL: {{ currentRoom?.nombre.toUpperCase() }}
        </span>
      </div>
      <div class="contiguous-map">
        <button
          v-for="room in mission.habitaciones_2d"
          :key="room.id"
          class="map-node"
          :class="{
            active: room.id === mission.habitacion_jugador,
            alert: room.alerta_activa,
          }"
          @click="emit('moveRoom', room.id)"
        >
          <span v-if="room.alerta_activa" class="blink-warning" style="color: var(--orange)">▲</span>
          {{ room.nombre }}
        </button>
      </div>
    </div>

    <div v-if="currentRoom" class="game-stage-layout">
      <!-- ESCENARIO 2D PIXEL ART ANIMADO -->
      <div class="pixel-stage-canvas">
        <!-- Fondo de ventana espacial según destino (OTB vs LUNA) y habitación -->
        <div
          class="backdrop-layer"
          :class="[
            `room-bg-${currentRoom.id}`,
            mission.destino === 'LUNA' ? 'dest-luna' : 'dest-otb',
          ]"
        >
          <!-- Estrellas pixeladas -->
          <div class="pixel-stars"></div>

          <!-- Ventanal exterior con planeta -->
          <div class="observation-window">
            <div v-if="mission.destino === 'OTB'" class="planet-earth"></div>
            <div v-else class="planet-moon"></div>
            <div class="window-hud">
              {{ mission.destino === 'LUNA' ? 'ÓRBITA LUNAR · 384.400 KM' : 'ÓRBITA TERRESTRE BAJA · 400 KM' }}
            </div>
          </div>

          <!-- Luces de estado del módulo -->
          <div class="bulkhead-lights">
            <span
              class="status-lamp"
              :class="currentRoom.alerta_activa ? 'lamp-alert blink-warning' : 'lamp-ok'"
            ></span>
            <span class="lamp-text">{{ currentRoom.sistema_principal }}</span>
          </div>
        </div>

        <!-- PISO INTERACTIVO CON PUERTAS CONTIGUAS, CONSOLA Y SPRITES ANIMADOS -->
        <div class="deck-floor">
          <!-- PUERTA CONTIGUA IZQUIERDA -->
          <div
            class="airlock-door left"
            :class="{ active: nearLeftDoor, sealed: !currentRoom.puerta_izquierda }"
            @click="currentRoom.puerta_izquierda && emit('moveRoom', currentRoom.puerta_izquierda)"
          >
            <div v-if="nearLeftDoor && currentRoom.puerta_izquierda" class="key-e-floating">
              [E] ABRIR PUERTA
            </div>
            <div class="door-arch">
              <div class="door-lights"></div>
              <span>{{
                currentRoom.puerta_izquierda
                  ? `◄ ${currentRoom.puerta_izquierda.replace('_', ' ').toUpperCase()}`
                  : 'SELLADA'
              }}</span>
            </div>
          </div>

          <!-- CONSOLA / ESTACIÓN INTERACTIVA CENTRAL DE LA HABITACIÓN -->
          <div
            class="room-workstation"
            :class="{ active: nearCenterStation, alert: currentRoom.alerta_activa }"
            @click="triggerInteractionE"
          >
            <div v-if="nearCenterStation" class="key-e-floating">
              <template v-if="currentRoom.id === 'cabina_mando'">[E] LEER TELEMETRÍA</template>
              <template v-else-if="currentRoom.id === 'laboratorio'">[E] OPERAR LABORATORIO</template>
              <template v-else-if="currentRoom.id === 'soporte_vital'">[E] SOPORTE VITAL / ÁNIMO</template>
              <template v-else>[E] SISTEMAS / ANTENA</template>
            </div>

            <div class="console-screen">
              <div class="screen-scanline"></div>
              <div class="screen-title">{{ currentRoom.nombre.toUpperCase() }}</div>
              <div class="screen-sub">
                <template v-if="currentRoom.id === 'cabina_mando'">
                  ENERGÍA: {{ mission.bateria_actual_wh }} Wh · Δv: {{ mission.delta_v_disponible_ms }} m/s
                </template>
                <template v-else-if="currentRoom.id === 'laboratorio'">
                  CIENCIA: {{ mission.puntos_ciencia_generados }} pts · DATOS: {{ mission.datos_generados_gb }} GB
                </template>
                <template v-else-if="currentRoom.id === 'soporte_vital'">
                  OXÍGENO: {{ mission.o2_dias_disponibles }}d · COMIDA: {{ mission.comida_dias_disponibles }}d
                </template>
                <template v-else>
                  VENTANAS COMM: {{ mission.ventanas_comm_restantes }} · INTEGRIDAD:
                  {{ Math.round((mission.rendimiento_subsistemas.energia ?? 1) * 100) }}%
                </template>
              </div>
            </div>
          </div>

          <!-- PUERTA CONTIGUA DERECHA -->
          <div
            class="airlock-door right"
            :class="{ active: nearRightDoor, sealed: !currentRoom.puerta_derecha }"
            @click="currentRoom.puerta_derecha && emit('moveRoom', currentRoom.puerta_derecha)"
          >
            <div v-if="nearRightDoor && currentRoom.puerta_derecha" class="key-e-floating">
              [E] ABRIR PUERTA
            </div>
            <div class="door-arch">
              <div class="door-lights"></div>
              <span>{{
                currentRoom.puerta_derecha
                  ? `${currentRoom.puerta_derecha.replace('_', ' ').toUpperCase()} ►`
                  : 'SELLADA'
              }}</span>
            </div>
          </div>

          <!-- SPRITES DE TRIPULANTES ESPECIALISTAS / CONTROL EN LA SALA -->
          <div
            v-for="(member, idx) in roomCrewMembers"
            :key="member.id"
            class="character-actor npc-actor"
            :style="{ left: `${npcOffsets[`npc_${idx % 2}`]?.x ?? 35 + idx * 20}%` }"
          >
            <PixelSprite
              :animacion="isInteracting ? 'gato_hablar' : 'gato_caminar'"
              :flip-x="(npcOffsets[`npc_${idx % 2}`]?.dir ?? 1) < 0"
              :width="92"
              :height="92"
              :fps="7"
              :animo="member.estado_animo"
              :etiqueta="`${member.nombre.split(' ')[1] || member.nombre} (${member.especialidad})`"
            />
          </div>

          <!-- SPRITE PRINCIPAL DEL JUGADOR (PERRO ASTRONAUTA CON CASCO) -->
          <div class="character-actor player-actor" :style="{ left: `${playerX}%` }">
            <PixelSprite
              :animacion="playerAnimation"
              :flip-x="facingLeft"
              :width="104"
              :height="104"
              :fps="10"
              :animo="directorMood"
              etiqueta="DIRECTOR [TÚ]"
            />
          </div>
        </div>

        <!-- Barra de controles rápidos e indicador de acción -->
        <div class="arcade-controls-bar">
          <div class="btn-group">
            <button @mousedown="stepWalk(-12)" @click="stepWalk(-10)">◄ Caminar [A / ←]</button>
            <button class="btn-primary" @click="triggerInteractionE">
              ⚡ [Tecla E] Interactuar / Cruzar Puerta
            </button>
            <button @mousedown="stepWalk(12)" @click="stepWalk(10)">Caminar [D / →] ►</button>
          </div>
          <div class="feedback-ticker">{{ actionFeedback }}</div>
        </div>
      </div>

      <!-- PANEL LATERAL CONTEXTUAL (RESPETANDO LA REGLA DE ASIMETRÍA DE INFORMACIÓN) -->
      <div class="contextual-room-hud">
        <div class="hud-title">LECTURA LOCAL: {{ currentRoom.nombre.toUpperCase() }}</div>

        <!-- CABINA DE MANDO: Único lugar con Energía y Combustible exactos -->
        <template v-if="currentRoom.id === 'cabina_mando'">
          <div class="hud-stat">
            <span>Batería Acumulada</span>
            <strong style="color: var(--cyan)">
              {{ mission.bateria_actual_wh }} / {{ mission.bateria_capacidad_wh }} Wh
            </strong>
          </div>
          <div class="hud-meter">
            <div
              :style="{
                width: `${Math.min(100, (mission.bateria_actual_wh / Math.max(1, mission.bateria_capacidad_wh)) * 100)}%`,
                background: 'var(--cyan)',
              }"
            ></div>
          </div>

          <div class="hud-stat">
            <span>Balance Eléctrico</span>
            <strong :style="{ color: mission.balance_potencia_w >= 0 ? 'var(--green)' : 'var(--orange)' }">
              {{ mission.balance_potencia_w >= 0 ? `+${mission.balance_potencia_w}` : mission.balance_potencia_w }} W
            </strong>
          </div>

          <div class="hud-stat">
            <span>Propulsión / Delta-v</span>
            <strong style="color: var(--amber)">{{ mission.delta_v_disponible_ms }} m/s</strong>
          </div>
          <div class="hud-meter">
            <div
              :style="{
                width: `${Math.min(100, (mission.delta_v_disponible_ms / Math.max(1, mission.delta_v_inicial_ms)) * 100)}%`,
                background: 'var(--amber)',
              }"
            ></div>
          </div>
          <p class="asymmetry-hint">
            ✓ Estás en la <strong>Cabina de Mando</strong>: tienes acceso visual directo a las cifras de energía y combustible.
          </p>
        </template>

        <!-- LABORATORIO CIENTÍFICO: Único lugar para ejecutar investigación -->
        <template v-else-if="currentRoom.id === 'laboratorio'">
          <div class="hud-stat">
            <span>Ciencia Acumulada</span>
            <strong style="color: var(--cyan)">{{ mission.puntos_ciencia_generados }} pts</strong>
          </div>
          <div class="hud-stat">
            <span>Memoria de Datos</span>
            <strong style="color: var(--amber)">{{ mission.datos_generados_gb }} GB</strong>
          </div>
          <div class="hud-stat">
            <span>Calidad Experimental</span>
            <strong style="color: var(--green)">{{ mission.calidad_datos_promedio }}%</strong>
          </div>
          <button class="btn-primary hud-action-btn" @click="triggerInteractionE">
            🔬 [E] Operar Instrumentos del Laboratorio
          </button>
          <p class="asymmetry-hint">
            🔒 <em>Energía y combustible ocultos aquí:</em> camina a la izquierda hacia la Cabina de Mando con <strong>[E]</strong> para consultarlos.
          </p>
        </template>

        <!-- MÓDULO DE VIDA Y HABITACIÓN -->
        <template v-else-if="currentRoom.id === 'soporte_vital'">
          <div class="hud-stat">
            <span>Autonomía Oxígeno</span>
            <strong style="color: var(--green)">{{ mission.o2_dias_disponibles }} días</strong>
          </div>
          <div class="hud-stat">
            <span>Agua y Raciones</span>
            <strong style="color: var(--green)">{{ mission.comida_dias_disponibles }} días</strong>
          </div>
          <button class="btn-cyan hud-action-btn" @click="triggerInteractionE">
            ☀️ [E] Estabilizar Ánimo de Tripulación
          </button>
          <p class="asymmetry-hint">
            El icono sobre la cabeza de cada tripulante (☀️ Sol, ☁️ Nube, 🌧️ Lluvia) altera su velocidad y calidad de trabajo.
          </p>
        </template>

        <!-- SALA DE SISTEMAS Y COMUNICACIONES -->
        <template v-else>
          <div class="hud-stat">
            <span>Ventanas Comm</span>
            <strong style="color: var(--lilac)">{{ mission.ventanas_comm_restantes }} restantes</strong>
          </div>
          <div class="hud-stat">
            <span>Datos Transmitidos</span>
            <strong style="color: var(--cyan)">
              {{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB
            </strong>
          </div>
          <button class="btn-cyan hud-action-btn" @click="emit('runCrewTask', 'mantenimiento_general')">
            🔧 [E] Reparar / Mantenimiento Común
          </button>
          <button class="btn-primary hud-action-btn" @click="emit('useCommWindow')">
            📡 Transmitir Datos a Tierra (1 Ventana)
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interactive-room-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-color: var(--amber);
}

.room-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.badge-live {
  background: rgba(255, 176, 0, 0.18);
  border: 1px solid var(--amber);
  color: var(--gold);
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  margin-right: 10px;
}

.room-title-main {
  font-size: 13px;
  font-weight: 700;
  color: var(--bone);
}

.contiguous-map {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.map-node {
  font-size: 11px;
  padding: 5px 10px;
}

.map-node.active {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.22);
  color: var(--gold);
  font-weight: 700;
}

.map-node.alert {
  border-color: var(--orange);
}

.game-stage-layout {
  display: grid;
  grid-template-columns: 1fr 265px;
  gap: 14px;
}

@media (max-width: 900px) {
  .game-stage-layout {
    grid-template-columns: 1fr;
  }
}

.pixel-stage-canvas {
  background: #080b14;
  border: 2px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.backdrop-layer {
  height: 125px;
  position: relative;
  border-bottom: 3px solid #2b3550;
  overflow: hidden;
  background: linear-gradient(180deg, #10162b 0%, #1b2340 100%);
}

.pixel-stars {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(#e8e4d8 1px, transparent 1px),
    radial-gradient(#4fd1c5 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: 0 0, 20px 20px;
  opacity: 0.28;
}

.observation-window {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  height: 82px;
  background: #060810;
  border: 3px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
}

.planet-earth {
  position: absolute;
  bottom: -55px;
  left: 25%;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #4fd1c5, #2e6fd8 60%, #1b2340);
  box-shadow: 0 0 18px rgba(79, 209, 197, 0.45);
}

.planet-moon {
  position: absolute;
  top: 12px;
  right: 28%;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #e8e4d8, #b8b2a7 55%, #6e6a66);
  box-shadow: 0 0 14px rgba(232, 228, 216, 0.35);
}

.window-hud {
  position: absolute;
  bottom: 4px;
  left: 8px;
  font-size: 9px;
  color: var(--cyan);
  letter-spacing: 0.05em;
}

.bulkhead-lights {
  position: absolute;
  top: 10px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(11, 14, 26, 0.8);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--steel);
}

.status-lamp {
  width: 9px;
  height: 9px;
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

.lamp-text {
  font-size: 10px;
  color: var(--mist);
}

.deck-floor {
  position: relative;
  height: 175px;
  background: repeating-linear-gradient(
    90deg,
    #161e36 0px,
    #161e36 44px,
    #12182b 44px,
    #12182b 48px
  );
  border-bottom: 6px solid #2b3550;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 12px 12px;
}

.airlock-door {
  width: 92px;
  height: 132px;
  background: #232d4b;
  border: 3px solid var(--steel);
  border-radius: 6px 6px 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.airlock-door.active {
  border-color: var(--amber);
  box-shadow: 0 0 16px rgba(255, 176, 0, 0.45);
}

.airlock-door.sealed {
  opacity: 0.35;
  cursor: default;
}

.door-arch {
  font-size: 9px;
  font-weight: 700;
  color: var(--gold);
  text-align: center;
  padding: 4px;
}

.room-workstation {
  width: 230px;
  height: 112px;
  margin-bottom: 8px;
  background: #0d1222;
  border: 2px solid var(--cyan);
  border-radius: 6px;
  padding: 8px;
  position: relative;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.room-workstation.active {
  border-color: var(--amber);
  box-shadow: 0 0 18px rgba(255, 176, 0, 0.38);
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
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(255, 176, 0, 0.6);
  z-index: 6;
}

.console-screen {
  text-align: center;
}

.screen-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--amber);
  margin-bottom: 4px;
}

.screen-sub {
  font-size: 10px;
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

.arcade-controls-bar {
  background: var(--void);
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.btn-group {
  display: flex;
  gap: 6px;
}

.feedback-ticker {
  font-size: 11px;
  color: var(--cyan);
}

.contextual-room-hud {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 11px;
}

.hud-title {
  color: var(--amber);
  font-weight: 700;
  border-bottom: 1px solid var(--steel);
  padding-bottom: 5px;
}

.hud-stat {
  display: flex;
  justify-content: space-between;
}

.hud-meter {
  height: 6px;
  background: var(--steel);
  border-radius: 3px;
  overflow: hidden;
}

.hud-meter > div {
  height: 100%;
}

.hud-action-btn {
  width: 100%;
  margin-top: 4px;
}

.asymmetry-hint {
  font-size: 10px;
  color: var(--mist);
  line-height: 1.45;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px dashed var(--steel);
}
</style>
