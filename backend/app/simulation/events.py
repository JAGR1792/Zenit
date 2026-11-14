"""Motor de generación y resolución de eventos no deterministas dependientes del estado."""

from __future__ import annotations

import random
import uuid
from app.repositories.seed import COMPONENTES_CATALOGO
from app.schemas.mission import (
    CategoriaComponente,
    DestinoId,
    EstadoAnimo,
    EstadoMision,
    EventoMision,
    OpcionEvento,
)


def actualizar_estados_animo_aleatorios(
    estado: EstadoMision,
    rng: random.Random | None = None,
) -> list[str]:
    """Actualiza el estado de ánimo de la tripulación (sol, nube, lluvia) según presión y azar.

    Args:
        estado: Estado de la misión.
        rng: Generador aleatorio opcional (para reproducibilidad en tests).

    Returns:
        list[str]: Mensajes de cambio de estado anímico.
    """
    gen = rng or random.Random()
    cambios: list[str] = []
    vivos = [t for t in estado.tripulacion if t.vivo]

    # Presión por aislamiento (ej. misión en solitario o con baja dotación) o déficit de recursos
    presion_aislamiento = (
        0.28 if len(vivos) == 1 else (0.12 if len(vivos) == 2 else 0.05)
    )
    presion_recursos = (
        0.22
        if (estado.balance_potencia_w < 0 or estado.o2_dias_disponibles < 3.0)
        else 0.0
    )
    prob_deterioro = min(0.75, 0.14 + presion_aislamiento + presion_recursos)

    for miembro in vivos:
        if len(vivos) == 1:
            miembro.salud_mental = max(15.0, round(miembro.salud_mental - 14.0, 1))
        roll = gen.random()
        if roll < prob_deterioro:
            if miembro.estado_animo == EstadoAnimo.SOL:
                miembro.estado_animo = EstadoAnimo.NUBE
                cambios.append(
                    f"{miembro.nombre} muestra signos de fatiga (Nube sobre su cabeza)."
                )
            elif miembro.estado_animo == EstadoAnimo.NUBE:
                miembro.estado_animo = EstadoAnimo.LLUVIA
                cambios.append(
                    f"{miembro.nombre} sufre desconcentración severa (Lluvia: menor calidad y mayor tiempo de tarea)."
                )
        elif roll > 0.85 and miembro.estado_animo != EstadoAnimo.SOL:
            miembro.estado_animo = EstadoAnimo.SOL
            cambios.append(f"{miembro.nombre} recupera la concentración óptima (Sol).")

    return cambios


