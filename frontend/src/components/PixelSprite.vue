<script lang="ts">
export type AnimacionSprite =
  | 'perro_idle'
  | 'perro_caminar'
  | 'perro_interactuar'
  | 'perro_cientifico'
  | 'perro_ingeniero'
  | 'perro_medico'
  | 'perro_comunicaciones'
  | 'gato_idle'
  | 'gato_caminar'
  | 'gato_hablar'

/**
 * Devuelve el sprite de perro correspondiente a cada miembro de la tripulación.
 * Regla de diseño de Zenit: Los perros son SIEMPRE la tripulación; el gato es SIEMPRE el Jefe.
 */
export function obtenerSpriteTripulante(
  especialidad: string,
  esJugador = false,
): AnimacionSprite {
  if (esJugador) return 'perro_idle'
  if (especialidad === 'geologia' || especialidad === 'astrobiologia') {
    return 'perro_cientifico'
  }
  if (especialidad === 'ingenieria') {
    return 'perro_ingeniero'
  }
  if (especialidad === 'medicina') {
    return 'perro_medico'
  }
  return 'perro_comunicaciones'
}
</script>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

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

// Caché de los 8 frames del Perro Director con casco (PERRO1.zip)
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

// Caché de los Perros Especialistas de la Tripulación (ELEMENTOS.zip)
const RUTAS_ESPECIALISTAS: Record<string, { der: string; izq: string }> = {
  perro_cientifico: {
    der: '/sprites/elementos/PerroC.png',
    izq: '/sprites/elementos/PerroC_Izq.png',
  },
  perro_ingeniero: {
    der: '/sprites/elementos/PerroI.png',
    izq: '/sprites/elementos/PerroI_Izq.png',
  },
  perro_medico: {
    der: '/sprites/elementos/PerroD.png',
    izq: '/sprites/elementos/PerroD_Izq.png',
  },
  perro_comunicaciones: {
    der: '/sprites/elementos/PerroCom.png',
    izq: '/sprites/elementos/PerroCom_Izq.png',
  },
}

let framesPerroDer: HTMLCanvasElement[] = []
let framesPerroIzq: HTMLCanvasElement[] = []
const cacheEspecialistas: Record<
  string,
  { der: HTMLCanvasElement | null; izq: HTMLCanvasElement | null }
> = {}
let processedCatBossSheet: HTMLCanvasElement | null = null
let assetsPromise: Promise<void> | null = null

// Sprite separado del Gato Jefe (ya recortado, sin hoja de celdas)
const RUTA_GATO_JEFE = '/sprites/iconos/icono_gato_jefe.png'

const rutaIconoAnimo = computed(() => {
  if (!props.animo) return null
  if (props.animo === 'sol') return '/sprites/elementos/Sol.png'
  if (props.animo === 'nube') return '/sprites/elementos/Nube.png'
  return '/sprites/elementos/Lluvia.png'
})

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
      if (a > 0 && r > 238 && g > 238 && b > 234) {
        data[i + 3] = 0
      } else if (a > 0 && r > 224 && g > 224 && b > 220) {
        data[i + 3] = 45
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
    const promesasEspecialistas = Object.entries(RUTAS_ESPECIALISTAS).map(
      async ([key, rutas]) => {
        const [derCanvas, izqCanvas] = await Promise.all([
          cargarImagen(rutas.der),
          cargarImagen(rutas.izq),
        ])
        cacheEspecialistas[key] = { der: derCanvas, izq: izqCanvas }
      },
    )

    const [der, izq, catBoss] = await Promise.all([
      Promise.all(RUTAS_PERRO_DER.map(cargarImagen)),
      Promise.all(RUTAS_PERRO_IZQ.map(cargarImagen)),
      cargarImagen(RUTA_GATO_JEFE),
      ...promesasEspecialistas,
    ])
    framesPerroDer = der.filter((c): c is HTMLCanvasElement => c !== null)
    framesPerroIzq = izq.filter((c): c is HTMLCanvasElement => c !== null)
    processedCatBossSheet = catBoss
  })()
  return assetsPromise
}

