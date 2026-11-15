<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EstadoMision } from '../services/api'

const props = defineProps<{
  mission: EstadoMision
  loading?: boolean
}>()

const emit = defineEmits<{
  (
    e: 'negotiate',
    payload: { bono_usd: number; argumento: string; acuerdo_id: string },
  ): void
  (e: 'finishNegotiation'): void
}>()

interface OpcionDialogo {
  id: string
  texto: string
  argumentoCorto: string
  bonoUsd: number
  acuerdoSugerido: 'austero' | 'estandar' | 'ambicioso'
  efectoAnimoJefe: 'sol' | 'nube' | 'lluvia'
  respuestaOrador: 'jefe' | 'blanca' | 'negro'
  respuestaNombre: string
  respuestaIcono: string
  respuestaTexto: string
}

interface RondaNegociacion {
  numero: number
  tituloRonda: string
  orador: 'jefe' | 'blanca' | 'negro'
  nombreOrador: string
  rolOrador: string
  iconoOrador: string
  dialogoInicial: string
  opciones: OpcionDialogo[]
}

const currentRoundIndex = ref<number>(0)
const bossMood = ref<'sol' | 'nube' | 'lluvia'>('nube')
const lastReply = ref<{
  speakerName: string
  speakerIcon: string
  text: string
  deltaUsd: number
} | null>(null)
const negotiationCompleted = ref<boolean>(false)
const totalSubidoUsd = ref<number>(0)

