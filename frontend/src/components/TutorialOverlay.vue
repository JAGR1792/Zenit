<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

export interface PasoTutorial {
  selector: string
  titulo: string
  descripcion: string
  posicion?: 'top' | 'bottom' | 'left' | 'right'
}

const props = withDefaults(
  defineProps<{
    pasos: PasoTutorial[]
    activo: boolean
    pasoInicial?: number
    etiquetaContexto?: string
  }>(),
  {
    pasoInicial: 0,
    etiquetaContexto: 'GUÍA REACTIVA',
  },
)

const emit = defineEmits<{
  (e: 'finish'): void
  (e: 'skip'): void
  (e: 'update:pasoInicial', valor: number): void
}>()

const indice = ref(0)
const rect = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const tooltipPos = ref<{ top: number; left: number }>({ top: 16, left: 16 })
const tooltipRef = ref<HTMLElement | null>(null)
const overlayRef = ref<HTMLElement | null>(null)

const pasosLista = computed<PasoTutorial[]>(() => props.pasos ?? [])
const pasoActual = computed<PasoTutorial | null>(() => pasosLista.value[indice.value] ?? null)

function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val))
}

function casiIgual(a: number, b: number): boolean {
  return Math.abs(a - b) < 0.5
}

function buscarElementoObjetivo(selector: string): HTMLElement | null {
  if (!selector) return null
  const partes = selector
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  for (const subselector of partes) {
    try {
      const candidatos = document.querySelectorAll(subselector)
      for (const node of candidatos) {
        const el = node as HTMLElement
        const r = el.getBoundingClientRect()
        if (r.width > 0 && r.height > 0) {
          return el
        }
      }
    } catch {
      // Ignorar subselector inválido y continuar con respaldo.
    }
  }
  return null
}

function calcularPosicionTooltip(
  r: { top: number; left: number; right: number; bottom: number; width: number; height: number } | null,
  preferencia?: 'top' | 'bottom' | 'left' | 'right',
): { top: number; left: number } {
  const vw = window.innerWidth || 1280
  const vh = window.innerHeight || 720
  const tipW = tooltipRef.value?.offsetWidth || Math.min(340, vw - 24)
  const tipH = tooltipRef.value?.offsetHeight || 190
  const margen = 12
  const separacion = 14
  const maxLeft = Math.max(margen, vw - tipW - margen)
  const maxTop = Math.max(margen, vh - tipH - margen)

  if (!r) {
    return {
      top: clamp((vh - tipH) / 2, margen, maxTop),
      left: clamp((vw - tipW) / 2, margen, maxLeft),
    }
  }

  const candidatos: Array<'bottom' | 'top' | 'left' | 'right'> = preferencia
    ? [preferencia, 'bottom', 'top', 'left', 'right']
    : ['bottom', 'top', 'left', 'right']

  for (const lado of candidatos) {
    if (lado === 'bottom' && r.bottom + separacion + tipH <= vh - margen) {
      return {
        top: r.bottom + separacion,
        left: clamp(r.left, margen, maxLeft),
      }
    }
    if (lado === 'top' && r.top - separacion - tipH >= margen) {
      return {
        top: r.top - separacion - tipH,
        left: clamp(r.left, margen, maxLeft),
      }
    }
    if (lado === 'left' && r.left - separacion - tipW >= margen) {
      return {
        top: clamp(r.top, margen, maxTop),
        left: r.left - separacion - tipW,
      }
    }
    if (lado === 'right' && r.right + separacion + tipW <= vw - margen) {
      return {
        top: clamp(r.top, margen, maxTop),
        left: r.right + separacion,
      }
    }
  }

  // Respaldo seguro dentro del viewport evitando tapar el objetivo en lo posible
  const espacioAbajo = vh - r.bottom
  const espacioArriba = r.top
  const fallbackTop =
    espacioAbajo >= espacioArriba
      ? clamp(r.bottom + separacion, margen, maxTop)
      : clamp(r.top - tipH - separacion, margen, maxTop)

  return {
    top: fallbackTop,
    left: clamp(r.left, margen, maxLeft),
  }
}