function esAnimacionPerroDirector(anim: AnimacionSprite): boolean {
  return anim === 'perro_idle' || anim === 'perro_caminar' || anim === 'perro_interactuar'
}

function esAnimacionPerroEspecialista(anim: AnimacionSprite): boolean {
  return (
    anim === 'perro_cientifico' ||
    anim === 'perro_ingeniero' ||
    anim === 'perro_medico' ||
    anim === 'perro_comunicaciones'
  )
}

function dibujarCanvasCentrado(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  source: HTMLCanvasElement,
  bobOffsetY = 0,
): void {
  const scale = Math.min(canvas.width / source.width, (canvas.height - 4) / source.height)
  const dw = Math.round(source.width * scale)
  const dh = Math.round(source.height * scale)
  const dx = Math.round((canvas.width - dw) / 2)
  const dy = Math.round(canvas.height - dh + bobOffsetY)
  ctx.drawImage(source, 0, 0, source.width, source.height, dx, dy, dw, dh)
}

function dibujarFrame(): void {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.imageSmoothingEnabled = false

  // 1. Perro Astronauta del Director (PERRO1.zip: PerroDer1..4 y PerroIzq1..4)
  if (esAnimacionPerroDirector(props.animacion)) {
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
      dibujarCanvasCentrado(ctx, canvas, banco[idx])
      return
    }
  }

  // 2. Perros Especialistas de la Tripulación (ELEMENTOS.zip: estáticos en su puesto)
  if (esAnimacionPerroEspecialista(props.animacion)) {
    const par = cacheEspecialistas[props.animacion]
    const spriteCanvas = props.flipX ? par?.izq : par?.der
    if (spriteCanvas) {
      dibujarCanvasCentrado(ctx, canvas, spriteCanvas, 0)
      return
    }
  }

  // 3. Gato Jefe (SIEMPRE y EXCLUSIVAMENTE el Jefe): retrato separado y estable
  //    /sprites/iconos/icono_gato_jefe.png (reemplaza la hoja GATO.jpeg que fallaba al recortar)
  if (!processedCatBossSheet) return
  ctx.save()
  if (props.flipX) {
    ctx.translate(canvas.width, 0)
    ctx.scale(-1, 1)
  }
  dibujarCanvasCentrado(ctx, canvas, processedCatBossSheet)
  ctx.restore()
}

function iniciarBucleAnimacion(): void {
  if (timerId !== null) window.clearInterval(timerId)
  const intervalMs = Math.max(90, Math.round(1000 / props.fps))
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
    frameIndex = (frameIndex + 1) % 6
    dibujarFrame()
  },
)

watch(
  () => props.animar,
  (v) => {
    if (v) iniciarBucleAnimacion()
    else if (timerId !== null) {
      window.clearInterval(timerId)
      timerId = null
    }
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
  <div
    class="pixel-sprite-container"
    :class="{ 'has-animo': !!(animo && rutaIconoAnimo) }"
    :style="{ width: `${width}px` }"
  >
    <!-- Efecto de estado de ánimo en Pixel Art oficial (Sol.png, Nube.png, Lluvia.png) -->
    <div v-if="animo && rutaIconoAnimo" class="animo-widget" :class="`animo-${animo}`">
      <img :src="rutaIconoAnimo" :alt="`Estado de ánimo: ${animo}`" class="animo-pixel-img" />
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
  flex-shrink: 0;
}

.pixel-sprite-container.has-animo {
  padding-top: 24px;
}

.sprite-canvas {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  display: block;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.65));
}

.animo-widget {
  position: absolute;
  top: 0;
  padding: 2px 5px;
  border-radius: 8px;
  background: rgba(11, 14, 26, 0.88);
  border: 1px solid var(--steel);
  animation: float-bob 1.5s infinite ease-in-out;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.animo-pixel-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
  image-rendering: pixelated;
  display: block;
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
  background: rgba(11, 14, 26, 0.9);
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