const rounds = computed<RondaNegociacion[]>(() => {
  const destNombre =
    props.mission.destino === 'LUNA'
      ? 'el Cráter Lunar Shackleton (384.400 km)'
      : 'la Órbita Terrestre Baja (OTB - 400 km)'

  return [
    {
      numero: 1,
      tituloRonda: 'RONDA 1 DE 3 · APERTURA ANTE EL COMISIONADO',
      orador: 'jefe',
      nombreOrador: 'GATO JEFE · COMISIONADO VANCE',
      rolOrador: 'Director General de la Agencia',
      iconoOrador: '/sprites/iconos/icono_gato_jefe.png',
      dialogoInicial: `«Siéntate, Capitán. Mis dos asistentes y yo hemos revisado tu plan hacia ${destNombre}. Tras perder los satélites automáticos en la tormenta Helios-9, el comité está escéptico. ¿Por qué deberíamos ampliarte el presupuesto inicial?»`,
      opciones: [
        {
          id: 'r1_ciencia_viva',
          texto:
            '«Porque ninguna sonda ciega puede recalibrar un espectrómetro en medio de la radiación solar; una dotación canina en laboratorio garantiza datos reales.»',
          argumentoCorto: 'Defensa de laboratorio tripulado en vivo',
          bonoUsd: 22000,
          acuerdoSugerido: 'estandar',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'jefe',
          respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
          respuestaIcono: '/sprites/iconos/icono_gato_jefe.png',
          respuestaTexto:
            '«Buen punto, Capitán. Las sondas fallaron precisamente por no poder adaptar sus filtros en órbita. Autorizo un primer incremento de +$22.000 USD base.»',
        },
        {
          id: 'r1_ambicion_total',
          texto:
            '«Si financian instrumentación pesada y enlace de alto caudal, mapearemos toda la anomalía Helios-9 en un solo vuelo histórico.»',
          argumentoCorto: 'Promesa de campaña científica de alta prioridad',
          bonoUsd: 32000,
          acuerdoSugerido: 'ambicioso',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'negro',
          respuestaNombre: 'ASESOR NEGRO · RIESGO Y CIENCIA',
          respuestaIcono: '/sprites/iconos/icono_gato_asistente_negro.png',
          respuestaTexto:
            '«Ambicioso, Capitán. El Comisionado aprueba +$32.000 USD base, pero toma nota: exigiremos un retorno científico de primer nivel en el tribunal final.»',
        },
        {
          id: 'r1_prudencia',
          texto:
            '«Operaremos con estricto control de costes y componentes esenciales para demostrar que el programa tripulado es rentable.»',
          argumentoCorto: 'Propuesta de viabilidad contenida',
          bonoUsd: 10000,
          acuerdoSugerido: 'austero',
          efectoAnimoJefe: 'nube',
          respuestaOrador: 'blanca',
          respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
          respuestaIcono: '/sprites/iconos/icono_gato_asistente_blanco.png',
          respuestaTexto:
            '«Por fin alguien que respeta el libro mayor. Te liberamos +$10.000 USD adicionales sin elevar tu cuota de exigencia científica.»',
        },
      ],
    },
    {
      numero: 2,
      tituloRonda: 'RONDA 2 DE 3 · OBJECIÓN DE LA AUDITORA BLANCA',
      orador: 'blanca',
      nombreOrador: 'AUDITORA BLANCA · ASISTENTE DE FINANZAS',
      rolOrador: 'Control Presupuestario',
      iconoOrador: '/sprites/iconos/icono_gato_asistente_blanco.png',
      dialogoInicial:
        '«Un momento, Comisionado. He revisado las nóminas del Hangar: este Capitán pretende contratar especialistas y comprar módulos regenerativos. ¡Cada sueldo y cada parche en vuelo sangrarán nuestras reservas!»',
      opciones: [
        {
          id: 'r2_especialistas',
          texto:
            '«Contratar a un ingeniero y un geólogo a bordo cuesta una fracción de lo que perderíamos si un subsistema falla a mitad de camino.»',
          argumentoCorto: 'Partida para contratación de especialistas',
          bonoUsd: 20000,
          acuerdoSugerido: 'estandar',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'jefe',
          respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
          respuestaIcono: '/sprites/iconos/icono_gato_jefe.png',
          respuestaTexto:
            '«El Capitán tiene razón, Auditora. Prefiero pagar el sueldo de dos especialistas hoy que lamentar una misión abortada mañana. Sube la partida en +$20.000 USD.»',
        },
        {
          id: 'r2_fondo_contingencia',
          texto:
            '«El seguimiento en tiempo real y las reparaciones remotas en tránsito cuestan dinero. Necesitamos un fondo de contingencia blindado.»',
          argumentoCorto: 'Fondo de reserva para imprevistos en vuelo',
          bonoUsd: 26000,
          acuerdoSugerido: 'ambicioso',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'blanca',
          respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
          respuestaIcono: '/sprites/iconos/icono_gato_asistente_blanco.png',
          respuestaTexto:
            '«Está bien, tienes argumentos técnicos sólidos. Desbloqueo +$26.000 USD para la cuenta operativa, pero vigilaré cada dólar que gastes en órbita.»',
        },
        {
          id: 'r2_reparacion_bordo',
          texto:
            '«Resolveremos las anomalías con nuestras propias baterías y herramientas a bordo antes de pedir soporte pagado a Tierra.»',
          argumentoCorto: 'Compromiso de autonomía operativa en vuelo',
          bonoUsd: 12000,
          acuerdoSugerido: 'estandar',
          efectoAnimoJefe: 'nube',
          respuestaOrador: 'blanca',
          respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
          respuestaIcono: '/sprites/iconos/icono_gato_asistente_blanco.png',
          respuestaTexto:
            '«Aceptable. Te asigno +$12.000 USD de margen operativo. Más te vale cuidar los vatios-hora de tu batería allá arriba.»',
        },
      ],
    },
    {
      numero: 3,
      tituloRonda: 'RONDA 3 DE 3 · EL RETO DEL ASESOR NEGRO',
      orador: 'negro',
      nombreOrador: 'ASESOR NEGRO · ASISTENTE DE RIESGO',
      rolOrador: 'Telemetría y Mecánica Orbital',
      iconoOrador: '/sprites/iconos/icono_gato_asistente_negro.png',
      dialogoInicial:
        '«Mi objeción es técnica, Comisionado. De nada sirve recolectar gigabytes en el Laboratorio si luego saturan la antena o se quedan sin Delta-v de retorno. ¿Qué garantía nos da, Capitán?»',
      opciones: [
        {
          id: 'r3_enlace_optico',
          texto:
            '«Con un último tramo de financiación instalaremos una antena de alta ganancia y transmitiremos el 100% de la telemetría antes de reentrar.»',
          argumentoCorto: 'Tramo final para ancho de banda y retorno',
          bonoUsd: 24000,
          acuerdoSugerido: 'ambicioso',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'jefe',
          respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
          respuestaIcono: '/sprites/iconos/icono_gato_jefe.png',
          respuestaTexto:
            '«Trato cerrado, Capitán. Tienes el respaldo total de esta mesa (+$24.000 USD finales). Ahora ve al Hangar y construye una nave digna del nombre Zenit.»',
        },
        {
          id: 'r3_margen_deltav',
          texto:
            '«Mantendremos la masa bajo el límite del lanzador y priorizaremos el Delta-v de retorno junto con ventanas de transmisión seguras.»',
          argumentoCorto: 'Garantía de margen de masa y Delta-v',
          bonoUsd: 16000,
          acuerdoSugerido: 'estandar',
          efectoAnimoJefe: 'sol',
          respuestaOrador: 'negro',
          respuestaNombre: 'ASESOR NEGRO · RIESGO Y CIENCIA',
          respuestaIcono: '/sprites/iconos/icono_gato_asistente_negro.png',
          respuestaTexto:
            '«Una respuesta de verdadero ingeniero de sistemas. Aprobamos +$16.000 USD adicionales. Nos veremos en el Tribunal de Evaluación a tu regreso.»',
        },
      ],
    },
  ]
})

