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
    paso?: number
    animar?: boolean
  }>(),
  {
    flipX: false,
    width: 84,
    height: 106,
    fps: 8,
    animo: null,
    etiqueta: '',
    paso: 0,
    animar: true,
  },
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
let timerId: number | null = null
let frameIndex = 0

// Caché de los 8 frames individuales del perro extraídos de PERRO1.zip
const RUTAS_PERRO_DER = [
  '/sprites/perro/PerroDer1.png',
  '/sprites/perro/PerroDer2.png',
  '/sprites/perro/PerroDer3.png',
  '/sprites/perro/PerroDer4.png',
]
const RUTAS_PERRO_IZQ = [
  '/sprites/perro/PerroIzq1.png',
  '/sprites/perro/PerroIzq2.png',
  '/sprites/perro/PerroIzq3.png',
  '/sprites/perro/PerroIzq4.png',
]

let framesPerroDer: HTMLCanvasElement[] = []
let framesPerroIzq: HTMLCanvasElement[] = []
let processedCatSheet: HTMLCanvasElement | null = null
let assetsPromise: Promise<void> | null = null

const COLS = 6
const ROWS = 4

function limpiarFondoBlancoCanvas(img: HTMLImageElement): HTMLCanvasElement {
  const off = document.createElement('canvas')
  off.width = img.width
  off.height = img.height
  const ctx = off.getContext('2d')
  if (!ctx) return off

  ctx.drawImage(img, 0, 0)
  try {
    const imgData = ctx.getImageData(0, 0, off.width, off.height)
    const data = imgData.data
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i]
      const g = data[i + 1]
      const b = data[i + 2]
      const a = data[i + 3]
      if (a > 0 && r > 240 && g > 240 && b > 236) {
        data[i + 3] = 0
      } else if (a > 0 && r > 228 && g > 228 && b > 224) {
        data[i + 3] = 55
      }
    }
    ctx.putImageData(imgData, 0, 0)
  } catch {
    // En entorno de pruebas jsdom sin soporte de getImageData se mantiene la imagen base
  }
  return off
}

function cargarImagen(src: string): Promise<HTMLCanvasElement | null> {
  return new Promise((resolve) => {
    if (typeof Image === 'undefined') {
      resolve(null)
      return
    }
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(limpiarFondoBlancoCanvas(img))
    img.onerror = () => resolve(null)
    img.src = src
  })
}

function inicializarAssetsSprites(): Promise<void> {
  if (assetsPromise) return assetsPromise
  assetsPromise = (async () => {
    const [der, izq, catSheet] = await Promise.all([
      Promise.all(RUTAS_PERRO_DER.map(cargarImagen)),
      Promise.all(RUTAS_PERRO_IZQ.map(cargarImagen)),
      cargarImagen('/sprites/Sprites1.jpg'),
    ])
    framesPerroDer = der.filter((c): c is HTMLCanvasElement => c !== null)
    framesPerroIzq = izq.filter((c): c is HTMLCanvasElement => c !== null)
    processedCatSheet = catSheet
  })()
  return assetsPromise
}

function esAnimacionPerro(anim: AnimacionSprite): boolean {
  return anim === 'perro_idle' || anim === 'perro_caminar' || anim === 'perro_interactuar'
}

function dibujarFrame(): void {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.imageSmoothingEnabled = false

  // 1. Renderizar Perro Astronauta usando los PNG dedicados de PERRO1.zip (PerroDer1..4 y PerroIzq1..4)
  if (esAnimacionPerro(props.animacion)) {
    const banco = props.flipX ? framesPerroIzq : framesPerroDer
    if (banco.length > 0) {
      let idx = 0
      if (props.animacion === 'perro_caminar') {
        idx = frameIndex % banco.length
      } else if (props.animacion === 'perro_interactuar') {
        const secuencia = [1, 2, 3, 2]
        idx = secuencia[frameIndex % secuencia.length] % banco.length
      } else {
        idx = 0
      }
      const frameCanvas = banco[idx]
      // Conservar proporción original (~130x166) centrada en el canvas
      const scale = Math.min(canvas.width / frameCanvas.width, canvas.height / frameCanvas.height)
      const dw = Math.round(frameCanvas.width * scale)
      const dh = Math.round(frameCanvas.height * scale)
      const dx = Math.round((canvas.width - dw) / 2)
      const dy = Math.round(canvas.height - dh)
      ctx.drawImage(frameCanvas, 0, 0, frameCanvas.width, frameCanvas.height, dx, dy, dw, dh)
      return
    }
  }

  // 2. Renderizar Gato Especialista / Jefe desde Sprites1.jpg
  if (!processedCatSheet) return
  const row = props.animacion === 'gato_caminar' ? 2 : 3
  const frames =
    props.animacion === 'gato_caminar'
      ? [0, 1, 2, 3, 4, 5]
      : props.animacion === 'gato_hablar'
        ? [1, 2, 3, 4, 5]
        : [0, 1]
  const col = frames[frameIndex % frames.length]

  const cellW = processedCatSheet.width / COLS
  const cellH = processedCatSheet.height / ROWS
  const sx = col * cellW
  const sy = row * cellH

  ctx.save()
  if (props.flipX) {
    ctx.translate(canvas.width, 0)
    ctx.scale(-1, 1)
  }
  ctx.drawImage(processedCatSheet, sx, sy, cellW, cellH, 0, 0, canvas.width, canvas.height)
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

watch(
  () => props.paso,
  () => {
    if (props.animacion === 'perro_caminar' || props.animacion === 'gato_caminar') {
      frameIndex = (frameIndex + 1) % 6
      dibujarFrame()
    }
  },
)

watch(
  () => props.animar,
  (v) => {
    if (v) iniciarBucleAnimacion()
    else if (timerId !== null) { window.clearInterval(timerId); timerId = null }
  },
)

onMounted(async () => {
  await inicializarAssetsSprites()
  dibujarFrame()
  if (props.animar) iniciarBucleAnimacion()
})

onUnmounted(() => {
  if (timerId !== null) window.clearInterval(timerId)
})
</script>

<template>
  <div class="pixel-sprite-container" :style="{ width: `${width}px` }">
    <!-- Efecto de estado de ánimo flotante sobre la cabeza (Sol, Nube, Lluvia) -->
    <div v-if="animo" class="animo-widget" :class="`animo-${animo}`">
      <span v-if="animo === 'sol'" class="animo-icon">☀</span>
      <span v-else-if="animo === 'nube'" class="animo-icon">☁</span>
      <span v-else class="animo-icon">🌧</span>
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
  margin-top: -2px;
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