async function actualizarRect(): Promise<void> {
  if (!props.activo || !pasoActual.value) {
    rect.value = null
    return
  }

  const el = buscarElementoObjetivo(pasoActual.value.selector)
  if (el) {
    const preRect = el.getBoundingClientRect()
    const vh = window.innerHeight || 720
    const fueraDeVista = preRect.bottom < 0 || preRect.top > vh
    if (fueraDeVista && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    }
  }

  await nextTick()

  const rRaw = el ? el.getBoundingClientRect() : null
  const nextRect =
    rRaw && rRaw.width > 0 && rRaw.height > 0
      ? { top: rRaw.top, left: rRaw.left, width: rRaw.width, height: rRaw.height }
      : null

  if (
    !rect.value ||
    !nextRect ||
    !casiIgual(rect.value.top, nextRect.top) ||
    !casiIgual(rect.value.left, nextRect.left) ||
    !casiIgual(rect.value.width, nextRect.width) ||
    !casiIgual(rect.value.height, nextRect.height)
  ) {
    if (rect.value !== nextRect) {
      rect.value = nextRect
    }
  }

  await nextTick()

  const nextPos = calcularPosicionTooltip(
    rRaw && rRaw.width > 0 && rRaw.height > 0 ? rRaw : null,
    pasoActual.value.posicion,
  )
  if (!casiIgual(tooltipPos.value.top, nextPos.top) || !casiIgual(tooltipPos.value.left, nextPos.left)) {
    tooltipPos.value = nextPos
  }
}

let rafPendiente = 0
function programarActualizacion(): void {
  if (!props.activo) return
  if (rafPendiente) cancelAnimationFrame(rafPendiente)
  rafPendiente = requestAnimationFrame(() => {
    rafPendiente = 0
    void actualizarRect()
  })
}

function sincronizarIndiceExterno(nuevo?: number): void {
  const total = pasosLista.value.length
  if (total === 0) {
    indice.value = 0
    return
  }
  const objetivo = typeof nuevo === 'number' ? clamp(nuevo, 0, total - 1) : 0
  indice.value = objetivo
}

function siguiente(): void {
  const total = pasosLista.value.length
  if (indice.value < total - 1) {
    indice.value += 1
    emit('update:pasoInicial', indice.value)
    programarActualizacion()
  } else {
    finalizar()
  }
}

function anterior(): void {
  if (indice.value > 0) {
    indice.value -= 1
    emit('update:pasoInicial', indice.value)
    programarActualizacion()
  }
}

function finalizar(): void {
  emit('finish')
}

function saltar(): void {
  emit('skip')
}

watch(
  () => props.activo,
  (activo) => {
    if (activo) {
      sincronizarIndiceExterno(props.pasoInicial)
      void actualizarRect()
      programarActualizacion()
    } else {
      rect.value = null
    }
  },
  { immediate: true },
)

watch(
  () => props.pasoInicial,
  (nuevo) => {
    if (props.activo) {
      sincronizarIndiceExterno(nuevo)
      programarActualizacion()
    }
  },
)

watch(
  () => props.pasos,
  () => {
    if (props.activo) {
      sincronizarIndiceExterno(props.pasoInicial ?? indice.value)
      programarActualizacion()
    }
  },
  { deep: true },
)

watch(
  () => indice.value,
  () => {
    if (props.activo) {
      void actualizarRect()
    }
  },
)

function manejarTeclado(ev: KeyboardEvent): void {
  if (!props.activo) return
  if (ev.key === 'Escape') {
    ev.preventDefault()
    finalizar()
  }
}

let observador: MutationObserver | null = null

onMounted(() => {
  window.addEventListener('resize', programarActualizacion)
  window.addEventListener('scroll', programarActualizacion, true)
  window.addEventListener('keydown', manejarTeclado)
  observador = new MutationObserver((mutaciones) => {
    if (!props.activo) return
    const soloDentroDeOverlay = mutaciones.every(
      (m) => overlayRef.value && overlayRef.value.contains(m.target),
    )
    if (!soloDentroDeOverlay) {
      programarActualizacion()
    }
  })
  observador.observe(document.body, { childList: true, subtree: true })
  if (props.activo) {
    void actualizarRect()
  }
})

onUnmounted(() => {
  if (rafPendiente) cancelAnimationFrame(rafPendiente)
  window.removeEventListener('resize', programarActualizacion)
  window.removeEventListener('scroll', programarActualizacion, true)
  window.removeEventListener('keydown', manejarTeclado)
  if (observador) observador.disconnect()
})
</script>

