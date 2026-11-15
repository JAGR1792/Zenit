<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import TypewriterText from './TypewriterText.vue'
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

type EscenarioId = 'recorte_junta' | 'crisis_helios' | 'auditoria_hangar'
type OradorId = 'jefe' | 'blanca' | 'negro'
type AnimoId = 'sol' | 'nube' | 'lluvia'

interface OpcionDialogo {
  id: string
  texto: string
  argumentoCorto: string
  bonoUsd: number
  acuerdoSugerido: 'austero' | 'estandar' | 'ambicioso'
  efectoAnimoJefe: AnimoId
  efectoAnimoJugador: AnimoId
  respuestaOrador: OradorId
  respuestaNombre: string
  respuestaIcono: string
  respuestaTexto: string
}

interface RondaNegociacion {
  numero: number
  tituloRonda: string
  orador: OradorId
  nombreOrador: string
  iconoOrador: string
  dialogoInicial: string
  opciones: OpcionDialogo[]
}

interface EscenarioNegociacion {
  id: EscenarioId
  tituloCorto: string
  subtituloEscena: string
  fondoSrc: string
  rondas: RondaNegociacion[]
}

const ICONS: Record<OradorId, string> = {
  jefe: '/sprites/iconos/icono_gato_jefe.png',
  blanca: '/sprites/iconos/icono_gato_asistente_blanco.png',
  negro: '/sprites/iconos/icono_gato_asistente_negro.png',
}

// Secuencia de parpadeo del Gato Jefe naranja oficial (gatoJefe1..5.png)
const BLINK_SEQUENCE = [1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 1]
const blinkStep = ref<number>(0)
let blinkTimer: number | null = null

onMounted(() => {
  blinkTimer = window.setInterval(() => {
    blinkStep.value = (blinkStep.value + 1) % BLINK_SEQUENCE.length
  }, 240)
})

onUnmounted(() => {
  if (blinkTimer !== null) window.clearInterval(blinkTimer)
})

const animatedOrangeBossSrc = computed(
  () => `/sprites/gato/gatoJefe${BLINK_SEQUENCE[blinkStep.value]}.png`,
)

function moodToImg(mood: AnimoId): string {
  if (mood === 'sol') return '/sprites/elementos/Sol.png'
  if (mood === 'nube') return '/sprites/elementos/Nube.png'
  return '/sprites/elementos/Lluvia.png'
}

function escenarioInicialPorMision(mission: EstadoMision): EscenarioId {
  const suma = mission.id
    .split('')
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
  const lista: EscenarioId[] = ['recorte_junta', 'crisis_helios', 'auditoria_hangar']
  if (mission.destino === 'LUNA' && suma % 3 === 0) return 'crisis_helios'
  return lista[suma % lista.length]
}

const selectedScenarioId = ref<EscenarioId>(
  props.mission.dificultad === 'facil' ? 'recorte_junta' : escenarioInicialPorMision(props.mission),
)
const currentRoundIndex = ref<number>(0)
const bossMood = ref<AnimoId>('nube')
const playerMood = ref<AnimoId>('sol')
const negotiationCompleted = ref<boolean>(false)
const roundsTaken = ref<number>(0)
const ES_TEST_VN =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.MODE === 'test') ||
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITEST === true)
const dialogueReady = ref<boolean>(ES_TEST_VN)
const netDeltaUsd = ref<number>(0)
const lastReply = ref<{
  speakerName: string
  speakerIcon: string
  text: string
  wasPositive: boolean
} | null>(null)

watch(
  () => props.mission.id,
  () => {
    const inicial = escenarioInicialPorMision(props.mission)
    selectedScenarioId.value =
      props.mission.dificultad === 'facil' ? 'recorte_junta' : inicial
    currentRoundIndex.value = 0
    bossMood.value = 'nube'
    playerMood.value = 'sol'
    negotiationCompleted.value = false
    roundsTaken.value = 0
    netDeltaUsd.value = 0
    lastReply.value = null
    if (!ES_TEST_VN) dialogueReady.value = false
  },
)

