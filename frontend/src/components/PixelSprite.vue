<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

export type AnimacionSprite =
  | 'perro_idle'
  | 'perro_caminar'
  | 'perro_interactuar'
  | 'gato_idle'
  | 'gato_caminar'
  | 'gato_hablar'

const props = withDefaults(
  defineProps<{
    animacion: AnimacionSprite
    flipX?: boolean
    width?: number
    height?: number
    fps?: number
    animo?: 'sol' | 'nube' | 'lluvia' | null
    etiqueta?: string
  }>(),
  {
    flipX: false,
    width: 96,
    height: 96,
    fps: 8,
    animo: null,
    etiqueta: '',
  },
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
let timerId: number | null = null
let frameIndex = 0

// Caché global del spritesheet procesado sin fondo blanco
let processedSheet: HTMLCanvasElement | null = null
let loadingPromise: Promise<HTMLCanvasElement | null> | null = null

const COLS = 6
const ROWS = 4

function cargarYProcesarSpritesheet(): Promise<HTMLCanvasElement | null> {
  if (processedSheet) return Promise.resolve(processedSheet)
  if (loadingPromise) return loadingPromise

  loadingPromise = new Promise((resolve) => {
    if (typeof Image === 'undefined') {
      resolve(null)
      return
    }
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      const off = document.createElement('canvas')
      off.width = img.width
      off.height = img.height
      const ctx = off.getContext('2d')
      if (!ctx) {
        resolve(null)
        return
      }
      ctx.drawImage(img, 0, 0)
      try {
        const imgData = ctx.getImageData(0, 0, off.width, off.height)
        const data = imgData.data
        // Eliminar el fondo blanco/casi blanco del JPEG manteniendo los bordes oscuros del pixel art
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i]
          const g = data[i + 1]
          const b = data[i + 2]
          if (r > 238 && g > 238 && b > 234) {
            data[i + 3] = 0
          } else if (r > 224 && g > 224 && b > 220) {
            // Suavizar halo de compresión JPEG alrededor del contorno negro
            data[i + 3] = 60
          }
        }
        ctx.putImageData(imgData, 0, 0)
      } catch {
        // Si el entorno de test (jsdom) no soporta getImageData, continúa con la imagen base
      }
      processedSheet = off
      resolve(off)
    }
    img.onerror = () => resolve(null)
    img.src = '/sprites/Sprites1.jpg'
  })

  return loadingPromise
}

function obtenerFilaYFrames(anim: AnimacionSprite): { row: number; frames: number[] } {
  switch (anim) {
    case 'perro_caminar':
      return { row: 0, frames: [0, 1, 2, 3, 4, 5] }
    case 'perro_interactuar':
      return { row: 1, frames: [1, 2, 3, 4, 5] }
    case 'perro_idle':
      return { row: 1, frames: [5, 4] }
    case 'gato_caminar':
      return { row: 2, frames: [0, 1, 2, 3, 4, 5] }
    case 'gato_hablar':
      return { row: 3, frames: [1, 2, 3, 4, 5] }
    case 'gato_idle':
    default:
      return { row: 3, frames: [0, 1] }
  }
}

function dibujarFrame(): void {
  const canvas = canvasRef.value
  if (!canvas || !processedSheet) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const { row, frames } = obtenerFilaYFrames(props.animacion)
  const col = frames[frameIndex % frames.length]

  const cellW = processedSheet.width / COLS
  const cellH = processedSheet.height / ROWS
  const sx = col * cellW
  const sy = row * cellH

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.imageSmoothingEnabled = false

  ctx.save()
  if (props.flipX) {
    ctx.translate(canvas.width, 0)
    ctx.scale(-1, 1)
  }
  ctx.drawImage(processedSheet, sx, sy, cellW, cellH, 0, 0, canvas.width, canvas.height)
  ctx.restore()
}

function iniciarBucleAnimacion(): void {
  if (timerId !== null) window.clearInterval(timerId)
  const intervalMs = Math.max(70, Math.round(1000 / props.fps))
  timerId = window.setInterval(() => {
    frameIndex = (frameIndex + 1) % 12
    dibujarFrame()
  }, intervalMs)
}

watch(
  () => [props.animacion, props.flipX, props.fps],
  () => {
    frameIndex = 0
    dibujarFrame()
  },
)

onMounted(async () => {
  await cargarYProcesarSpritesheet()
  dibujarFrame()
  iniciarBucleAnimacion()
})

onUnmounted(() => {
  if (timerId !== null) window.clearInterval(timerId)
})
</script>

<template>
  <div class="pixel-sprite-container" :style="{ width: `${width}px` }">
    <!-- Efecto de estado de ánimo flotante sobre la cabeza (Sol, Nube, Lluvia) -->
    <div v-if="animo" class="animo-widget" :class="`animo-${animo}`">
      <span v-if="animo === 'sol'" class="animo-icon">☀️</span>
      <span v-else-if="animo === 'nube'" class="animo-icon">☁️</span>
      <span v-else class="animo-icon">🌧️</span>
    </div>

    <canvas
      ref="canvasRef"
      :width="width"
      :height="height"
      class="sprite-canvas"
    ></canvas>

    <div v-if="etiqueta" class="sprite-nameplate">{{ etiqueta }}</div>
  </div>
</template>

<style scoped>
.pixel-sprite-container {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  user-select: none;
}

.sprite-canvas {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  display: block;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.65));
}

.animo-widget {
  position: absolute;
  top: -18px;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 13px;
  background: rgba(11, 14, 26, 0.85);
  border: 1px solid var(--steel);
  animation: float-bob 1.5s infinite ease-in-out;
  z-index: 3;
}

.animo-sol {
  border-color: var(--sun);
  box-shadow: 0 0 8px rgba(245, 200, 76, 0.45);
}

.animo-nube {
  border-color: var(--cloud);
}

.animo-lluvia {
  border-color: var(--rain);
  box-shadow: 0 0 8px rgba(74, 120, 194, 0.55);
}

.sprite-nameplate {
  margin-top: -4px;
  padding: 1px 6px;
  background: rgba(11, 14, 26, 0.88);
  border: 1px solid var(--steel);
  border-radius: 3px;
  font-size: 9px;
  font-weight: 700;
  color: var(--bone);
  white-space: nowrap;
}

@keyframes float-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}
</style>