<template>
  <div
    v-if="activo && pasoActual"
    ref="overlayRef"
    class="tutorial-overlay"
    role="region"
    aria-label="Tutorial interactivo de misión"
  >
    <!-- Spotlight visual NO bloqueante (permite interactuar con el juego mientras guía) -->
    <svg class="tutorial-mask" width="100%" height="100%" aria-hidden="true">
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
        fill="rgba(0, 0, 0, 0.45)"
        mask="url(#tutorial-spotlight)"
      />
    </svg>

    <!-- Anillo de enfoque ámbar alrededor del elemento destacado -->
    <div
      v-if="rect"
      class="tutorial-highlight-ring"
      aria-hidden="true"
      :style="{
        top: `${rect.top - 8}px`,
        left: `${rect.left - 8}px`,
        width: `${rect.width + 16}px`,
        height: `${rect.height + 16}px`,
      }"
    ></div>

    <!-- Tarjeta flotante interactiva -->
    <div
      ref="tooltipRef"
      class="tutorial-tooltip"
      :style="{ top: `${tooltipPos.top}px`, left: `${tooltipPos.left}px` }"
      tabindex="-1"
      @keydown.left.stop="anterior"
      @keydown.right.stop="siguiente"
    >
      <div class="tutorial-top-row">
        <div class="tutorial-step-counter">
          {{ etiquetaContexto }} · PASO {{ indice + 1 }} DE {{ pasosLista.length }}
        </div>
        <button
          type="button"
          class="tutorial-close-x"
          title="Ocultar guía en esta etapa (Esc)"
          aria-label="Ocultar guía en esta etapa"
          @click="finalizar"
        >
          ✕
        </button>
      </div>
      <h3 class="tutorial-title">{{ pasoActual.titulo }}</h3>
      <p class="tutorial-desc">{{ pasoActual.descripcion }}</p>
      <div class="tutorial-actions">
        <button v-if="indice > 0" type="button" class="tutorial-btn" @click="anterior">
          ← Anterior
        </button>
        <button type="button" class="tutorial-btn tutorial-btn-primary" @click="siguiente">
          {{ indice < pasosLista.length - 1 ? 'Siguiente →' : 'Entendido ✓' }}
        </button>
        <button type="button" class="tutorial-btn tutorial-btn-skip" @click="saltar">
          No mostrar más
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
  pointer-events: none;
}

.tutorial-mask {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.tutorial-highlight-ring {
  position: fixed;
  border: 2px solid var(--amber, #f59e0b);
  border-radius: 8px;
  box-shadow:
    0 0 0 2px rgba(245, 158, 11, 0.25),
    0 0 18px rgba(245, 158, 11, 0.45);
  pointer-events: none;
  transition:
    top 0.18s ease,
    left 0.18s ease,
    width 0.18s ease,
    height 0.18s ease;
}

.tutorial-tooltip {
  position: fixed;
  width: 340px;
  max-width: calc(100vw - 24px);
  background: rgba(11, 14, 26, 0.96);
  border: 2px solid var(--amber, #f59e0b);
  border-radius: 8px;
  padding: 12px 14px;
  color: var(--bone, #f3f0e6);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.88);
  font-size: 12px;
  pointer-events: auto;
  transition:
    top 0.18s ease,
    left 0.18s ease;
}

.tutorial-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.tutorial-step-counter {
  font-size: 9.5px;
  color: var(--cyan, #38bdf8);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.tutorial-close-x {
  background: transparent;
  border: 1px solid rgba(148, 163, 184, 0.35);
  color: var(--mist, #b6c2d9);
  border-radius: 4px;
  width: 22px;
  height: 22px;
  line-height: 1;
  font-size: 11px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.tutorial-close-x:hover {
  border-color: var(--amber, #f59e0b);
  color: var(--gold, #fbbf24);
}

.tutorial-title {
  font-size: 13.5px;
  color: var(--gold, #fbbf24);
  margin: 0 0 6px;
}

.tutorial-desc {
  font-size: 11.5px;
  color: var(--mist, #b6c2d9);
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
  background: rgba(27, 35, 64, 0.85);
  border: 1px solid var(--steel, #334155);
  color: var(--bone, #f3f0e6);
  border-radius: 4px;
  cursor: pointer;
}

.tutorial-btn:hover {
  border-color: var(--cyan, #38bdf8);
}

.tutorial-btn-primary {
  border-color: var(--amber, #f59e0b);
  color: var(--gold, #fbbf24);
  font-weight: 600;
}

.tutorial-btn-skip {
  color: var(--mist, #b6c2d9);
  margin-left: auto;
}
</style>