const activeRound = computed(() => rounds.value[currentRoundIndex.value])

const moodImageSrc = computed(() => {
  if (bossMood.value === 'sol') return '/sprites/elementos/Sol.png'
  if (bossMood.value === 'nube') return '/sprites/elementos/Nube.png'
  return '/sprites/elementos/Lluvia.png'
})

const roundsTaken = ref<number>(0)

function selectDialogueOption(opt: OpcionDialogo): void {
  if (negotiationCompleted.value) return
  bossMood.value = opt.efectoAnimoJefe
  totalSubidoUsd.value += opt.bonoUsd
  roundsTaken.value += 1
  lastReply.value = {
    speakerName: opt.respuestaNombre,
    speakerIcon: opt.respuestaIcono,
    text: opt.respuestaTexto,
    deltaUsd: opt.bonoUsd,
  }

  emit('negotiate', {
    bono_usd: opt.bonoUsd,
    argumento: opt.argumentoCorto,
    acuerdo_id: opt.acuerdoSugerido,
  })

  if (currentRoundIndex.value < rounds.value.length - 1) {
    currentRoundIndex.value += 1
  } else {
    negotiationCompleted.value = true
  }
}
</script>

<template>
  <div class="vn-stage-container">
    <!-- 1. CABECERA DE LA ESCENA DE NOVELA VISUAL -->
    <div class="vn-top-bar">
      <div>
        <span class="vn-eyebrow">ETAPA 02 · NOVELA VISUAL DE NEGOCIACIÓN</span>
        <strong class="vn-location">OFICINA DE PLANIFICACIÓN · COMITÉ DE LOS 3 GATOS</strong>
      </div>
      <div class="vn-budget-counter">
        <span class="vn-budget-label">PRESUPUESTO NEGOCIADO:</span>
        <strong class="vn-budget-value">${{ mission.presupuesto_inicial_usd.toLocaleString() }} USD</strong>
        <span v-if="totalSubidoUsd > 0" class="vn-budget-bonus">
          (+${{ totalSubidoUsd.toLocaleString() }} logrados)
        </span>
      </div>
    </div>

    <!-- 2. ESCENARIO PIXEL ART EN GRANDE (OFICINA DE PLANIFICACIÓN + JEFE Y 2 ASISTENTES) -->
    <div class="vn-backdrop-frame">
      <img
        src="/sprites/escenas/oficina_planificacion.png"
        alt="Oficina de Planificación"
        class="vn-bg-image"
      />
      <div class="vn-bg-vignette"></div>

      <!-- Los 3 Gatos en sus escritorios: Asistente Blanca (Izq), Gato Jefe (Centro), Asistente Negro (Der) -->
      <div class="vn-office-actors">
        <!-- Asistente 1: Auditora Blanca (Izquierda) -->
        <div
          class="vn-actor-station assistant-left"
          :class="{ speaking: activeRound.orador === 'blanca' && !negotiationCompleted }"
        >
          <img
            src="/sprites/iconos/icono_gato_asistente_blanco.png"
            alt="Auditora Blanca"
            class="vn-actor-portrait"
          />
          <span class="vn-actor-tag">AUDITORA BLANCA</span>
        </div>

        <!-- Centro: El Gato Jefe (Comisionado Félix Vance) con su estado de ánimo encima -->
        <div
          class="vn-actor-station boss-center"
          :class="{ speaking: activeRound.orador === 'jefe' || negotiationCompleted }"
        >
          <div class="vn-boss-mood-float">
            <img :src="moodImageSrc" alt="Ánimo del Jefe" class="vn-mood-img" />
          </div>
          <img
            src="/sprites/iconos/icono_gato_jefe.png"
            alt="Gato Jefe"
            class="vn-actor-portrait boss-portrait"
          />
          <span class="vn-actor-tag boss-tag">GATO JEFE (VANCE)</span>
        </div>

        <!-- Asistente 2: Asesor Negro (Derecha) -->
        <div
          class="vn-actor-station assistant-right"
          :class="{ speaking: activeRound.orador === 'negro' && !negotiationCompleted }"
        >
          <img
            src="/sprites/iconos/icono_gato_asistente_negro.png"
            alt="Asesor Negro"
            class="vn-actor-portrait"
          />
          <span class="vn-actor-tag">ASESOR NEGRO</span>
        </div>
      </div>

      <!-- GLOBO DE DIÁLOGO SUPERIOR (QUIÉN HABLA EN EL COMITÉ DE GATOS) -->
      <div class="vn-npc-speech-bubble">
        <!-- Si hay respuesta reciente a tu argumento anterior, la muestra arriba -->
        <div v-if="lastReply" class="vn-last-reply-banner">
          <img :src="lastReply.speakerIcon" alt="Orador" class="vn-mini-icon" />
          <div class="vn-reply-copy">
            <strong>{{ lastReply.speakerName }}:</strong> {{ lastReply.text }}
          </div>
        </div>

        <!-- Intervención actual del Gato Jefe o sus Asistentes -->
        <div class="vn-speaker-main-row">
          <img
            :src="
              negotiationCompleted
                ? '/sprites/iconos/icono_gato_jefe.png'
                : activeRound.iconoOrador
            "
            :alt="activeRound.nombreOrador"
            class="vn-speaker-framed-icon"
          />
          <div class="vn-bubble-content">
            <div class="vn-speaker-header">
              <span class="vn-speaker-nameplate">
                {{
                  negotiationCompleted
                    ? 'GATO JEFE · VEREDICTO DE FINANCIACIÓN'
                    : activeRound.nombreOrador
                }}
              </span>
              <span class="vn-round-pill">
                {{
                  negotiationCompleted
                    ? 'NEGOCIACIÓN CONCLUIDA'
                    : activeRound.tituloRonda
                }}
              </span>
            </div>
            <p class="vn-dialogue-text">
              <template v-if="!negotiationCompleted">
                {{ activeRound.dialogoInicial }}
              </template>
              <template v-else>
                «Hemos escuchado tus tres argumentos, Capitán. Tu presupuesto final queda fijado en
                <strong>${{ mission.presupuesto_inicial_usd.toLocaleString() }} USD</strong> (disponibles tras chasis base:
                <strong>${{ mission.presupuesto_restante_usd.toLocaleString() }} USD</strong>). Dirígete al Hangar en la Etapa 3 para equipar la nave y contratar a tu tripulación.»
              </template>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. CAJA DE DECISIONES DEL JUGADOR ESTILO NOVELA VISUAL + RETRATO CAPTAIN DOG -->
    <div class="vn-player-decision-dock">
      <div class="vn-choices-column">
        <div class="vn-choices-header">
          <span>ELIGE TU ARGUMENTO PARA CONVENCER AL COMITÉ:</span>
        </div>

        <template v-if="!negotiationCompleted">
          <button
            v-for="opt in activeRound.opciones"
            :key="opt.id"
            class="vn-choice-line"
            :disabled="loading"
            @click="selectDialogueOption(opt)"
          >
            <span class="vn-choice-arrow">&gt;</span>
            <span class="vn-choice-text">{{ opt.texto }}</span>
            <span class="vn-choice-effect">
              [ Persuadir: +${{ opt.bonoUsd.toLocaleString() }} USD ]
            </span>
          </button>
        </template>

        <template v-else>
          <div class="vn-completed-actions">
            <button class="btn-primary vn-finish-btn" @click="emit('finishNegotiation')">
              ✓ FIRMAR PRESUPUESTO (${{ mission.presupuesto_inicial_usd.toLocaleString() }} USD · PLAN {{ mission.acuerdo_financiacion_id.toUpperCase() }}) Y AVANZAR A ETAPA 3 ►
            </button>
            <span class="vn-closed-deal-pill">
              Acuerdo sellado tras {{ roundsTaken }}/3 rondas ante el Comité
            </span>
          </div>
        </template>
      </div>

      <!-- Retrato enmarcado de CAPTAIN DOG (Jugador) con su icono Sol encima -->
      <div class="vn-captain-portrait-card">
        <div class="vn-captain-sun">
          <img src="/sprites/elementos/Sol.png" alt="Sol" class="vn-mood-img" />
        </div>
        <img
          src="/sprites/iconos/icono_perro_director.png"
          alt="Capitán Perro"
          class="vn-captain-img"
        />
        <div class="vn-captain-label">CAPITÁN PERRO [TÚ]</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vn-stage-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 100%;
  background: var(--void-deep);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 8px;
}

