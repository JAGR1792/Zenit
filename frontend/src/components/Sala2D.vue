<template>
  <section class="sala">
    <div class="titulo">{{ habitacion.nombre }}</div>
    <div class="escena">
      <div class="puerta izq" v-if="habitacion.puerta_izquierda" @click="emit('mover', habitacion.puerta_izquierda)">◀</div>
      <div class="personaje" :style="{ left: pos + 'px' }">🧑</div>
      <div class="terminal" v-if="cerca">
        <p>{{ habitacion.mensaje_terminal }}</p>
        <button @click="emit('interactuar', habitacion.id)">[E] Interactuar</button>
      </div>
      <div class="puerta der" v-if="habitacion.puerta_derecha" @click="emit('mover', habitacion.puerta_derecha)">▶</div>
    </div>
    <div class="alerta" v-if="habitacion.alerta_activa" :class="habitacion.color_alerta">
      ⚠ {{ habitacion.mensaje_terminal }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{ habitacion: any }>()
const emit = defineEmits(['mover', 'interactuar'])

const pos = ref(60)
const cerca = computed(() => pos.value > 120 && pos.value < 220)

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') pos.value = Math.max(0, pos.value - 12)
  if (e.key === 'ArrowRight') pos.value = Math.min(260, pos.value + 12)
  if (e.key === 'e' || e.key === 'E') {
    if (cerca.value) emit('interactuar', props.habitacion.id)
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.sala { background: #1B2340; border: 1px solid #3A4666; border-radius: 8px; padding: 12px; margin-top: 16px; }
.titulo { color: #FFB000; font-weight: 700; margin-bottom: 8px; }
.escena { position: relative; height: 80px; background: #0B0E1A; border-radius: 6px; overflow: hidden; }
.puerta { position: absolute; top: 24px; color: #FFB000; cursor: pointer; font-size: 20px; }
.puerta.izq { left: 8px; }
.puerta.der { right: 8px; }
.personaje { position: absolute; top: 24px; font-size: 24px; transition: left 0.1s; }
.terminal { position: absolute; top: 4px; left: 90px; background: #1B2340; border: 1px solid #3A4666; padding: 6px; border-radius: 4px; font-size: 11px; color: #E8E4D8; max-width: 160px; }
.terminal button { margin-top: 4px; cursor: pointer; }
.alerta { margin-top: 8px; padding: 6px; border-radius: 4px; font-size: 12px; }
.alerta.orange { color: #FF7A3D; border: 1px solid #FF7A3D; }
.alerta.red { color: #E5484D; border: 1px solid #E5484D; }
.alerta.cyan { color: #4FD1C5; border: 1px solid #4FD1C5; }
</style>