def generar_eventos_contextuales(
    estado: EstadoMision,
    rng: random.Random | None = None,
) -> list[EventoMision]:
    """Genera eventos (anomalías, fallos, obstáculos) según estado + entorno + ánimo + decisiones previas.

    Reglas:
    - Los mensajes de alerta NO cuantifican el fallo para que el jugador interprete su gravedad.
    - Ofrecen la opción de usar una ventana de comunicación y energía para consultar a Tierra.
    - Separan el manejo de costes imprevistos financieros ($) frente a energéticos (Wh) en tránsito y órbita.

    Args:
        estado: Estado actual de la misión.
        rng: Generador aleatorio opcional.

    Returns:
        list[EventoMision]: Nuevos eventos disparados en esta etapa.
    """
    gen = rng or random.Random()
    nuevos_eventos: list[EventoMision] = []
    catalogo = {c.id: c for c in COMPONENTES_CATALOGO}

    contexto = "transito" if estado.etapa_actual == 6 else "orbita_destino"
    if estado.etapa_actual not in (6, 7, 8, 9):
        return nuevos_eventos

    # 1. Evento en Tránsito (Etapa 6): Fuga / Desviación térmica de transferencia
    if estado.etapa_actual == 6:
        prob_base = 0.55 if estado.balance_potencia_w < 50 else 0.38
        if gen.random() < prob_base or not estado.eventos_activos:
            ev_transito = EventoMision(
                id=f"ev_trans_{uuid.uuid4().hex[:6]}",
                titulo="Anomalía en Colector de Transferencia",
                mensaje_alerta=(
                    "Se detecta una fluctuación de presión y deriva térmica en el conducto primario "
                    "durante el crucero. La magnitud de la pérdida no está cuantificada."
                ),
                subsistema_afectado="soporte_vital",
                severidad_visual="advertencia",
                etapa_origen=6,
                contexto="transito",
                diagnostico_detallado=(
                    "Telemetría de Tierra confirma microfuga en sello criogénico por ciclado térmico. "
                    "Aislar con calefactor auxiliar o calibrar con el especialista de ingeniería evita perder oxígeno."
                ),
                impacto_oculto_rendimiento=0.18,
                opciones=[
                    OpcionEvento(
                        id="reparar_local_transito",
                        texto="Enviar tripulación a sellar válvula manualmente (Tarea común / Ingeniería)",
                        tipo_accion="reparacion_tripulacion",
                        costo_energia_wh=140.0,
                        especialidad_ideal="ingenieria",
                    ),
                    OpcionEvento(
                        id="maniobra_termica_energia",
                        texto="Purgar línea y compensar con calefactores de reserva (Gasto de Presupuesto de Energía)",
                        tipo_accion="maniobra_energia",
                        costo_energia_wh=360.0,
                        costo_delta_v_ms=45.0,
                    ),
                    OpcionEvento(
                        id="parche_remoto_tierra",
                        texto="Contratar recalibración urgente de válvulas desde Tierra (Gasto de Presupuesto Financiero)",
                        tipo_accion="soporte_financiero_tierra",
                        costo_presupuesto_usd=4500.0,
                        costo_energia_wh=60.0,
                    ),
                    OpcionEvento(
                        id="consultar_tierra_transito",
                        texto="Transmitir telemetría a Tierra para diagnóstico (Consume 1 ventana comm + Energía)",
                        tipo_accion="consultar_tierra",
                        costo_energia_wh=180.0,
                        consume_ventana_comm=True,
                    ),
                ],
            )
            nuevos_eventos.append(ev_transito)

    # 2. Evento específico de entorno: Robot resbala en terreno lunar helado (Etapa 7/8)
    if (
        estado.etapa_actual in (7, 8)
        and estado.destino == DestinoId.LUNA
        and estado.tiene_robot_autonomo
        and not any(
            "robot" in e.id for e in estado.eventos_activos + estado.historial_eventos
        )
    ):
        ev_robot = EventoMision(
            id=f"ev_robot_{uuid.uuid4().hex[:6]}",
            titulo="Pérdida de Tracción de Unidad Autónoma en Cráter Helado",
            mensaje_alerta=(
                "La unidad autónoma Kibo-R1 reporta deslizamiento sobre regolito lunar helado y bloqueo "
                "en un actuador articular. El grado de obstrucción mecánica se desconoce."
            ),
            subsistema_afectado="robot",
            severidad_visual="advertencia",
            etapa_origen=estado.etapa_actual,
            contexto="orbita_destino",
            diagnostico_detallado=(
                "Análisis cinemático desde Tierra: placa de hielo vitrificado bajo las patas traseras. "
                "Un pulso térmico en los servomotores libera el chasis sin dañar los sensores."
            ),
            impacto_oculto_rendimiento=0.25,
            opciones=[
                OpcionEvento(
                    id="eva_rescate_tripulacion",
                    texto="Intervención manual de tripulante para liberar y reparar actuador",
                    tipo_accion="reparacion_tripulacion",
                    costo_energia_wh=160.0,
                    especialidad_ideal="ingenieria",
                ),
                OpcionEvento(
                    id="sobrecarga_servos_energia",
                    texto="Forzar servomotores y calefactores del robot (Gasto de Presupuesto de Energía)",
                    tipo_accion="maniobra_energia",
                    costo_energia_wh=380.0,
                ),
                OpcionEvento(
                    id="software_traccion_tierra",
                    texto="Comprar rutina de control adaptativo al fabricante (Gasto de Presupuesto Financiero)",
                    tipo_accion="soporte_financiero_tierra",
                    costo_presupuesto_usd=5200.0,
                ),
                OpcionEvento(
                    id="consultar_tierra_robot",
                    texto="Usar ventana de comunicación para pedir telemetría a Tierra (1 ventana + Energía)",
                    tipo_accion="consultar_tierra",
                    costo_energia_wh=190.0,
                    consume_ventana_comm=True,
                ),
            ],
        )
        nuevos_eventos.append(ev_robot)

    # 3. Fallo aleatorio de componente en órbita/destino (reduce rendimiento real respecto al publicado)
    if estado.etapa_actual in (7, 8, 9) and len(nuevos_eventos) == 0:
        # Elegir un componente instalado cuya fiabilidad pueda sufrir degradación
        candidatos_comp = [
            catalogo[cid] for cid in estado.componentes_instalados if cid in catalogo
        ]
        if candidatos_comp:
            comp_afectado = gen.choice(candidatos_comp)
            mapa_sub = {
                CategoriaComponente.MOTOR: "motor",
                CategoriaComponente.ENERGIA: "energia",
                CategoriaComponente.ANTENA: "antena",
                CategoriaComponente.SOPORTE_VITAL: "soporte_vital",
                CategoriaComponente.INSTRUMENTO: "cientifico",
                CategoriaComponente.ROBOT: "robot",
            }
            sub_key = mapa_sub.get(comp_afectado.categoria, "energia")
            # Aplicamos reducción de rendimiento real respecto al valor fijo publicado en catálogo
            estado.rendimiento_subsistemas[sub_key] = round(
                max(0.55, estado.rendimiento_subsistemas.get(sub_key, 1.0) - 0.18), 2
            )
            ev_comp = EventoMision(
                id=f"ev_comp_{uuid.uuid4().hex[:6]}",
                titulo=f"Anomalía en {comp_afectado.nombre}",
                mensaje_alerta=(
                    f"Se detecta una anomalía operativa en '{comp_afectado.nombre}'. "
                    "El rendimiento real ha caído respecto a la ficha técnica publicada (magnitud sin cuantificar)."
                ),
                subsistema_afectado=sub_key,
                severidad_visual="grave"
                if sub_key in ("energia", "soporte_vital")
                else "advertencia",
                etapa_origen=estado.etapa_actual,
                contexto=contexto,
                diagnostico_detallado=(
                    f"Control en Tierra identifica degradación en el bus secundario de {comp_afectado.nombre}. "
                    "Se recomienda puenteo por especialista o reconfiguración remota."
                ),
                impacto_oculto_rendimiento=0.18,
                opciones=[
                    OpcionEvento(
                        id="reparar_componente_crew",
                        texto="Reparar módulo con la tripulación a bordo (Tarea común; mejor con especialista)",
                        tipo_accion="reparacion_tripulacion",
                        costo_energia_wh=150.0,
                        especialidad_ideal=comp_afectado.especialidad_requerida
                        or "ingenieria",
                    ),
                    OpcionEvento(
                        id="compensar_con_bateria",
                        texto="Alimentar circuito redundante de emergencia (Gasto de Presupuesto de Energía)",
                        tipo_accion="maniobra_energia",
                        costo_energia_wh=340.0,
                    ),
                    OpcionEvento(
                        id="asistencia_ingenieria_tierra",
                        texto="Encargar tele-reconfiguración a contratista en Tierra (Gasto de Presupuesto Financiero)",
                        tipo_accion="soporte_financiero_tierra",
                        costo_presupuesto_usd=4800.0,
                    ),
                    OpcionEvento(
                        id="consultar_tierra_comp",
                        texto="Informar del imprevisto a Tierra y pedir retroalimentación (1 ventana comm + Energía)",
                        tipo_accion="consultar_tierra",
                        costo_energia_wh=180.0,
                        consume_ventana_comm=True,
                    ),
                ],
            )
            nuevos_eventos.append(ev_comp)

    # Marcar alertas sin cuantificar en las habitaciones 2D correspondientes
    for ev in nuevos_eventos:
        estado.alertas_no_cuantificadas.append(ev.mensaje_alerta)
        for hab in estado.habitaciones_2d:
            if (
                (
                    ev.subsistema_afectado in ("energia", "motor", "antena", "robot")
                    and hab.id == "sala_sistemas"
                )
                or (
                    ev.subsistema_afectado == "soporte_vital"
                    and hab.id == "soporte_vital"
                )
                or (ev.subsistema_afectado == "cientifico" and hab.id == "laboratorio")
            ):
                hab.alerta_activa = True
                hab.color_alerta = "red" if ev.severidad_visual == "grave" else "orange"
                hab.mensaje_terminal = ev.mensaje_alerta

    return nuevos_eventos