const scenarios = computed<Record<EscenarioId, EscenarioNegociacion>>(() => {
  const destNombre =
    props.mission.destino === 'LUNA'
      ? 'el Cráter Lunar Shackleton (384.400 km)'
      : 'la Órbita Terrestre Baja (OTB · 400 km)'
  const presupuestoBase = Math.round(props.mission.presupuesto_inicial_usd)
  const techoJunta = presupuestoBase + (props.mission.destino === 'LUNA' ? 50000 : 40000)

  return {
    recorte_junta: {
      id: 'recorte_junta',
      tituloCorto: 'Recorte de la Junta',
      subtituloEscena: 'OFICINA DE PLANIFICACIÓN · RECORTE PREVENTIVO',
      fondoSrc: '/sprites/escenas/escena_inicial.jpg',
      rondas: [
        {
          numero: 1,
          tituloRonda: 'RONDA 1 DE 3 · PROPUESTA DEL COMISIONADO',
          orador: 'jefe',
          nombreOrador: 'GATO JEFE · COMISIONADO VANCE',
          iconoOrador: ICONS.jefe,
          dialogoInicial: `«La Junta Directiva dice que ${techoJunta.toLocaleString()} CZ es aceptable para llegar a ${destNombre}. Pero yo creo que ustedes son capaces de hacerlo con menos; por eso parto dándoles ${presupuestoBase.toLocaleString()} Créditos Zenit (CZ). ¿Qué me dices, Capitán?»`,
          opciones: [
            {
              id: 'rj_r1_ceder',
              texto:
                '«Tiene razón, Comisionado: podemos recortar baterías de reserva y raciones extra para salir todavía más baratos.»',
              argumentoCorto: 'Cesión prematura de reservas críticas',
              bonoUsd: -16000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'nube',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Me gusta tu espíritu de ahorro, Capitán. Si tú mismo admites que te sobra margen en reservas, ajusto tu asignación aún más abajo desde ahora.»',
            },
            {
              id: 'rj_r1_tecnica',
              texto:
                '«Acepto ajustar gastos superfluos, pero bajar del umbral sin redundancia eléctrica para los eclipses pondría en riesgo toda la telemetría.»',
              argumentoCorto: 'Defensa técnica del margen eléctrico en eclipse',
              bonoUsd: 24000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Buen contraargumento: recortar en vacío térmico sale más caro que financiar la redundancia. Te acerco al techo aprobado por la Junta.»',
            },
            {
              id: 'rj_r1_arrogante',
              texto:
                '«La Junta ya aprobó el techo máximo; no deberíamos perder tiempo justificando cada crédito si confía en mi historial.»',
              argumentoCorto: 'Exigencia de techo máximo sin respaldo técnico',
              bonoUsd: -20000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Aquí no firmamos cheques por orgullo, Capitán. Si no justificas tus necesidades de vuelo, te aplico un recorte disciplinario inmediato.»',
            },
          ],
        },
        {
          numero: 2,
          tituloRonda: 'RONDA 2 DE 3 · ESCRUTINIO DE LA AUDITORA',
          orador: 'blanca',
          nombreOrador: 'AUDITORA BLANCA · FINANZAS',
          iconoOrador: ICONS.blanca,
          dialogoInicial:
            '«Aun así, cada especialista que contrates y cada parche que pidas desde órbita dispararán la factura. ¿Para qué necesitas más margen si puedes llevar solo equipo básico?»',
          opciones: [
            {
              id: 'rj_r2_especialistas',
              texto:
                '«Un especialista bien pagado a bordo evita fallos de calibración y reduce reparaciones remotas costosas desde Tierra.»',
              argumentoCorto: 'Justificación de dotación especializada a bordo',
              bonoUsd: 22000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Cierto: pagar soporte remoto en emergencia destruye cualquier presupuesto. Libero una partida adicional para tu dotación.»',
            },
            {
              id: 'rj_r2_improvisar',
              texto:
                '«Si aparece una avería en el trayecto ya pediremos soluciones de emergencia sobre la marcha, no hace falta presupuestarlo hoy.»',
              argumentoCorto: 'Dependencia de rescates improvisados en vuelo',
              bonoUsd: -14000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Improvisar en el espacio es la receta de la bancarrota. Congelo parte de tu caja operativa para cubrir tu falta de previsión.»',
            },
            {
              id: 'rj_r2_disciplina',
              texto:
                '«Combinaremos herramientas de reparación internas con una dotación compacta, manteniendo reserva solo para lo irremplazable.»',
              argumentoCorto: 'Plan de autonomía con reserva acotada',
              bonoUsd: 10000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'nube',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Prudente y medido. Te concedo un refuerzo moderado en la cuenta, aunque seguiré vigilando tus gastos en el Hangar.»',
            },
          ],
        },
        {
          numero: 3,
          tituloRonda: 'RONDA 3 DE 3 · CIERRE DE RIESGO Y RETORNO',
          orador: 'negro',
          nombreOrador: 'ASESOR NEGRO · TELEMETRÍA',
          iconoOrador: ICONS.negro,
          dialogoInicial:
            '«Último punto, Capitán. Si te damos el tramo final de la Junta, ¿cómo garantizas que la nave regrese íntegra y con los datos completos de Helios-9?»',
          opciones: [
            {
              id: 'rj_r3_solo_ida',
              texto:
                '«Priorizaremos sensores científicos al límite; si falta combustible para el retorno, transmitiremos todo antes de quedar en órbita.»',
              argumentoCorto: 'Sacrificio del margen de retorno seguro',
              bonoUsd: -22000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · TELEMETRÍA',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«La Agencia no financia misiones suicidas ni pérdida de tripulación. El Comité retira de inmediato el bono de cierre.»',
            },
            {
              id: 'rj_r3_conservador',
              texto:
                '«Respetaremos el tope de masa del cohete y usaremos equipo estándar probado para garantizar un regreso limpio.»',
              argumentoCorto: 'Compromiso de masa segura y equipo probado',
              bonoUsd: 12000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Sensato. Prefiero una misión sobria que vuelva a casa que promesas vacías. Sumamos un último respaldo a tu cuenta.»',
            },
            {
              id: 'rj_r3_integral',
              texto:
                '«Equilibraremos motor de alto Isp, antena de enlace fiable y reserva de soporte vital sin superar la masa máxima de lanzamiento.»',
              argumentoCorto: 'Arquitectura integral masa, Delta-v y enlace',
              bonoUsd: 26000,
              acuerdoSugerido: 'ambicioso',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · TELEMETRÍA',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«Por fin escucho ingeniería de sistemas real. Comisionado, merece la ampliación completa para ejecutar ese diseño.»',
            },
          ],
        },
      ],
    },

    crisis_helios: {
      id: 'crisis_helios',
      tituloCorto: 'Crisis Helios-9',
      subtituloEscena: 'SALA DE CRISIS HELIOS-9 · AUDITORÍA DE SINIESTROS',
      fondoSrc: '/sprites/escenas/negociacion_sala_crisis.jpg',
      rondas: [
        {
          numero: 1,
          tituloRonda: 'RONDA 1 DE 3 · SOMBRA DE SONDAS PERDIDAS',
          orador: 'jefe',
          nombreOrador: 'GATO JEFE · COMISIONADO VANCE',
          iconoOrador: ICONS.jefe,
          dialogoInicial: `«Acabamos de perder dos sondas automáticas en la tormenta Helios-9 rumbo a ${destNombre}. La mitad del Comité pide reducir tu vuelo a lo mínimo indispensable. Convénceme.»`,
          opciones: [
            {
              id: 'ch_r1_riesgo_cero',
              texto:
                '«Esa tormenta fue exagerada por los sensores; nuestra nave no sufrirá ningún fallo ni necesitará contingencias.»',
              argumentoCorto: 'Negación del riesgo de radiación Helios-9',
              bonoUsd: -18000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · TELEMETRÍA',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«¿Exagerada? Tengo los restos de dos satélites en mi tableta. Desestimar el entorno te cuesta financiación desde el minuto uno.»',
            },
            {
              id: 'ch_r1_calibracion',
              texto:
                '«Las sondas cayeron porque ningún algoritmo pudo recalibrar filtros ni aislar fallos en tiempo real; una dotación preparada sí puede.»',
              argumentoCorto: 'Defensa de intervención humana ante fallos',
              bonoUsd: 26000,
              acuerdoSugerido: 'ambicioso',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Exacto. La latencia mató a las sondas antes de recibir un comando. Aprobamos refuerzo inicial para tu equipo científico.»',
            },
            {
              id: 'ch_r1_minimo',
              texto:
                '«Si el Comité desconfía, recortemos la carga experimental y vayamos únicamente a probar si el casco aguanta.»',
              argumentoCorto: 'Renuncia temprana al alcance científico',
              bonoUsd: -10000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'nube',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Si vas a renunciar a la ciencia antes de despegar, no necesitas todo este presupuesto. Recorto la partida científica.»',
            },
          ],
        },
        {
          numero: 2,
          tituloRonda: 'RONDA 2 DE 3 · CONSUMO ELÉCTRICO Y ENLACE',
          orador: 'negro',
          nombreOrador: 'ASESOR NEGRO · TELEMETRÍA',
          iconoOrador: ICONS.negro,
          dialogoInicial:
            '«En los eclipses los paneles caen a cero y las tormentas degradan la antena. ¿Cómo aseguras que los datos no queden atrapados en órbita?»',
          opciones: [
            {
              id: 'ch_r2_baterias',
              texto:
                '«Dimensionando generación solar positiva junto con banco de baterías y antena con alta probabilidad de enlace por ventana.»',
              argumentoCorto: 'Dimensionamiento eléctrico y ventanas de enlace',
              bonoUsd: 22000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · TELEMETRÍA',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«Eso demuestra que leíste la telemetría de eclipse antes de entrar aquí. Respaldo una ampliación para sistemas eléctricos y antena.»',
            },
            {
              id: 'ch_r2_apagar_o2',
              texto:
                '«Si falta potencia en eclipse apagaremos el reciclaje de soporte vital temporalmente mientras transmite la antena.»',
              argumentoCorto: 'Propuesta peligrosa de corte de soporte vital',
              bonoUsd: -18000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«¿Apagar el oxígeno para enviar un paquete de datos? Retén fondos, Auditora; este equipo necesita replantear sus prioridades.»',
            },
            {
              id: 'ch_r2_turnos',
              texto:
                '«Escalonaremos instrumentos y transmisiones en ventanas diurnas para mantener el balance eléctrico estable.»',
              argumentoCorto: 'Operación escalonada de consumo eléctrico',
              bonoUsd: 11000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'nube',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · TELEMETRÍA',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«Operación disciplinada, aunque justa de margen. Añadimos un refuerzo contenido para asegurar las ventanas.»',
            },
          ],
        },
        {
          numero: 3,
          tituloRonda: 'RONDA 3 DE 3 · RENDICIÓN DE CUENTAS',
          orador: 'blanca',
          nombreOrador: 'AUDITORA BLANCA · FINANZAS',
          iconoOrador: ICONS.blanca,
          dialogoInicial:
            '«Si la tormenta golpea en pleno vuelo habrá presiones para comprar ayuda técnica carísima. ¿Cuál es tu pacto final con finanzas?»',
          opciones: [
            {
              id: 'ch_r3_cheque',
              texto:
                '«Tengan preparada una línea de crédito abierta por si el retorno científico nos obliga a gastar sin límite.»',
              argumentoCorto: 'Solicitud de crédito abierto sin tope',
              bonoUsd: -14000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«El presupuesto es un límite duro, Capitán. Pedir crédito ilimitado hace que cierre el grifo todavía más.»',
            },
            {
              id: 'ch_r3_retorno',
              texto:
                '«Asumimos el presupuesto como límite duro: usaremos margen reservado para contingencias y entregaremos datos verificables al volver.»',
              argumentoCorto: 'Pacto de límite duro con reserva de contingencia',
              bonoUsd: 22000,
              acuerdoSugerido: 'ambicioso',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Así habla un director responsable. Cerramos el acuerdo con respaldo reforzado. Demuéstralo en el Hangar.»',
            },
          ],
        },
      ],
    },

    auditoria_hangar: {
      id: 'auditoria_hangar',
      tituloCorto: 'Auditoría de Hangar',
      subtituloEscena: 'GALERÍA DE HANGAR · COSTE POR KILOGRAMO',
      fondoSrc: '/sprites/escenas/negociacion_auditoria_hangar.jpg',
      rondas: [
        {
          numero: 1,
          tituloRonda: 'RONDA 1 DE 3 · LÍMITE DE MASA DEL LANZADOR',
          orador: 'blanca',
          nombreOrador: 'AUDITORA BLANCA · FINANZAS',
          iconoOrador: ICONS.blanca,
          dialogoInicial: `«Tu cohete tiene un tope fijo de ${props.mission.masa_lanzamiento_max_kg} kg en rampa. Si no puedes cargar módulos gigantes, ¿por qué tendríamos que ampliarte el dinero?»`,
          opciones: [
            {
              id: 'ah_r1_miniaturizacion',
              texto:
                '«Precisamente porque cada kilogramo cuenta: los motores de mayor Isp, paneles eficientes y sistemas compactos cuestan más por kilo.»',
              argumentoCorto: 'Relación coste-eficiencia por kilogramo de masa',
              bonoUsd: 26000,
              acuerdoSugerido: 'ambicioso',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Touché. Reducir masa manteniendo Delta-v nunca es barato. Desbloqueo fondos para tecnología ligera de alto rendimiento.»',
            },
            {
              id: 'ah_r1_no_lei',
              texto:
                '«Todavía no reviso la masa exacta de la ficha técnica; primero consigamos los fondos y luego vemos qué cabe.»',
              argumentoCorto: 'Desconocimiento del límite de masa en rampa',
              bonoUsd: -18000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«¿Negociar presupuesto sin saber cuánto puede levantar tu cohete? Te reduzco la asignación hasta que estudies el catálogo.»',
            },
            {
              id: 'ah_r1_quitar_equipo',
              texto:
                '«Entonces llevaremos una nave casi vacía para no acercarnos al límite y ahorrar dinero en la compra.»',
              argumentoCorto: 'Reducción voluntaria de equipamiento de misión',
              bonoUsd: -10000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'nube',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'blanca',
              respuestaNombre: 'AUDITORA BLANCA · FINANZAS',
              respuestaIcono: ICONS.blanca,
              respuestaTexto:
                '«Anotado: menos hardware requiere menos partida. Ajusto tu presupuesto acorde a ese recorte.»',
            },
          ],
        },
        {
          numero: 2,
          tituloRonda: 'RONDA 2 DE 3 · NÓMINAS EN EL HANGAR',
          orador: 'negro',
          nombreOrador: 'ASESOR NEGRO · OPERACIONES',
          iconoOrador: ICONS.negro,
          dialogoInicial:
            '«En el Hangar decidirás si contratas especialistas experimentados o vuelas con personal genérico. ¿Qué justifica pagar salarios altos?»',
          opciones: [
            {
              id: 'ah_r2_baratos',
              texto:
                '«Contrataremos al personal más barato disponible sin importar su especialidad para guardar dinero.»',
              argumentoCorto: 'Elección exclusiva por salario mínimo',
              bonoUsd: -15000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'nube',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · OPERACIONES',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«Un instrumento sin su especialista rinde mal y un novato falla en emergencias. Recortamos fondos por mala estrategia de equipo.»',
            },
            {
              id: 'ah_r2_balance',
              texto:
                '«Combinaremos al especialista exacto para nuestra carga científica principal con mantenimiento disciplinado del resto.»',
              argumentoCorto: 'Selección focalizada de especialidad clave',
              bonoUsd: 16000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'negro',
              respuestaNombre: 'ASESOR NEGRO · OPERACIONES',
              respuestaIcono: ICONS.negro,
              respuestaTexto:
                '«Criterio quirúrgico. Aprobamos una ampliación equilibrada para cubrir nóminas esenciales sin inflar la masa de soporte vital.»',
            },
            {
              id: 'ah_r2_veteranos',
              texto:
                '«La experiencia acelera las tareas científicas, eleva la calidad del dato y reduce el impacto de las emergencias en órbita.»',
              argumentoCorto: 'Valoración técnica de experiencia y especialidad',
              bonoUsd: 22000,
              acuerdoSugerido: 'ambicioso',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Exacto: cada día extra en el espacio cuesta energía y oxígeno. Te autorizo margen adicional para contratar talento probado.»',
            },
          ],
        },
        {
          numero: 3,
          tituloRonda: 'RONDA 3 DE 3 · MARGEN DE SEGURIDAD EN RAMPA',
          orador: 'jefe',
          nombreOrador: 'GATO JEFE · COMISIONADO VANCE',
          iconoOrador: ICONS.jefe,
          dialogoInicial:
            '«Cierro la revisión. Antes de abrirte las puertas del Hangar, dime cómo manejarás los márgenes de trayectoria y vida a bordo.»',
          opciones: [
            {
              id: 'ah_r3_quemar_todo',
              texto:
                '«Optaremos siempre por la ruta más agresiva quemando el propelente justo al filo de la reserva mínima.»',
              argumentoCorto: 'Trayectoria al límite sin reserva de Delta-v',
              bonoUsd: -20000,
              acuerdoSugerido: 'austero',
              efectoAnimoJefe: 'lluvia',
              efectoAnimoJugador: 'lluvia',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Volar sin margen de Delta-v ante una ventana secundaria es temerario. El Comité reduce tu margen de cierre.»',
            },
            {
              id: 'ah_r3_margen_sano',
              texto:
                '«Mantendremos días de O₂ y raciones por encima de la duración total, más reserva de Delta-v y masa bajo el tope.»',
              argumentoCorto: 'Resguardo completo de O₂, raciones y Delta-v',
              bonoUsd: 20000,
              acuerdoSugerido: 'estandar',
              efectoAnimoJefe: 'sol',
              efectoAnimoJugador: 'sol',
              respuestaOrador: 'jefe',
              respuestaNombre: 'GATO JEFE · COMISIONADO VANCE',
              respuestaIcono: ICONS.jefe,
              respuestaTexto:
                '«Excelente cierre, Capitán. Tienes el voto de confianza del Comité y un último respaldo para el Hangar.»',
            },
          ],
        },
      ],
    },
  }
})