.vn-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  background: var(--cabin);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 5px 10px;
}

.vn-eyebrow {
  display: block;
  font-size: 9px;
  color: var(--cyan);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.vn-location {
  font-size: 12px;
  color: var(--gold);
}

.vn-budget-counter {
  display: flex;
  align-items: baseline;
  gap: 6px;
  background: var(--void);
  border: 1px solid var(--amber);
  padding: 4px 10px;
  border-radius: 4px;
}

.vn-budget-label {
  font-size: 9px;
  color: var(--mist);
}

.vn-budget-value {
  font-size: 14px;
  color: var(--gold);
}

.vn-budget-bonus {
  font-size: 10px;
  color: var(--green);
  font-weight: 700;
}

/* ESCENARIO DE FONDO EN GRANDE */
.vn-backdrop-frame {
  position: relative;
  flex: 1;
  min-height: 215px;
  border: 2px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px;
}

.vn-bg-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 35%;
  image-rendering: pixelated;
  z-index: 0;
}

.vn-bg-vignette {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(8, 11, 20, 0.35) 0%,
    rgba(8, 11, 20, 0.25) 45%,
    rgba(8, 11, 20, 0.85) 100%
  );
  z-index: 1;
}

/* LOS 3 GATOS EN LA OFICINA (JEFE + 2 AYUDANTES) */
.vn-office-actors {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  padding-top: 8px;
}

