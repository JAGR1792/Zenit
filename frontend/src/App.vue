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
    </div>
    <p v-else>Error al crear la misión.</p>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { SpaceApi } from './services/api'

const mission = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    mission.value = await SpaceApi.createMission({
      nombre_mision: 'Expedición Zenit-1',
      destino: 'OTB',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })
  } catch (e) {
    mission.value = null
  } finally {
    loading.value = false
  }
})

async function avanzar() {
  if (!mission.value) return
  const res = await SpaceApi.advance(mission.value.id)
  mission.value = res.mission_state ?? res
}
</script>

<style scoped>
.container { padding: 24px; font-family: monospace; }
h1 { font-size: 1.5rem; margin-bottom: 12px; }
button { margin-top: 12px; padding: 8px 12px; cursor: pointer; }
</style>