const activeScenario = computed(() => scenarios.value[selectedScenarioId.value])
const activeRound = computed(() => activeScenario.value.rondas[currentRoundIndex.value])
const isOfficialOfficeScene = computed(() => selectedScenarioId.value === 'recorte_junta')
const bossMoodImg = computed(() => moodToImg(bossMood.value))
const playerMoodImg = computed(() => moodToImg(playerMood.value))

function speakerPortraitFor(orador: OradorId): string {
  if (orador === 'jefe' && isOfficialOfficeScene.value) {
    return animatedOrangeBossSrc.value
  }
  return ICONS[orador]
}

const escenariosPermitidos = computed<EscenarioId[]>(() => {
  if (props.mission.dificultad === 'facil') return ['recorte_junta']
  return ['recorte_junta', 'crisis_helios', 'auditoria_hangar']
})

function selectScenario(id: EscenarioId): void {
  if (roundsTaken.value > 0 || negotiationCompleted.value) return
  if (!escenariosPermitidos.value.includes(id)) return
  selectedScenarioId.value = id
  if (!ES_TEST_VN) dialogueReady.value = false
}

function selectDialogueOption(opt: OpcionDialogo): void {
  if (negotiationCompleted.value || props.loading) return

  bossMood.value = opt.efectoAnimoJefe
  playerMood.value = opt.efectoAnimoJugador
  netDeltaUsd.value += opt.bonoUsd
  roundsTaken.value += 1

  lastReply.value = {
    speakerName: opt.respuestaNombre,
    speakerIcon: speakerPortraitFor(opt.respuestaOrador),
    text: opt.respuestaTexto,
    wasPositive: opt.bonoUsd >= 0,
  }

  emit('negotiate', {
    bono_usd: opt.bonoUsd,
    argumento: opt.argumentoCorto,
    acuerdo_id: opt.acuerdoSugerido,
  })

  if (currentRoundIndex.value < activeScenario.value.rondas.length - 1) {
    currentRoundIndex.value += 1
    if (!ES_TEST_VN) dialogueReady.value = false
  } else {
    negotiationCompleted.value = true
    if (!ES_TEST_VN) dialogueReady.value = false
  }
}
</script>