.vn-actor-station {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  position: relative;
  opacity: 0.82;
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.vn-actor-station.speaking {
  opacity: 1;
  transform: translateY(-4px) scale(1.05);
}

.vn-actor-portrait {
  width: 50px;
  height: 50px;
  image-rendering: pixelated;
  border: 2px solid var(--steel);
  border-radius: 4px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.75);
  background: var(--void);
}

.vn-actor-station.speaking .vn-actor-portrait {
  border-color: var(--amber);
  box-shadow: 0 0 14px rgba(255, 176, 0, 0.55);
}

.boss-portrait {
  width: 62px;
  height: 62px;
}

.vn-boss-mood-float {
  position: absolute;
  top: -26px;
  background: rgba(11, 14, 26, 0.9);
  border: 1px solid var(--amber);
  border-radius: 8px;
  padding: 2px 5px;
}

.vn-mood-img {
  width: 20px;
  height: 20px;
  image-rendering: pixelated;
  display: block;
}

.vn-actor-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  background: rgba(11, 14, 26, 0.92);
  border: 1px solid var(--steel);
  border-radius: 3px;
  color: var(--mist);
}

.boss-tag {
  color: var(--gold);
  border-color: var(--amber);
}

/* GLOBO DE DIÁLOGO ESTILO NOVELA VISUAL */
.vn-npc-speech-bubble {
  position: relative;
  z-index: 2;
  background: rgba(8, 11, 20, 0.94);
  border: 2px solid var(--bone);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8);
}

