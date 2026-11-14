import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { obtenerSpriteTripulante } from './components/PixelSprite.vue'
import ShipSchematic from './components/ShipSchematic.vue'
import type { ComponenteCatalogo, EstadoMision } from './services/api'

describe('Esquemático y componentes visuales de Zenit', () => {
  it('asigna siempre sprites de perro a toda la tripulación según su especialidad', () => {
    expect(obtenerSpriteTripulante('comando', true)).toBe('perro_caminar')
    expect(obtenerSpriteTripulante('geologia', false)).toBe('perro_cientifico')
    expect(obtenerSpriteTripulante('astrobiologia', false)).toBe('perro_cientifico')
    expect(obtenerSpriteTripulante('ingenieria', false)).toBe('perro_ingeniero')
    expect(obtenerSpriteTripulante('medicina', false)).toBe('perro_medico')
    expect(obtenerSpriteTripulante('comando', false)).toBe('perro_comunicaciones')
  })

  it('renderiza el esquemático de la nave y el estado de ánimo de la tripulación', () => {
    const misionMock: EstadoMision = {
      id: 'zenit-test',
      nombre_mision: 'Expedición Zenit-1',
      etapa_actual: 3,
      nombre_etapa: '3. Diseño de la nave y selección de personal',
      estado_juego: 'en_curso',
      causa_fallo: null,
      dificultad: 'facil',
      destino: 'OTB',
      acuerdo_financiacion_id: 'estandar',
      presupuesto_inicial_usd: 125000,
      presupuesto_restante_usd: 45500,
      masa_estructura_base_kg: 155,
      masa_lanzamiento_max_kg: 1300,
      masa_seca_kg: 405,
      masa_combustible_kg: 795,
      masa_total_kg: 1200,
      componentes_instalados: ['motor_biprop_estandar', 'inst_espectrometro'],
      rendimiento_subsistemas: { motor: 1, energia: 1, antena: 1, soporte_vital: 1, cientifico: 1, robot: 1 },
      isp_efectivo_s: 320,
      delta_v_inicial_ms: 3408,
      delta_v_disponible_ms: 3408,
      delta_v_requerido_total_ms: 2100,
      perfil_trayectoria: 'estandar',
      ventana_lanzamiento: 'optima',
      dias_transito: 1,
      dias_en_destino: 4,
      dias_transcurridos: 0,
      generacion_w: 550,
      consumo_w: 480,
      balance_potencia_w: 70,
      bateria_capacidad_wh: 2200,
      bateria_actual_wh: 2200,
      autonomia_eclipse_h: 12,
      tripulacion: [
        {
          id: 'crew_director',
          nombre: 'Cmdt. Director',
          rol: 'Director de Misión',
          especialidad: 'comando',
          experiencia: 4,
          salario_usd: 0,
          estado_animo: 'sol',
          salud: 100,
          salud_mental: 100,
          vivo: true,
          es_jugador: true,
          habitacion_actual: 'cabina_mando',
          biografia_corta: 'Director',
        },
      ],
      tiene_robot_autonomo: false,
      o2_dias_disponibles: 16,
      comida_dias_disponibles: 16,
      velocidad_tarea_equipo: 1,
      calidad_tarea_equipo: 1,
      puntos_ciencia_generados: 0,
      calidad_datos_promedio: 100,
      datos_generados_gb: 0,
      datos_transmitidos_gb: 0,
      tasa_transmision_kbps: 2000,
      ventanas_comm_por_dia: 3,
      ventanas_comm_restantes: 12,
      probabilidad_enlace_comm: 0.86,
      habitacion_jugador: 'cabina_mando',
      habitaciones_2d: [],
      eventos_activos: [],
      historial_eventos: [],
      alertas_no_cuantificadas: [],
      banderas_penalizacion_diferida: [],
      ultimos_cambios_variables: [],
      bitacora_decisiones: [],
    }

    const catalogoMock: ComponenteCatalogo[] = [
      {
        id: 'motor_biprop_estandar',
        nombre: 'Tobera Bipropelente Hyper-320',
        categoria: 'motor',
        costo_usd: 28000,
        masa_kg: 80,
        consumo_w: 55,
        generacion_w: 0,
        capacidad_wh: 0,
        isp_s: 320,
        combustible_kg: 795,
        alcance_km: 0,
        tasa_kbps: 0,
        ventanas_dia: 0,
        probabilidad_enlace: 0,
        dias_o2: 0,
        dias_comida: 0,
        puntos_ciencia_base: 0,
        datos_gb_dia: 0,
        especialidad_requerida: null,
        fiabilidad_nominal: 0.94,
        slot_visual: 'tobera_campana',
        descripcion_ficha: 'Motor estándar',
      },
      {
        id: 'inst_espectrometro',
        nombre: 'Espectrómetro de Masas Orbital',
        categoria: 'instrumento',
        costo_usd: 8000,
        masa_kg: 50,
        consumo_w: 120,
        generacion_w: 0,
        capacidad_wh: 0,
        isp_s: 0,
        combustible_kg: 0,
        alcance_km: 0,
        tasa_kbps: 0,
        ventanas_dia: 0,
        probabilidad_enlace: 0,
        dias_o2: 0,
        dias_comida: 0,
        puntos_ciencia_base: 15,
        datos_gb_dia: 2,
        especialidad_requerida: 'geologia',
        fiabilidad_nominal: 0.93,
        slot_visual: 'payload_espectrometro',
        descripcion_ficha: 'Espectrómetro',
      },
    ]

    const wrapper = mount(ShipSchematic, {
      props: {
        mission: misionMock,
        catalog: catalogoMock,
      },
    })

    expect(wrapper.text()).toContain('DISEÑO VISUAL DE LA NAVE Y DOTACIÓN PIXEL ART')
    expect(wrapper.text()).toContain('Cmdt. Director')
    expect(wrapper.text()).toContain('SOL')
  })
})