<template>
  <div class="vn-stage-container">
    <!-- 1. CABECERA ESTILO DEBRIEFING / OFICINA -->
    <div class="vn-top-bar">
      <div>
        <span class="vn-eyebrow">ZENIT · NEGOCIACIÓN DE PRESUPUESTO</span>
        <strong class="vn-location">
          {{ activeScenario.subtituloEscena }} · COMITÉ DE LOS 3 GATOS
        </strong>
      </div>

      <div class="vn-top-right">
        <div v-if="roundsTaken === 0 && !negotiationCompleted" class="vn-scenario-switcher">
          <button
            v-for="sc in Object.values(scenarios)"
            :key="sc.id"
            type="button"
            class="vn-sc-pill"
            :class="{ active: selectedScenarioId === sc.id }"
            :disabled="!escenariosPermitidos.includes(sc.id) || roundsTaken > 0 || negotiationCompleted"
            @click="selectScenario(sc.id)"
          >
            {{ sc.tituloCorto }}
          </button>
        </div>

        <div class="vn-budget-counter">
          <span class="vn-budget-label">PRESUPUESTO APROBADO:</span>
          <strong class="vn-budget-value">
            {{ mission.presupuesto_inicial_usd.toLocaleString() }} CZ
          </strong>
        </div>

        <div class="vn-difficulty-pill">
          DIFICULTAD: {{ mission.dificultad.toUpperCase() }}
        </div>
      </div>
    </div>

    <!-- 2. ESCENARIO WIDESCREEN PIXEL ART CON LOS 3 GATOS + GLOBO DE DIÁLOGO -->
    <div class="vn-backdrop-frame">
      <img
        :src="activeScenario.fondoSrc"
        :alt="activeScenario.subtituloEscena"
        class="vn-bg-image"
      />
      <div class="vn-bg-vignette"></div>

      <!-- Icono de ánimo flotando sobre el Gato Jefe -->
      <div
        class="vn-boss-mood-badge"
        :class="{ 'center-boss': isOfficialOfficeScene }"
        title="Ánimo del Comité"
      >
        <img :src="bossMoodImg" alt="Ánimo del Gato Jefe" class="vn-mood-img" />
      </div>

      <!-- Globo de diálogo (zona inferior integrada en escena oficial o superior derecha en fondos alternos) -->
      <div class="vn-speech-cluster" :class="{ 'bottom-anchor': isOfficialOfficeScene }">
        <div class="vn-npc-speech-bubble">
          <div v-if="!isOfficialOfficeScene" class="vn-bubble-tail"></div>

          <div v-if="lastReply" class="vn-last-reply-banner" :class="{ negative: !lastReply.wasPositive }">
            <img :src="lastReply.speakerIcon" alt="Respuesta" class="vn-mini-icon" />
            <div class="vn-reply-copy">
              <strong>{{ lastReply.speakerName }}:</strong>
              <TypewriterText :text="lastReply.text" :key="`reply-${lastReply.text}`" />
            </div>
          </div>

          <div class="vn-speaker-main-row">
            <img
              :src="
                negotiationCompleted
                  ? speakerPortraitFor('jefe')
                  : speakerPortraitFor(activeRound.orador)
              "
              :alt="activeRound.nombreOrador"
              class="vn-speaker-framed-icon"
            />
            <div class="vn-bubble-content">
              <div class="vn-speaker-header">
                <span class="vn-speaker-nameplate">
                  {{
                    negotiationCompleted
                      ? 'GATO JEFE · VEREDICTO FINAL'
                      : activeRound.nombreOrador
                  }}
                </span>
                <span class="vn-round-pill">
                  {{
                    negotiationCompleted
                      ? 'ACUERDO CERRADO'
                      : activeRound.tituloRonda
                  }}
                </span>
              </div>

              <p class="vn-dialogue-text">
                <template v-if="!negotiationCompleted">
                  <TypewriterText
                    :text="activeRound.dialogoInicial"
                    :key="`vn-${selectedScenarioId}-${currentRoundIndex}`"
                    skip-hint="(clic para saltar)"
                    @complete="dialogueReady = true"
                  />
                </template>
                <template v-else>
                  <TypewriterText
                    :text="`«Tres rondas concluidas, Capitán. Tu presupuesto definitivo de misión queda cerrado en ${mission.presupuesto_inicial_usd.toLocaleString()} CZ (saldo disponible tras chasis base: ${mission.presupuesto_restante_usd.toLocaleString()} CZ). Pasa al Hangar en la Etapa 3.»`"
                    :key="`vn-final-${mission.id}`"
                    skip-hint="(clic para saltar)"
                    @complete="dialogueReady = true"
                  />
                </template>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. DOCK INFERIOR: RESPUESTAS NARRATIVAS (SIN SPOILERS) + RETRATO CAPITÁN PERRO -->
    <div class="vn-player-decision-dock">
      <div class="vn-choices-column">
        <div class="vn-choices-header">
          <span>CAPITÁN PERRO · RESPUESTAS AL COMITÉ (SIN GARANTÍA DE RESULTADO)</span>
        </div>

        <template v-if="!negotiationCompleted">
          <button
            v-for="opt in activeRound.opciones"
            :key="opt.id"
            type="button"
            class="vn-choice-line"
            :disabled="loading || !dialogueReady"
            :class="{ 'vn-choice-locked': !dialogueReady }"
            @click="selectDialogueOption(opt)"
          >
            <span class="vn-choice-arrow">&gt;</span>
            <span class="vn-choice-text">{{ opt.texto }}</span>
          </button>
        </template>

        <template v-else>
          <div class="vn-completed-actions">
            <button
              type="button"
              class="btn-primary vn-finish-btn"
              :disabled="loading || !dialogueReady"
              @click="emit('finishNegotiation')"
            >
              ✓ FIRMAR PRESUPUESTO ({{ mission.presupuesto_inicial_usd.toLocaleString() }} CZ) Y AVANZAR A ETAPA 3 ►
            </button>
            <span class="vn-closed-deal-pill">
              Acuerdo cerrado tras {{ roundsTaken }}/3 rondas · Balance neto:
              {{ netDeltaUsd >= 0 ? `+${netDeltaUsd.toLocaleString()}` : netDeltaUsd.toLocaleString() }} CZ
            </span>
          </div>
        </template>
      </div>

      <!-- Retrato enmarcado de CAPITÁN PERRO con su icono de ánimo -->
      <div class="vn-captain-portrait-card">
        <div class="vn-captain-sun">
          <img :src="playerMoodImg" alt="Ánimo Capitán Perro" class="vn-mood-img" />
        </div>
        <img
          src="/sprites/iconos/icono_captain_dog_casco.png"
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
  gap: 8px;
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
  padding: 6px 10px;
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

