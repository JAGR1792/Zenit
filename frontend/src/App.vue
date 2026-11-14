<template>
  <main class="container">
    <h1>Zenit — Simulador de misiones espaciales</h1>
    <p v-if="loading">Cargando misión...</p>
    <div v-else-if="mission">
      <p>Misión: {{ mission.nombre_mision }}</p>
      <p>Etapa: {{ mission.nombre_etapa }}</p>
      <p>Destino: {{ mission.destino }}</p>
      <p>Presupuesto restante: {{ mission.presupuesto_restante_usd }} USD</p>
      <p>Masa total: {{ mission.masa_total_kg }} kg</p>
      <button @click="avanzar">Avanzar etapa</button>
      <Sala2D
        v-if="habitacionActual"
        :habitacion="habitacionActual"
        @mover="moverHabitacion"
        @interactuar="interactuarHabitacion"
      />
    </div>
    <p v-else>Error al crear la misión.</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { zenitApi } from './services/api'
import Sala2D from './components/Sala2D.vue'

const mission = ref<any>(null)
const loading = ref(true)
const habitacionId = ref<string>('cabina_mando')

const habitacionActual = computed(() => {
  if (!mission.value?.habitaciones_2d) return null
  return mission.value.habitaciones_2d.find((h: any) => h.id === habitacionId.value) ?? mission.value.habitaciones_2d[0]
})

onMounted(async () => {
  try {
    mission.value = await zenitApi.createMission({
      nombre_mision: 'Expedición Zenit-1',
      destino: 'OTB',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })
    habitacionId.value = mission.value.habitacion_jugador ?? 'cabina_mando'
  } catch (e) {
    mission.value = null
  } finally {
    loading.value = false
  }
})

async function avanzar() {
  if (!mission.value) return
  const res = await zenitApi.advanceStage(mission.value.id)
  mission.value = res.mission_state ?? res
}

async function moverHabitacion(destino: string) {
  if (!mission.value) return
  const res = await zenitApi.sendDecision(mission.value.id, {
    stage: mission.value.etapa_actual,
    decision: 'mover_habitacion',
    params: { habitacion_id: destino },
  })
  mission.value = res.mission_state ?? res
  habitacionId.value = destino
}

async function interactuarHabitacion(id: string) {
  if (!mission.value) return
  await zenitApi.sendDecision(mission.value.id, {
    stage: mission.value.etapa_actual,
    decision: 'inspeccionar_habitacion',
    params: { habitacion_id: id },
  })
}
</script>

<style scoped>
.container { padding: 24px; font-family: monospace; }
h1 { font-size: 1.5rem; margin-bottom: 12px; }
button { margin-top: 12px; padding: 8px 12px; cursor: pointer; }
</style>