.vn-last-reply-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(79, 209, 197, 0.12);
  border-left: 3px solid var(--cyan);
  padding: 5px 8px;
  border-radius: 3px;
  font-size: 11px;
  color: var(--cyan);
}

.vn-mini-icon {
  width: 28px;
  height: 28px;
  image-rendering: pixelated;
  flex-shrink: 0;
}

.vn-speaker-main-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vn-speaker-framed-icon {
  width: 64px;
  height: 64px;
  image-rendering: pixelated;
  flex-shrink: 0;
  border-radius: 4px;
}

.vn-bubble-content {
  flex: 1;
}

.vn-speaker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 4px;
}

.vn-speaker-nameplate {
  background: var(--void);
  border: 1px solid var(--amber);
  color: var(--gold);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 0.05em;
}

.vn-round-pill {
  font-size: 9px;
  color: var(--cyan);
  font-weight: 700;
}

.vn-dialogue-text {
  font-size: 13px;
  color: var(--bone);
  line-height: 1.48;
}

/* CAJA DE RESPUESTAS DEL JUGADOR + RETRATO CAPTAIN DOG */
.vn-player-decision-dock {
  display: flex;
  align-items: stretch;
  gap: 10px;
  background: #080b14;
  border: 2px solid var(--bone);
  border-radius: 6px;
  padding: 10px 12px;
}

.vn-choices-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.vn-choices-header {
  font-size: 10px;
  font-weight: 700;
  color: var(--amber);
  letter-spacing: 0.05em;
}

.vn-choice-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  text-align: left;
  background: rgba(27, 35, 64, 0.55);
  border: 1px solid var(--steel);
  border-radius: 4px;
  padding: 7px 10px;
  font-size: 11px;
  color: var(--bone);
  cursor: pointer;
  transition: border-color 0.14s, background-color 0.14s;
}

.vn-choice-line:hover {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.14);
}

.vn-choice-arrow {
  color: var(--amber);
  font-weight: 700;
}

.vn-choice-text {
  flex: 1;
}

.vn-choice-effect {
  color: var(--cyan);
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.vn-completed-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.vn-finish-btn {
  flex: 1;
  padding: 10px 14px;
  font-size: 12px;
}

.vn-closed-deal-pill {
  font-size: 10px;
  color: var(--green);
  border: 1px solid var(--green);
  background: rgba(123, 216, 143, 0.12);
  padding: 6px 10px;
  border-radius: 4px;
  align-self: center;
}

.vn-captain-portrait-card {
  width: 98px;
  background: var(--cabin);
  border: 2px solid var(--gold);
  border-radius: 5px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  flex-shrink: 0;
}

.vn-captain-sun {
  position: absolute;
  top: -12px;
  right: -8px;
  background: var(--void);
  border: 1px solid var(--amber);
  border-radius: 50%;
  padding: 2px;
}

.vn-captain-img {
  width: 68px;
  height: 68px;
  image-rendering: pixelated;
  border-radius: 3px;
}

.vn-captain-label {
  margin-top: 4px;
  font-size: 8px;
  font-weight: 700;
  color: var(--gold);
  text-align: center;
  letter-spacing: 0.04em;
}
</style>
