import { mount } from '@vue/test-utils'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import BossReportScene from './BossReportScene.vue'
import DestinationRooms2D from './DestinationRooms2D.vue'
import GameMainMenu from './GameMainMenu.vue'
import ShipSchematic from './ShipSchematic.vue'
import VisualNovelNegotiation from './VisualNovelNegotiation.vue'
import type { InformeFinal, TripulanteEstado } from '../services/api'
import { createMissionLocal, sendDecisionLocal } from '../services/localSimulationFallback'

beforeAll(() => {
  // jsdom no implementa canvas 2D nativo; evitamos advertencias al montar PixelSprite
  if (typeof HTMLCanvasElement !== 'undefined') {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
  }
})

function crearInformePrueba(): InformeFinal {
  return {
    mission_id: 'zenit-test-01',
    final_id: 'exito_cientifico_pleno',
    numero_final: 1,
    titulo_final: 'Final 1 — Éxito Científico Sobresaliente',
    subtitulo_final: 'Retorno seguro con telemetría científica completa.',
    puntuacion_global: 91,
    hubo_muertes_tripulacion: false,
    silencio_previo_segundos: 3,
    dialogo_jefe_apertura: 'Excelente trabajo en órbita. La agencia respalda tu informe.',
    monologo_cuarta_pared: 'Cada parámetro de la ficha técnica se cumplió sin improvisar.',
    dimensiones: [
      {
        id: 'eficiencia_financiera',
        nombre: 'Eficiencia Financiera',
        puntuacion: 88,
        estado_etiqueta: 'ÓPTIMO',
        comentario_jefe: 'Cierre presupuestario dentro del margen pactado.',
        explicacion_tecnica: 'Reserva final positiva y cero sobrecostes críticos.',
      },
      {
        id: 'exito_cientifico',
        nombre: 'Éxito Científico',
        puntuacion: 94,
        estado_etiqueta: 'SOBRESALIENTE',
        comentario_jefe: 'Cobertura completa del paquete experimental.',
        explicacion_tecnica: 'Datos científicos transmitidos sin degradación.',
      },
      {
        id: 'supervivencia_salud',
        nombre: 'Supervivencia y Salud',
        puntuacion: 92,
        estado_etiqueta: 'SALUDABLE',
        comentario_jefe: 'Tripulación estable y sin bajas.',
        explicacion_tecnica: 'Soporte vital y moral por encima del umbral seguro.',
      },
    ],
    trazabilidad_causal: ['Negociación inicial equilibrada', 'Transmisión científica completada'],
    recomendaciones_ingenieria: ['Mantener reserva de enlace adicional para Luna.'],
    frase_despedida: 'Nos vemos en la próxima ventana de lanzamiento.',
    resumen_tecnico_datos: { presupuesto_restante_usd: 120000 },
  }
}