.vn-top-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.vn-scenario-switcher {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.vn-sc-pill {
  background: var(--void);
  border: 1px solid var(--steel);
  color: var(--mist);
  font-size: 9px;
  padding: 3px 7px;
  border-radius: 3px;
  cursor: pointer;
}

.vn-sc-pill.active {
  border-color: var(--cyan);
  color: var(--cyan);
  background: rgba(79, 209, 197, 0.12);
  font-weight: 700;
}

.vn-difficulty-pill {
  font-size: 9px;
  font-weight: 700;
  color: var(--gold);
  border: 1px solid var(--amber);
  background: rgba(255, 176, 0, 0.12);
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.05em;
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

/* ESCENARIO 16:9 LIMPIO CON LOS 3 GATOS Y GLOBO EN ESQUINA SUPERIOR DERECHA */
.vn-backdrop-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  min-height: 250px;
  max-height: 410px;
  border: 2px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 12px;
}

.vn-bg-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center center;
  image-rendering: pixelated;
  z-index: 0;
}

.vn-bg-vignette {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(8, 11, 20, 0.08) 0%,
    rgba(8, 11, 20, 0.16) 45%,
    rgba(8, 11, 20, 0.42) 100%
  );
  z-index: 1;
}

.vn-boss-mood-badge {
  position: absolute;
  top: 10%;
  left: 23%;
  z-index: 2;
  background: rgba(11, 14, 26, 0.9);
  border: 1px solid var(--amber);
  border-radius: 8px;
  padding: 3px 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.65);
}

