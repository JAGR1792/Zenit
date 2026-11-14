<template>
  <section class="informe" v-if="informe">
    <h2>{{ informe.titulo_final }}</h2>
    <p class="sub">{{ informe.subtitulo_final }}</p>
    <p class="puntaje">Puntuación global: {{ informe.puntuacion_global }}</p>
    <p class="dialogo">{{ informe.dialogo_jefe_apertura }}</p>
    <p class="monologo" v-if="informe.monologo_cuarta_pared">{{ informe.monologo_cuarta_pared }}</p>
    <ul class="dimensiones">
      <li v-for="d in informe.dimensiones" :key="d.id">
        <strong>{{ d.nombre }}</strong>: {{ d.puntuacion }} — {{ d.estado_etiqueta }}
        <br /><small>{{ d.comentario_jefe }}</small>
      </li>
    </ul>
    <p class="frase">{{ informe.frase_despedida }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { zenitApi } from '../services/api'

const props = defineProps<{ missionId: string | null }>()
const informe = ref<any>(null)

async function cargar() {
  if (!props.missionId) return
  try {
    informe.value = await zenitApi.getReport(props.missionId)
  } catch (e) {
    informe.value = null
  }
}

watch(() => props.missionId, cargar, { immediate: true })
</script>

<style scoped>
.informe { background: #1B2340; border: 1px solid #3A4666; border-radius: 8px; padding: 16px; margin-top: 16px; color: #E8E4D8; }
h2 { color: #F5D36B; }
.sub { color: #8FA3BF; font-size: 12px; }
.puntaje { color: #4FD1C5; font-weight: 700; }
.dialogo { margin-top: 8px; }
.monologo { color: #6B5B95; font-style: italic; }
.dimensiones { margin-top: 12px; list-style: none; padding: 0; }
.dimensiones li { margin-bottom: 8px; }
.frase { margin-top: 12px; color: #FFB000; }
</style>
