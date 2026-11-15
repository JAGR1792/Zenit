import { onScopeDispose, onUnmounted, ref, watch, type Ref } from 'vue'

/**
 * Composable de efecto "máquina de escribir" (estilo Undertale) para cuadros de diálogo.
 *
 * Muestra el texto letra a letra con una cadencia configurable y emite un pequeño
 * "blip" de sonido por cada carácter (generado por Web Audio API, sin archivos
 * externos). El jugador puede saltar la animación pulsando el cuadro o llamando
 * a `saltar()`.
 *
 * En entorno de pruebas (Vitest) la animación se completa de forma inmediata para
 * no bloquear las aserciones síncronas.
 */
export interface OpcionesTypewriter {
  /** Milisegundos por carácter. Por defecto 26 ms. */
  velocidadMs?: number
  /** Activa/desactiva el sonido de "blip". Por defecto true. */
  sonido?: boolean
  /** Pausa adicional tras signos de puntuación (ms). */
  pausaPuntuacionMs?: number
}

const ES_TEST =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.MODE === 'test') ||
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITEST === true) ||
  (typeof globalThis !== 'undefined' &&
    (globalThis as any).process?.env?.VITEST === 'true')

let contextoAudio: AudioContext | null = null
function obtenerContextoAudio(): AudioContext | null {
  if (ES_TEST) return null
  if (contextoAudio) return contextoAudio
  try {
    const Ctor = (window as any).AudioContext || (window as any).webkitAudioContext
    if (!Ctor) return null
    contextoAudio = new Ctor()
    return contextoAudio
  } catch {
    return null
  }
}

function reproducirBlip(caracter: string): void {
  const ctx = obtenerContextoAudio()
  if (!ctx) return
  try {
    if (ctx.state === 'suspended') void ctx.resume()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    // Tono ligeramente variable según el carácter para que suene "vivo".
    const base = 320 + (caracter.charCodeAt(0) % 40) * 4
    osc.type = 'square'
    osc.frequency.value = base
    gain.gain.setValueAtTime(0.018, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.05)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.06)
  } catch {
    // Silencio si el navegador bloquea el audio.
  }
}

export function useTypewriter(
  fuente: Ref<string> | (() => string),
  opciones: OpcionesTypewriter = {},
) {
  const velocidadMs = opciones.velocidadMs ?? 26
  const sonido = opciones.sonido ?? true
  const pausaPuntuacionMs = opciones.pausaPuntuacionMs ?? 110

  const textoMostrado = ref('')
  const estaEscribiendo = ref(false)
  const completado = ref(false)

  let temporizador: number | null = null
  let cancelado = false

  function limpiarTemporizador(): void {
    if (temporizador !== null) {
      window.clearTimeout(temporizador)
      temporizador = null
    }
  }

  function obtenerTextoFuente(): string {
    return typeof fuente === 'function' ? fuente() : fuente.value
  }

  function escribir(texto: string): void {
    limpiarTemporizador()
    cancelado = false
    textoMostrado.value = ''
    completado.value = false

    if (!texto) {
      estaEscribiendo.value = false
      completado.value = true
      return
    }

    // En pruebas, completar de inmediato para no bloquear aserciones síncronas.
    if (ES_TEST || velocidadMs <= 0) {
      textoMostrado.value = texto
      estaEscribiendo.value = false
      completado.value = true
      return
    }

    estaEscribiendo.value = true
    let indice = 0
    const paso = (): void => {
      if (cancelado) return
      if (indice >= texto.length) {
        estaEscribiendo.value = false
        completado.value = true
        return
      }
      const ch = texto[indice]
      textoMostrado.value += ch
      if (sonido && ch.trim() !== '') reproducirBlip(ch)
      indice += 1
      const ultimo = texto[indice - 1]
      const pausaExtra = /[.!?…]/.test(ultimo) ? pausaPuntuacionMs : 0
      temporizador = window.setTimeout(paso, velocidadMs + pausaExtra)
    }
    paso()
  }

  function saltar(): void {
    cancelado = true
    limpiarTemporizador()
    textoMostrado.value = obtenerTextoFuente()
    estaEscribiendo.value = false
    completado.value = true
  }

  watch(
    () => obtenerTextoFuente(),
    (nuevo) => escribir(nuevo ?? ''),
    { immediate: true },
  )

  // Limpieza al desmontar.
  try {
    onUnmounted(() => {
      cancelado = true
      limpiarTemporizador()
    })
  } catch {
    // Fuera de un setup de componente: ignorar.
  }
  try {
    onScopeDispose(() => {
      cancelado = true
      limpiarTemporizador()
    })
  } catch {
    // Ignorar.
  }

  return {
    textoMostrado,
    estaEscribiendo,
    completado,
    saltar,
  }
}