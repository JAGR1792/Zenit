<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

export interface PasoTutorial {
  selector: string
  titulo: string
  descripcion: string
  posicion?: 'top' | 'bottom' | 'left' | 'right'
}

const props = defineProps<{
  pasos: PasoTutorial[]
  activo: boolean
}>()

const emit = defineEmits<{
  (e: 'finish'): void
  (e: 'skip'): void
}>()

const indice = ref(0)
const rect = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const tooltipPos = ref<{ top: number; left: number }>({ top: 0, left: 0 })

const pasoActual = computed(() => props.pasos[indice.value] ?? null)

function actualizarRect(): void {
  if (!pasoActual.value) {
    rect.value = null
    return
  }
  const el = document.querySelector(pasoActual.value.selector) as HTMLElement | null
  if (!el) {
    rect.value = null
    tooltipPos.value = { top: window.innerHeight / 2, left: window.innerWidth / 2 }
    return
  }
  const r = el.getBoundingClientRect()
  rect.value = { top: r.top, left: r.left, width: r.width, height: r.height }
  // Posicionar tooltip debajo del elemento por defecto
  tooltipPos.value = {
    top: r.bottom + 12,
    left: Math.max(12, Math.min(window.innerWidth - 340, r.left)),
  }
  if (pasoActual.value.posicion === 'top') {
    tooltipPos.value = { top: Math.max(12, r.top - 180), left: tooltipPos.value.left }
  }
}

function siguiente(): void {
  if (indice.value < props.pasos.length - 1) {
    indice.value += 1
    actualizarRect()
  } else {
    finalizar()
  }
}

function anterior(): void {
  if (indice.value > 0) {
    indice.value -= 1
    actualizarRect()
  }
}

function finalizar(): void {
  emit('finish')
}

function saltar(): void {
  emit('skip')
}

watch(() => props.activo, (v) => {
  if (v) {
    indice.value = 0
    setTimeout(actualizarRect, 50)
  }
})

watch(() => indice.value, () => actualizarRect())

onMounted(() => {
  window.addEventListener('resize', actualizarRect)
  window.addEventListener('scroll', actualizarRect, true)
})

onUnmounted(() => {
  window.removeEventListener('resize', actualizarRect)
  window.removeEventListener('scroll', actualizarRect, true)
})
</script>

<template>
  <div v-if="activo && pasoActual" class="tutorial-overlay">
    <!-- Spotlight -->
    <svg class="tutorial-mask" width="100%" height="100%">
      <defs>
        <mask id="tutorial-spotlight">
          <rect width="100%" height="100%" fill="white" />
          <rect
            v-if="rect"
            :x="rect.left - 8"
            :y="rect.top - 8"
            :width="rect.width + 16"
            :height="rect.height + 16"
            rx="8"
            fill="black"
          />
        </mask>
      </defs>
      <rect
        width="100%"
        height="100%"
        fill="rgba(0,0,0,0.72)"
        mask="url(#tutorial-spotlight)"
      />
    </svg>

    <!-- Tooltip -->
    <div class="tutorial-tooltip" :style="{ top: tooltipPos.top + 'px', left: tooltipPos.left + 'px' }">
      <div class="tutorial-step-counter">
        Paso {{ indice + 1 }} de {{ pasos.length }}
      </div>
      <h3 class="tutorial-title">{{ pasoActual.titulo }}</h3>
      <p class="tutorial-desc">{{ pasoActual.descripcion }}</p>
      <div class="tutorial-actions">
        <button v-if="indice > 0" type="button" class="tutorial-btn" @click="anterior">
          ← Anterior
        </button>
        <button type="button" class="tutorial-btn tutorial-btn-primary" @click="siguiente">
          {{ indice < pasos.length - 1 ? 'Siguiente →' : 'Finalizar' }}
        </button>
        <button type="button" class="tutorial-btn tutorial-btn-skip" @click="saltar">
          Saltar tutorial
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: auto;
}

.tutorial-mask {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.tutorial-tooltip {
  position: absolute;
  width: 320px;
  max-width: calc(100vw - 24px);
  background: rgba(11, 14, 26, 0.98);
  border: 2px solid var(--amber);
  border-radius: 8px;
  padding: 12px 14px;
  color: var(--bone);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.85);
  font-size: 12px;
}

.tutorial-step-counter {
  font-size: 9px;
  color: var(--cyan);
  font-weight: 700;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
}

.tutorial-title {
  font-size: 13px;
  color: var(--gold);
  margin: 0 0 6px;
}

.tutorial-desc {
  font-size: 11.5px;
  color: var(--mist);
  line-height: 1.45;
  margin: 0 0 10px;
}

.tutorial-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tutorial-btn {
  padding: 5px 10px;
  font-size: 10.5px;
  background: rgba(27, 35, 64, 0.78);
  border: 1px solid var(--steel);
  color: var(--bone);
  border-radius: 4px;
  cursor: pointer;
}

.tutorial-btn-primary {
  border-color: var(--amber);
  color: var(--gold);
}

.tutorial-btn-skip {
  color: var(--mist);
}
</style>