.vn-boss-mood-badge.center-boss {
  top: 32%;
  left: 48%;
  transform: translateX(-50%);
}

.vn-mood-img {
  width: 22px;
  height: 22px;
  image-rendering: pixelated;
  display: block;
}

.vn-speech-cluster {
  position: relative;
  z-index: 2;
  align-self: flex-end;
  width: min(62%, 560px);
}

.vn-speech-cluster.bottom-anchor {
  align-self: stretch;
  width: 100%;
  margin-top: auto;
}

.vn-npc-speech-bubble {
  position: relative;
  background: rgba(8, 11, 20, 0.94);
  border: 2px solid var(--bone);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.85);
}

.vn-bubble-tail {
  position: absolute;
  left: -10px;
  top: 26px;
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-right: 10px solid var(--bone);
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

.vn-last-reply-banner.negative {
  background: rgba(255, 107, 107, 0.14);
  border-left-color: #ff6b6b;
  color: #ffb3b3;
}

.vn-mini-icon {
  width: 26px;
  height: 26px;
  image-rendering: pixelated;
  flex-shrink: 0;
  border-radius: 3px;
}

.vn-speaker-main-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.vn-speaker-framed-icon {
  width: 56px;
  height: 56px;
  image-rendering: pixelated;
  flex-shrink: 0;
  border-radius: 4px;
  border: 1px solid var(--steel);
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
  padding: 2px 7px;
  border-radius: 3px;
  letter-spacing: 0.05em;
}

.vn-round-pill {
  font-size: 9px;
  color: var(--cyan);
  font-weight: 700;
}

.vn-dialogue-text {
  font-size: 12.5px;
  color: var(--bone);
  line-height: 1.45;
  margin: 0;
}

/* CAJA INFERIOR DE RESPUESTAS + RETRATO CAPITÁN PERRO */
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
  font-size: 11.5px;
  color: var(--bone);
  cursor: pointer;
  transition: border-color 0.14s, background-color 0.14s;
}

.vn-choice-line:hover {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.14);
}

.vn-choice-line:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.vn-choice-line.vn-choice-locked {
  opacity: 0.4;
}

.vn-choice-arrow {
  color: var(--amber);
  font-weight: 700;
}

.vn-choice-text {
  flex: 1;
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
  width: 102px;
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
  width: 72px;
  height: 72px;
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

@media (max-width: 760px) {
  .vn-speech-cluster {
    width: 100%;
  }

  .vn-bubble-tail {
    display: none;
  }

  .vn-player-decision-dock {
    flex-direction: column;
  }

  .vn-captain-portrait-card {
    width: 100%;
    flex-direction: row;
    gap: 10px;
  }
}
</style>
