<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { EstadoMision } from '../services/api'

const props = defineProps<{
  mission: EstadoMision
}>()

const emit = defineEmits<{
  (e: 'moveRoom', roomId: string): void
  (e: 'runScience'): void
  (e: 'runCrewTask', subtipo: string): void
  (e: 'useCommWindow'): void
}>()

// Posición horizontal del jugador dentro de la habitación actual (0 a 100%)
const playerX = ref<number>(50)

const currentRoom = computed(() => {
  return (
    props.mission.habitaciones_2d.find((h) => h.id === props.mission.habitacion_jugador) ??
    props.mission.habitaciones_2d[0]
  )
})

const nearLeftDoor = computed(() => playerX.value <= 24 && !!currentRoom.value?.puerta_izquierda)
const nearRightDoor = computed(() => playerX.value >= 76 && !!currentRoom.value?.puerta_derecha)
const nearCenterConsole = computed(() => playerX.value > 28 && playerX.value < 72)

function handleKeydown(ev: KeyboardEvent): void {
  const tag = (ev.target as HTMLElement | null)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  if (ev.key === 'ArrowLeft' || ev.key === 'a' || ev.key === 'A') {
    playerX.value = Math.max(8, playerX.value - 14)
  } else if (ev.key === 'ArrowRight' || ev.key === 'd' || ev.key === 'D') {
    playerX.value = Math.min(92, playerX.value + 14)
  } else if (ev.key === 'e' || ev.key === 'E') {
    triggerKeyE()
  }
}