describe('Componentes principales del simulador Zenit', () => {
  it('VisualNovelNegotiation oculta montos en opciones, permite ganar o perder presupuesto y cambia escenarios', async () => {
    const mision = createMissionLocal({
      nombre_mision: 'Zenit Test VN',
      destino: 'OTB',
      dificultad: 'normal',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })

    const wrapper = mount(VisualNovelNegotiation, {
      props: { mission: mision, loading: false },
    })

    expect(wrapper.text()).toContain('COMITÉ DE LOS 3 GATOS')

    // Cambiar explícitamente al escenario de Recorte de la Junta
    const btnRecorte = wrapper
      .findAll('.vn-sc-pill')
      .find((b) => b.text().includes('Recorte de la Junta'))
    expect(btnRecorte).toBeTruthy()
    await btnRecorte!.trigger('click')
    expect(wrapper.text()).toContain('La Junta Directiva dice')

    // Verifica uso de moneda ficticia Créditos Zenit (CZ) en lugar de dólares reales
    expect(wrapper.text()).toContain('CZ')
    expect(wrapper.text()).not.toContain('USD')

    // Ninguna opción narrativa debe revelar montos de dinero antes de decidir
    const opcionesTexto = wrapper.find('.vn-choices-column').text()
    expect(opcionesTexto).not.toContain('USD')
    expect(opcionesTexto).not.toContain('CZ')
    expect(opcionesTexto).not.toContain('+$')
    expect(opcionesTexto).not.toContain('-$')

    // Ronda 1: elegir ceder reservas (penaliza presupuesto -> bono negativo)
    await wrapper.find('.vn-choice-line').trigger('click')
    // Ronda 2: primera opción (justificar especialistas -> bono positivo)
    await wrapper.find('.vn-choice-line').trigger('click')
    // Ronda 3: tercera opción (arquitectura integral -> bono positivo)
    const opcionesR3 = wrapper.findAll('.vn-choice-line')
    await opcionesR3[opcionesR3.length - 1].trigger('click')

    const emisiones = wrapper.emitted('negotiate') as
      | Array<[{ bono_usd: number; argumento: string; acuerdo_id: string }]>
      | undefined
    expect(emisiones).toBeTruthy()
    expect(emisiones?.length).toBe(3)
    expect(emisiones![0][0].bono_usd).toBeLessThan(0)
    expect(emisiones![1][0].bono_usd).toBeGreaterThan(0)
    expect(emisiones![2][0].bono_usd).toBeGreaterThan(0)

    // Al completar 3 rondas se muestra cierre sin bucle de reinicio infinito
    expect(wrapper.text()).toContain('FIRMAR PRESUPUESTO')
    expect(wrapper.text()).not.toContain('Reiniciar negociación')

    const botonFirmar = wrapper
      .findAll('button')
      .find((b) => b.text().includes('FIRMAR PRESUPUESTO'))
    expect(botonFirmar).toBeTruthy()
    await botonFirmar!.trigger('click')
    expect(wrapper.emitted('finishNegotiation')).toBeTruthy()
  })

  it('DestinationRooms2D ajusta la altura del piso por sala y abre el diálogo RPG de tripulación', async () => {
    const mision = createMissionLocal({
      nombre_mision: 'Zenit Test Salas',
      destino: 'OTB',
      dificultad: 'normal',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'comando',
    })
    mision.etapa_actual = 6
    mision.habitacion_jugador = 'laboratorio'

    const especialistaLab: TripulanteEstado = {
      id: 'crew_elena',
      nombre: 'Dra. Elena Rostova',
      rol: 'Especialista Científica',
      especialidad: 'astrobiologia',
      experiencia: 4,
      salario_usd: 45000,
      estado_animo: 'sol',
      salud: 96,
      salud_mental: 94,
      vivo: true,
      es_jugador: false,
      habitacion_actual: 'laboratorio',
      biografia_corta: 'Investigadora principal de muestras.',
    }
    mision.tripulacion.push(especialistaLab)

    const wrapper = mount(DestinationRooms2D, {
      props: { mission: mision },
    })

    // Verifica el ajuste de piso en laboratorio (1%)
    const escenarioLab = wrapper.find('.scene-box')
    expect(escenarioLab.attributes('style')).toContain('--piso: 1%')

    // Cambia a soporte_vital (1%), sala_sistemas (1%) y cabina_mando (12%)
    mision.habitacion_jugador = 'soporte_vital'
    await wrapper.setProps({ mission: { ...mision } })
    expect(wrapper.find('.scene-box').attributes('style')).toContain('--piso: 1%')

    mision.habitacion_jugador = 'sala_sistemas'
    await wrapper.setProps({ mission: { ...mision } })
    expect(wrapper.find('.scene-box').attributes('style')).toContain('--piso: 1%')

    // Vuelve a laboratorio y abre diálogo RPG con tripulante estático de la sala
    mision.habitacion_jugador = 'laboratorio'
    await wrapper.setProps({ mission: { ...mision } })

    const botonHablar = wrapper.findAll('button').find((b) => b.text().includes('💬'))
    expect(botonHablar).toBeTruthy()
    await botonHablar!.trigger('click')

    expect(wrapper.find('.rpg-dialogue-box').exists()).toBe(true)
    expect(wrapper.text()).toContain('CAPITÁN [TÚ]')
    expect(wrapper.text()).toContain('Pedir diagnóstico de esta sala')

    const botonDiagnostico = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Pedir diagnóstico de esta sala'))
    expect(botonDiagnostico).toBeTruthy()
    await botonDiagnostico!.trigger('click')
    expect(wrapper.find('.rpg-dialogue-box').exists()).toBe(true)

    // Modo solitario cuando no hay tripulantes en cabina_mando
    mision.habitacion_jugador = 'cabina_mando'
    await wrapper.setProps({ mission: { ...mision } })
    expect(wrapper.find('.scene-box').attributes('style')).toContain('--piso: 12%')

    const botonBitacora = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Bitácora de Mando'))
    expect(botonBitacora).toBeTruthy()
    await botonBitacora!.trigger('click')
    expect(wrapper.find('.rpg-dialogue-box').exists()).toBe(true)
  })

  it('BossReportScene cambia de orador entre el Gato Jefe y sus 2 ayudantes', async () => {
    const informe = crearInformePrueba()
    const wrapper = mount(BossReportScene, {
      props: { report: informe },
    })

    expect(wrapper.text()).toContain('Final 1 — Éxito Científico Sobresaliente')
    expect(wrapper.text()).toContain('91 / 100')
    expect(wrapper.text()).toContain(informe.monologo_cuarta_pared!)
    expect(wrapper.find('.tribunal-bg-img').attributes('src')).toBe('/sprites/escenas/escena_final.jpg')

    const btnSalaJuicio = wrapper.findAll('button').find((b) => b.text().includes('Sala de Juicio'))
    expect(btnSalaJuicio).toBeTruthy()
    await btnSalaJuicio!.trigger('click')
    expect(wrapper.find('.tribunal-bg-img').attributes('src')).toBe(
      '/sprites/escenas/sala_juicio_tribunal_wide.jpg',
    )

    const btnFinanzas = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Ayudante 1: Finanzas'))
    expect(btnFinanzas).toBeTruthy()
    await btnFinanzas!.trigger('click')
    expect(wrapper.text()).toContain('AUDITORA BLANCA')
    expect(wrapper.text()).toContain('Cierre presupuestario dentro del margen pactado.')

    const btnCiencia = wrapper
      .findAll('button')
      .find((b) => b.text().includes('Ayudante 2: Ciencia/Tripulación'))
    expect(btnCiencia).toBeTruthy()
    await btnCiencia!.trigger('click')
    expect(wrapper.text()).toContain('ASESOR NEGRO')
    expect(wrapper.text()).toContain('Cobertura completa del paquete experimental.')
  })

  it('ShipSchematic renderiza el corte transversal oficial nave.png', () => {
    const mision = createMissionLocal({
      nombre_mision: 'Zenit Nave Test',
      destino: 'OTB',
      dificultad: 'normal',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'ingenieria',
    })
    const wrapper = mount(ShipSchematic, {
      props: { mission: mision },
    })
    const imgNave = wrapper.find('image[href="/sprites/escenarios/nave/nave.png"]')
    expect(imgNave.exists()).toBe(true)
  })

  it('localSimulationFallback bloquea operaciones antes de etapa 6 y limita negociaciones a 3 rondas', () => {
    const mision = createMissionLocal({
      nombre_mision: 'Zenit Fallback Cap',
      destino: 'LUNA',
      dificultad: 'normal',
      acuerdo_financiacion_id: 'estandar',
      especialidad_director: 'ingenieria',
    })

    // Etapa 1: operaciones en órbita deben quedar bloqueadas
    const opBloqueada = sendDecisionLocal(mision.id, {
      stage: 1,
      decision: 'operacion_cientifica',
      params: {},
    })
    expect(opBloqueada.allowed).toBe(false)
    expect(opBloqueada.status).toBe('fail')

    // Etapa 2: hasta 3 rondas permitidas (incluyendo recortes negativos) y bloqueo en la 4.ª
    const presupuestoAntes = mision.presupuesto_restante_usd
    const r1 = sendDecisionLocal(mision.id, {
      stage: 2,
      decision: 'negociar_presupuesto',
      params: { bono_usd: 25000, argumento: 'Ronda 1', acuerdo_id: 'estandar' },
    })
    expect(r1.allowed).toBe(true)
    expect(r1.mission_state.presupuesto_restante_usd).toBe(presupuestoAntes + 25000)

    const r2 = sendDecisionLocal(mision.id, {
      stage: 2,
      decision: 'negociar_presupuesto',
      params: { bono_usd: -15000, argumento: 'Ronda 2 recorte', acuerdo_id: 'austero' },
    })
    expect(r2.allowed).toBe(true)
    expect(r2.mission_state.presupuesto_restante_usd).toBe(presupuestoAntes + 25000 - 15000)

    const r3 = sendDecisionLocal(mision.id, {
      stage: 2,
      decision: 'negociar_presupuesto',
      params: { bono_usd: 10000, argumento: 'Ronda 3', acuerdo_id: 'estandar' },
    })
    expect(r3.allowed).toBe(true)

    const cuartaRonda = sendDecisionLocal(mision.id, {
      stage: 2,
      decision: 'negociar_presupuesto',
      params: {
        bono_usd: 25000,
        argumento: 'Cuarto intento fuera de límite',
        acuerdo_id: 'estandar',
      },
    })
    expect(cuartaRonda.allowed).toBe(false)
    expect(cuartaRonda.status).toBe('warning')
  })

  it('GameMainMenu muestra portada limpia de videojuego y navega a Nueva Expedición y subvistas', async () => {
    const wrapper = mount(GameMainMenu, {
      props: {
        hasActiveMission: true,
        difficultyOptions: [
          {
            id: 'facil',
            title: 'Modo Cadete (Fácil · Recomendado)',
            badge: '+FÁCIL',
            desc: 'Ideal para aprender sistemas.',
            perks: ['+35% de presupuesto (168.750 CZ)'],
          },
          {
            id: 'normal',
            title: 'Modo Director (Estándar)',
            badge: 'EQUILIBRADO',
            desc: 'Experiencia clásica.',
            perks: ['Presupuesto nominal (125.000 CZ)'],
          },
        ],
      },
    })

    // En la portada inicial debe verse el fondo oficial, logotipo ZENIT y botones principales centrados
    expect(wrapper.find('.menu-bg-art').attributes('src')).toBe(
      '/sprites/escenas/menu_principal_bg.jpg',
    )
    expect(wrapper.find('.zenit-wordmark').text()).toContain('Z')
    expect(wrapper.text()).toContain('Nueva Expedición')
    expect(wrapper.text()).toContain('Cómo Jugar')
    expect(wrapper.text()).toContain('Tripulación y Comité')
    expect(wrapper.text()).toContain('Créditos y Fuentes')

    // Navegar a Cómo Jugar y volver
    const btnHowto = wrapper.findAll('button').find((b) => b.text().includes('Cómo Jugar'))
    expect(btnHowto).toBeTruthy()
    await btnHowto!.trigger('click')
    expect(wrapper.text()).toContain('MANUAL DE VUELO')

    const btnVolver = wrapper.findAll('button').find((b) => b.text().includes('Volver'))
    expect(btnVolver).toBeTruthy()
    await btnVolver!.trigger('click')
    expect(wrapper.text()).toContain('MENÚ PRINCIPAL')

    // Abrir Nueva Expedición, elegir Luna y emitir start
    const btnNueva = wrapper.findAll('button').find((b) => b.text().includes('Nueva Expedición'))
    expect(btnNueva).toBeTruthy()
    await btnNueva!.trigger('click')

    const btnLuna = wrapper.findAll('button').find((b) => b.text().includes('Luna'))
    expect(btnLuna).toBeTruthy()
    await btnLuna!.trigger('click')

    const btnDespegar = wrapper.find('.arcade-btn-launch')
    await btnDespegar.trigger('click')

    const startEmitted = wrapper.emitted('start') as
      | Array<[{ nombre_mision: string; destino: string; dificultad: string }]>
      | undefined
    expect(startEmitted).toBeTruthy()
    expect(startEmitted![0][0].destino).toBe('LUNA')
  })
})