function triggerKeyE(): void {
  if (!currentRoom.value) return
  if (nearLeftDoor.value && currentRoom.value.puerta_izquierda) {
    playerX.value = 72
    emit('moveRoom', currentRoom.value.puerta_izquierda)
    return
  }
  if (nearRightDoor.value && currentRoom.value.puerta_derecha) {
    playerX.value = 28
    emit('moveRoom', currentRoom.value.puerta_derecha)
    return
  }
  // Interacción con el componente central de la sala actual
  if (currentRoom.value.id === 'laboratorio') {
    emit('runScience')
  } else if (currentRoom.value.id === 'soporte_vital') {
    emit('runCrewTask', 'estabilizar_animo')
  } else if (currentRoom.value.id === 'sala_sistemas') {
    if (props.mission.etapa_actual === 9) {
      emit('useCommWindow')
    } else {
      emit('runCrewTask', 'mantenimiento_general')
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const moodColor = (mood: string): string => {
  if (mood === 'sol') return '#F5C84C'
  if (mood === 'nube') return '#9AA8B8'
  return '#4A78C2'
}
</script>

<template>
  <div class="panel-box destination-2d">
    <div class="room-top-bar">
      <div>
        <span class="amber-title">INTERFAZ DE HABITACIONES CONTIGUAS (MODO DESTINO 2D)</span>
        <span class="controls-hint">
          Usa [←/→] o [A/D] para desplazarte y presiona <strong>[E]</strong> en puertas o consolas
        </span>
      </div>
      <!-- Mapa de habitaciones contiguas -->
      <div class="room-tabs">
        <button
          v-for="room in mission.habitaciones_2d"
          :key="room.id"
          class="room-pill"
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

    <!-- Escenario 2D lateral (Placeholder estilo Artboard Dirección A mientras llegan sprites) -->
    <div v-if="currentRoom" class="scene-grid">
      <div class="viewport-2d">
        <!-- Ventana exterior según destino -->
        <div
          class="space-window"
          :class="mission.destino === 'LUNA' ? 'window-moon' : 'window-otb'"
        >
          <div v-if="mission.destino === 'OTB'" class="celestial-earth"></div>
          <div v-else class="celestial-moon"></div>
          <div class="room-banner">
            SALA ACTUAL: {{ currentRoom.nombre.toUpperCase() }} ({{ currentRoom.sistema_principal }})
          </div>
        </div>

        <!-- Piso de la habitación con Puerta Izquierda, Consola Central y Puerta Derecha -->
        <div class="room-floor">
          <!-- Puerta Izquierda -->
          <div
            class="door-frame left-door"
            :class="{ highlighted: nearLeftDoor, disabled: !currentRoom.puerta_izquierda }"
            @click="currentRoom.puerta_izquierda && emit('moveRoom', currentRoom.puerta_izquierda)"
          >
            <div class="door-label">
              {{
                currentRoom.puerta_izquierda
                  ? `[E] ◄ ${currentRoom.puerta_izquierda.replace('_', ' ').toUpperCase()}`
                  : 'MAMPARO SELLADO'
              }}
            </div>
          </div>

          <!-- Estación Central de la Sala -->
          <div class="station-console" :class="{ highlighted: nearCenterConsole }">
            <div class="station-title">{{ currentRoom.sistema_principal }}</div>
            <div class="station-sub">
              <template v-if="currentRoom.id === 'cabina_mando'">
                [Consola de Telemetría Primaria Activa]
              </template>
              <template v-else-if="currentRoom.id === 'laboratorio'">
                Pulsa <strong>[E]</strong> o clic para operar instrumentos científicos
              </template>
              <template v-else-if="currentRoom.id === 'soporte_vital'">
                Pulsa <strong>[E]</strong> para estabilizar estado de ánimo y soporte vital
              </template>
              <template v-else>
                Pulsa <strong>[E]</strong> para mantenimiento de sistemas / transmitir por antena
              </template>
            </div>
          </div>

          <!-- Puerta Derecha -->
          <div
            class="door-frame right-door"
            :class="{ highlighted: nearRightDoor, disabled: !currentRoom.puerta_derecha }"
            @click="currentRoom.puerta_derecha && emit('moveRoom', currentRoom.puerta_derecha)"
          >
            <div class="door-label">
              {{
                currentRoom.puerta_derecha
                  ? `[E] ${currentRoom.puerta_derecha.replace('_', ' ').toUpperCase()} ►`
                  : 'ESCLUSA EXTERIOR'
              }}
            </div>
          </div>

          <!-- Tripulantes presentes en la sala con su icono de estado de ánimo (Sol/Nube/Lluvia) -->
          <div
            v-for="(member, idx) in mission.tripulacion.filter(
              (t) => t.habitacion_actual === currentRoom?.id && !t.es_jugador,
            )"
            :key="member.id"
            class="crew-avatar npc-avatar"
            :style="{ left: `${36 + idx * 18}%` }"
          >
            <div
              class="mood-bubble"
              :style="{ borderColor: moodColor(member.estado_animo), color: moodColor(member.estado_animo) }"
            >
              {{ member.estado_animo.toUpperCase() }}
            </div>
            <div class="pixel-body npc-body"></div>
            <div class="avatar-caption">{{ member.nombre.split(' ')[1] || member.nombre }}</div>
          </div>

          <!-- Avatar del Jugador (Director) -->
          <div class="crew-avatar player-avatar" :style="{ left: `${playerX}%` }">
            <div class="mood-bubble" style="border-color: var(--amber); color: var(--amber)">
              DIRECTOR [E]
            </div>
            <div class="pixel-body director-body"></div>
            <div class="avatar-caption">TÚ</div>
          </div>
        </div>

        <!-- Controles táctiles rápidos para caminar y pulsar E -->
        <div class="walk-bar">
          <button @click="playerX = Math.max(8, playerX - 18)">◄ Caminar Izquierda</button>
          <button class="btn-primary" @click="triggerKeyE()">
            [Tecla E] Interactuar / Abrir Puerta
          </button>
          <button @click="playerX = Math.min(92, playerX + 18)">Caminar Derecha ►</button>
        </div>
      </div>

      <!-- Panel Derecho: Asimetría de Información según la habitación donde esté el jugador -->
      <div class="room-telemetry-panel">
        <div class="telemetry-header">TERMINAL LOCAL DE SALA</div>

        <!-- 1. Si está en CABINA DE MANDO: ve Energía y Combustible/Delta-v exactos -->
        <template v-if="currentRoom.id === 'cabina_mando'">
          <div class="metric-row">
            <span>Batería Reserva</span>
            <span style="color: var(--cyan)">
              {{ mission.bateria_actual_wh }} / {{ mission.bateria_capacidad_wh }} Wh
            </span>
          </div>
          <div class="bar">
            <div
              :style="{
                width: `${Math.min(100, (mission.bateria_actual_wh / Math.max(1, mission.bateria_capacidad_wh)) * 100)}%`,
                background: 'var(--cyan)',
              }"
            ></div>
          </div>

          <div class="metric-row" style="margin-top: 8px">
            <span>Balance Potencia</span>
            <span :style="{ color: mission.balance_potencia_w >= 0 ? 'var(--green)' : 'var(--orange)' }">
              {{ mission.balance_potencia_w >= 0 ? `+${mission.balance_potencia_w}` : mission.balance_potencia_w }} W
            </span>
          </div>

          <div class="metric-row" style="margin-top: 8px">
            <span>Delta-v Restante</span>
            <span style="color: var(--amber)">{{ mission.delta_v_disponible_ms }} m/s</span>
          </div>
          <div class="bar">
            <div
              :style="{
                width: `${Math.min(100, (mission.delta_v_disponible_ms / Math.max(1, mission.delta_v_inicial_ms)) * 100)}%`,
                background: 'var(--amber)',
              }"
            ></div>
          </div>
          <p class="room-note">
            Lectura directa de instrumentos de cabina. (Esta información crítica se oculta al salir de Cabina de Mando).
          </p>
        </template>

        <!-- 2. Si está en LABORATORIO: ve Investigación y Datos -->
        <template v-else-if="currentRoom.id === 'laboratorio'">
          <div class="metric-row">
            <span>Puntos de Ciencia</span>
            <span style="color: var(--cyan)">{{ mission.puntos_ciencia_generados }} pts</span>
          </div>
          <div class="metric-row">
            <span>Datos en Memoria</span>
            <span style="color: var(--amber)">{{ mission.datos_generados_gb }} GB</span>
          </div>
          <div class="metric-row">
            <span>Calidad de Muestras</span>
            <span style="color: var(--green)">{{ mission.calidad_datos_promedio }}%</span>
          </div>
          <button class="btn-primary" style="width: 100%; margin-top: 10px" @click="emit('runScience')">
            [E] Ejecutar Campaña de Instrumentos
          </button>
          <p class="room-note">
            Nota: Para ver energía exacta (Wh) y Delta-v restante debes caminar a la Cabina de Mando.
          </p>
        </template>

        <!-- 3. Si está en SOPORTE VITAL: ve O2, Comida y Salud Mental -->
        <template v-else-if="currentRoom.id === 'soporte_vital'">
          <div class="metric-row">
            <span>Reserva Oxígeno</span>
            <span style="color: var(--green)">{{ mission.o2_dias_disponibles }} días</span>
          </div>
          <div class="metric-row">
            <span>Agua y Raciones</span>
            <span style="color: var(--green)">{{ mission.comida_dias_disponibles }} días</span>
          </div>
          <button
            class="btn-cyan"
            style="width: 100%; margin-top: 10px"
            @click="emit('runCrewTask', 'estabilizar_animo')"
          >
            [E] Estabilizar Ánimo y Soporte Vital
          </button>
          <p class="room-note">
            Energía y combustible ocultos fuera de Cabina de Mando; investigación requiere ir al Laboratorio.
          </p>
        </template>

        <!-- 4. Si está en SALA DE SISTEMAS: ve Antena, Ventanas Comm y Mantenimiento -->
        <template v-else>
          <div class="metric-row">
            <span>Ventanas Comm</span>
            <span style="color: var(--lilac)">{{ mission.ventanas_comm_restantes }} disponibles</span>
          </div>
          <div class="metric-row">
            <span>Datos Transmitidos</span>
            <span style="color: var(--cyan)">
              {{ mission.datos_transmitidos_gb }} / {{ mission.datos_generados_gb }} GB
            </span>
          </div>
          <button
            class="btn-cyan"
            style="width: 100%; margin-top: 8px"
            @click="emit('runCrewTask', 'mantenimiento_general')"
          >
            [E] Mantenimiento Común de Subsistemas
          </button>
          <button
            class="btn-primary"
            style="width: 100%; margin-top: 6px"
            @click="emit('useCommWindow')"
          >
            Transmitir Datos en Ventana Comm
          </button>
        </template>

        <!-- Alertas sin cuantificar visibles en el panel -->
        <div v-if="mission.eventos_activos.length > 0" class="unquantified-alert blink-warning">
          ▲ ALERTA ACTIVA: {{ mission.eventos_activos[0].titulo }} (Ver consola de eventos abajo)
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.destination-2d {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.room-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.amber-title {
  color: var(--amber);
  font-weight: 700;
  font-size: 13px;
  display: block;
}
.controls-hint {
  font-size: 11px;
  color: var(--mist);
}
.room-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.room-pill {
  font-size: 11px;
  padding: 5px 10px;
}
.room-pill.active {
  border-color: var(--amber);
  color: var(--gold);
  background: rgba(255, 176, 0, 0.16);
}
.room-pill.alert {
  border-color: var(--orange);
}
.scene-grid {
  display: grid;
  grid-template-columns: 1fr 250px;
  gap: 14px;
}
@media (max-width: 820px) {
  .scene-grid {
    grid-template-columns: 1fr;
  }
}
.viewport-2d {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.space-window {
  height: 92px;
  border-radius: 5px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--steel);
}
.window-otb {
  background: linear-gradient(180deg, #0b0e1a 0%, #1b2340 60%, #2e6fd8 100%);
}
.window-moon {
  background: linear-gradient(180deg, #0b0e1a 0%, #1b2340 70%, #6e6a66 100%);
}
.celestial-earth {
  position: absolute;
  bottom: -45px;
  left: 18%;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #4fd1c5, #2e6fd8 65%, #1b2340);
}
.celestial-moon {
  position: absolute;
  top: 14px;
  right: 18%;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #b8b2a7, #6e6a66 75%);
}
.room-banner {
  position: relative;
  z-index: 2;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--gold);
  background: rgba(11, 14, 26, 0.72);
}
.room-floor {
  position: relative;
  height: 125px;
  background: #141b33;
  border: 1px solid var(--steel);
  border-radius: 5px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
}
.door-frame {
  width: 110px;
  height: 88px;
  background: var(--steel);
  border: 2px solid var(--mist);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 6px;
  cursor: pointer;
}
.door-frame.highlighted {
  border-color: var(--amber);
  box-shadow: 0 0 10px rgba(255, 176, 0, 0.35);
}
.door-frame.disabled {
  opacity: 0.35;
  cursor: default;
}
.door-label {
  font-size: 10px;
  color: var(--gold);
  font-weight: 700;
}
.station-console {
  flex: 1;
  margin: 0 14px;
  padding: 10px;
  background: var(--void);
  border: 1px dashed var(--cyan);
  border-radius: 4px;
  text-align: center;
}
.station-console.highlighted {
  border-style: solid;
  border-color: var(--amber);
}
.station-title {
  font-size: 11px;
  color: var(--cyan);
  font-weight: 700;
}
.station-sub {
  font-size: 10px;
  color: var(--mist);
  margin-top: 4px;
}
.crew-avatar {
  position: absolute;
  bottom: 8px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: left 0.15s ease-out;
  pointer-events: none;
}
.mood-bubble {
  font-size: 9px;
  font-weight: 700;
  background: var(--void);
  border: 1px solid;
  padding: 1px 5px;
  border-radius: 3px;
  margin-bottom: 3px;
  white-space: nowrap;
}
.pixel-body {
  width: 18px;
  height: 28px;
  border-radius: 3px;
  border: 2px solid var(--bone);
}
.director-body {
  background: var(--amber);
}
.npc-body {
  background: var(--cyan);
}
.avatar-caption {
  font-size: 9px;
  color: var(--bone);
  margin-top: 2px;
}
.walk-bar {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.room-telemetry-panel {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 12px;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.telemetry-header {
  color: var(--amber);
  font-weight: 700;
  border-bottom: 1px solid var(--steel);
  padding-bottom: 4px;
  margin-bottom: 4px;
}
.metric-row {
  display: flex;
  justify-content: space-between;
}
.bar {
  height: 6px;
  background: var(--steel);
  border-radius: 3px;
  overflow: hidden;
}
.bar > div {
  height: 100%;
}
.room-note {
  font-size: 10px;
  color: var(--mist);
  margin-top: 8px;
  line-height: 1.4;
}
.unquantified-alert {
  margin-top: auto;
  padding: 6px;
  border: 1px solid var(--orange);
  border-radius: 4px;
  color: var(--orange);
  font-size: 10px;
}
</style>
