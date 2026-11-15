"""Motor de cálculo de consecuencias y propagación de variables interdependientes."""

from __future__ import annotations

import random
from typing import Any
from app.repositories.seed import (
    ACUERDOS_FINANCIACION,
    CANDIDATOS_TRIPULACION,
    COMPONENTES_CATALOGO,
    DESTINOS_CATALOGO,
    NOMBRES_ETAPAS,
)
from app.schemas.mission import (
    CambioVariable,
    CategoriaComponente,
    DestinoId,
    DificultadId,
    EstadoAnimo,
    EstadoMision,
)
from app.simulation.events import (
    actualizar_estados_animo_aleatorios,
    generar_eventos_contextuales,
)
from app.simulation.physics import (
    calcular_rendimiento_tripulacion,
    recalcular_subsistemas_mision,
)


def capturar_instantanea_variables(
    estado: EstadoMision,
) -> dict[str, tuple[str, float, str]]:
    """Captura los valores actuales de las variables clave para calcular la tabla de impacto.

    Args:
        estado: Estado de la misión.

    Returns:
        dict[str, tuple[str, float, str]]: Mapa {clave: (etiqueta, valor, unidad)}.
    """
    catalogo = {c.id: c for c in COMPONENTES_CATALOGO}
    tasa_datos_dia = sum(
        catalogo[cid].datos_gb_dia
        for cid in estado.componentes_instalados
        if cid in catalogo
    )
    datos_visibles = round(estado.datos_generados_gb + tasa_datos_dia, 2)

    return {
        "masa_total_kg": ("Masa total", round(estado.masa_total_kg, 1), "kg"),
        "balance_potencia_w": (
            "Balance de energía",
            round(estado.balance_potencia_w, 1),
            "W",
        ),
        "bateria_actual_wh": (
            "Reserva de batería",
            round(estado.bateria_actual_wh, 1),
            "Wh",
        ),
        "delta_v_disponible_ms": (
            "Delta-v disponible",
            round(estado.delta_v_disponible_ms, 1),
            "m/s",
        ),
        "datos_flujo_gb": ("Volumen/flujo de datos", datos_visibles, "GB"),
        "presupuesto_restante_usd": (
            "Presupuesto restante",
            round(estado.presupuesto_restante_usd, 0),
            "USD",
        ),
        "o2_dias_disponibles": (
            "Autonomía soporte vital",
            round(estado.o2_dias_disponibles, 1),
            "días",
        ),
        "puntos_ciencia_generados": (
            "Potencial/puntos ciencia",
            round(estado.puntos_ciencia_generados, 1),
            "pts",
        ),
    }


def construir_tabla_cambios(
    antes: dict[str, tuple[str, float, str]],
    despues: dict[str, tuple[str, float, str]],
) -> list[CambioVariable]:
    """Construye la tabla explícita de variables afectadas tras una decisión.

    Siempre incluye las 5 variables troncales (masa, energía, delta-v, datos, presupuesto)
    más cualquier otra variable que haya cambiado numéricamente.

    Args:
        antes: Instantánea previa a la decisión.
        despues: Instantánea posterior a la decisión.

    Returns:
        list[CambioVariable]: Lista de variables con valor anterior, nuevo y delta.
    """
    claves_troncales = {
        "masa_total_kg",
        "balance_potencia_w",
        "delta_v_disponible_ms",
        "datos_flujo_gb",
        "presupuesto_restante_usd",
    }
    cambios: list[CambioVariable] = []
    for clave, (etiqueta, val_ant, unidad) in antes.items():
        _, val_nue, _ = despues[clave]
        delta = round(val_nue - val_ant, 2)
        if clave in claves_troncales or abs(delta) > 0.01:
            cambios.append(
                CambioVariable(
                    variable=clave,
                    etiqueta=etiqueta,
                    valor_anterior=val_ant,
                    valor_nuevo=val_nue,
                    delta=delta,
                    unidad=unidad,
                )
            )
    return cambios


def aplicar_decision(
    estado: EstadoMision,
    stage: int,
    decision: str,
    params: dict[str, Any],
) -> tuple[EstadoMision, list[CambioVariable], str]:
    """Aplica una decisión validada al estado de la misión y calcula la tabla de impacto.

    Args:
        estado: Estado actual de la misión.
        stage: Etapa de la decisión.
        decision: Acción ejecutada.
        params: Parámetros de la decisión.

    Returns:
        tuple[EstadoMision, list[CambioVariable], str]:
            (nuevo_estado, tabla_variables_afectadas, resumen_narrativo).
    """
    antes = capturar_instantanea_variables(estado)
    catalogo = {c.id: c for c in COMPONENTES_CATALOGO}
    resumen = "Decisión procesada."

    if decision == "seleccionar_destino":
        estado.destino = DestinoId(params["destino"])
        recalcular_subsistemas_mision(estado)
        resumen = f"Destino fijado en {DESTINOS_CATALOGO[estado.destino].nombre}."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "seleccionar_financiacion":
        acuerdo_id = params["acuerdo_id"]
        acuerdo = next(a for a in ACUERDOS_FINANCIACION if a["id"] == acuerdo_id)
        factor_pres = (
            1.35
            if estado.dificultad == DificultadId.FACIL
            else (0.90 if estado.dificultad == DificultadId.DIFICIL else 1.0)
        )
        nuevo_inicial = round(float(acuerdo["presupuesto_usd"]) * factor_pres, 0)
        gasto_acumulado = (
            estado.presupuesto_inicial_usd - estado.presupuesto_restante_usd
        )
        estado.acuerdo_financiacion_id = acuerdo_id
        estado.presupuesto_inicial_usd = nuevo_inicial
        estado.presupuesto_restante_usd = max(
            0.0, round(nuevo_inicial - gasto_acumulado, 2)
        )
        recalcular_subsistemas_mision(estado)
        resumen = f"Acuerdo '{acuerdo['nombre']}' firmado. Presupuesto global ajustado: {nuevo_inicial:,.0f} USD."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "negociar_presupuesto":
        bono_usd = float(params.get("bono_usd", 0.0))
        argumento = str(params.get("argumento", "Argumento ante el comité"))
        acuerdo_id = str(params.get("acuerdo_id", estado.acuerdo_financiacion_id))
        if acuerdo_id in {a["id"] for a in ACUERDOS_FINANCIACION}:
            estado.acuerdo_financiacion_id = acuerdo_id

        factor_dif = (
            1.20
            if estado.dificultad == DificultadId.FACIL
            else (0.90 if estado.dificultad == DificultadId.DIFICIL else 1.0)
        )
        incremento_real = round(bono_usd * factor_dif, 0)
        estado.presupuesto_inicial_usd = round(
            max(75000.0, estado.presupuesto_inicial_usd + incremento_real), 0
        )
        estado.presupuesto_restante_usd = round(
            max(0.0, estado.presupuesto_restante_usd + incremento_real), 2
        )
        recalcular_subsistemas_mision(estado)
        signo = "+" if incremento_real >= 0 else ""
        resumen = (
            f"Negociación con el Gato Jefe ({argumento}): {signo}{incremento_real:,.0f} USD "
            f"(Presupuesto total aprobado: {estado.presupuesto_inicial_usd:,.0f} USD)."
        )
        estado.bitacora_decisiones.append(resumen)

    elif decision == "instalar_componente":
        comp_id = params["componente_id"]
        comp = catalogo[comp_id]
        # Si es motor, energía, antena o soporte vital, reemplaza al anterior de esa categoría
        if comp.categoria in (
            CategoriaComponente.MOTOR,
            CategoriaComponente.ENERGIA,
            CategoriaComponente.ANTENA,
            CategoriaComponente.SOPORTE_VITAL,
        ):
            a_remover = [
                cid
                for cid in estado.componentes_instalados
                if cid in catalogo and catalogo[cid].categoria == comp.categoria
            ]
            for cid_old in a_remover:
                estado.componentes_instalados.remove(cid_old)
                estado.presupuesto_restante_usd += catalogo[cid_old].costo_usd

        estado.componentes_instalados.append(comp_id)
        estado.presupuesto_restante_usd = round(
            estado.presupuesto_restante_usd - comp.costo_usd, 2
        )
        recalcular_subsistemas_mision(estado)
        resumen = f"Instalado en nave: {comp.nombre} (-{comp.costo_usd:,.0f} USD, +{comp.masa_kg} kg)."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "remover_componente":
        comp_id = params["componente_id"]
        comp = catalogo[comp_id]
        estado.componentes_instalados.remove(comp_id)
        estado.presupuesto_restante_usd = round(
            estado.presupuesto_restante_usd + comp.costo_usd, 2
        )
        recalcular_subsistemas_mision(estado)
        resumen = (
            f"Desinstalado: {comp.nombre} (+{comp.costo_usd:,.0f} USD reembolsados)."
        )
        estado.bitacora_decisiones.append(resumen)

    elif decision == "contratar_tripulante":
        crew_id = params["crew_id"]
        cand = next(c for c in CANDIDATOS_TRIPULACION if c.id == crew_id)
        estado.tripulacion.append(cand.model_copy(deep=True))
        estado.presupuesto_restante_usd = round(
            estado.presupuesto_restante_usd - cand.salario_usd, 2
        )
        recalcular_subsistemas_mision(estado)
        resumen = f"Contratado: {cand.nombre} ({cand.rol}, Salario: -{cand.salario_usd:,.0f} USD)."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "remover_tripulante":
        crew_id = params["crew_id"]
        miembro = next(t for t in estado.tripulacion if t.id == crew_id)
        estado.tripulacion = [t for t in estado.tripulacion if t.id != crew_id]
        estado.presupuesto_restante_usd = round(
            estado.presupuesto_restante_usd + miembro.salario_usd, 2
        )
        recalcular_subsistemas_mision(estado)
        resumen = f"Relevado de la misión: {miembro.nombre} (+{miembro.salario_usd:,.0f} USD)."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "configurar_trayectoria":
        estado.perfil_trayectoria = params.get("perfil_trayectoria", "estandar")
        estado.ventana_lanzamiento = params.get("ventana_lanzamiento", "optima")
        recalcular_subsistemas_mision(estado)
        if estado.perfil_trayectoria == "estandar" and estado.destino == DestinoId.LUNA:
            if (
                "trayectoria_lenta_consumo_eclss"
                not in estado.banderas_penalizacion_diferida
            ):
                estado.banderas_penalizacion_diferida.append(
                    "trayectoria_lenta_consumo_eclss"
                )
        resumen = (
            f"Trayectoria '{estado.perfil_trayectoria}' en ventana '{estado.ventana_lanzamiento}' fijada. "
            f"Delta-v requerido estimado: {estado.delta_v_requerido_total_ms} m/s."
        )
        estado.bitacora_decisiones.append(resumen)

    elif decision == "mover_habitacion":
        destino_hab = params.get("habitacion_id", "cabina_mando")
        hab_validas = {h.id for h in estado.habitaciones_2d}
        if destino_hab in hab_validas:
            estado.habitacion_jugador = destino_hab
            for t in estado.tripulacion:
                if t.es_jugador:
                    t.habitacion_actual = destino_hab
            nombre_hab = next(
                h.nombre for h in estado.habitaciones_2d if h.id == destino_hab
            )
            resumen = f"[Tecla E] Compuerta abierta. Te has desplazado a: {nombre_hab}."

    elif decision == "operacion_cientifica":
        # Etapa 7+: Ejecutar campaña científica con los instrumentos instalados (o sensores base si no compró extras)
        instrumentos = [
            catalogo[cid]
            for cid in estado.componentes_instalados
            if cid in catalogo
            and catalogo[cid].categoria
            in (CategoriaComponente.INSTRUMENTO, CategoriaComponente.ROBOT)
        ]
        if not instrumentos:
            # Sensores orbitales base integrados en el laboratorio para que el jugador nunca quede bloqueado con 0 GB
            _, cal_base = calcular_rendimiento_tripulacion(
                estado.tripulacion,
                especialidad_requerida=None,
                es_tarea_comun=True,
            )
            rend_sub = estado.rendimiento_subsistemas.get("cientifico", 1.0)
            puntos_totales = round(14.0 * cal_base * rend_sub, 1)
            datos_totales = round(2.4 * rend_sub, 2)
            energia_consumida = 90.0
            estado.puntos_ciencia_generados = round(
                estado.puntos_ciencia_generados + puntos_totales, 1
            )
            estado.datos_generados_gb = round(
                estado.datos_generados_gb + datos_totales, 2
            )
            estado.bateria_actual_wh = round(
                max(0.0, estado.bateria_actual_wh - energia_consumida), 1
            )
            estado.calidad_datos_promedio = round(
                min(100.0, estado.calidad_tarea_equipo * 88.0), 1
            )
            resumen = (
                f"Campaña ejecutada con Sensores Base del Laboratorio: +{puntos_totales:.1f} pts de ciencia, "
                f"+{datos_totales:.2f} GB en memoria (-{energia_consumida:.0f} Wh). "
                "Ahora puedes transmitirlos a Tierra con la antena."
            )
            estado.bitacora_decisiones.append(resumen)
        else:
            puntos_totales = 0.0
            datos_totales = 0.0
            energia_consumida = 0.0
            for inst in instrumentos:
                _, cal_esp = calcular_rendimiento_tripulacion(
                    estado.tripulacion,
                    especialidad_requerida=inst.especialidad_requerida,
                    es_tarea_comun=False,
                )
                rend_sub = estado.rendimiento_subsistemas.get(
                    "robot"
                    if inst.categoria == CategoriaComponente.ROBOT
                    else "cientifico",
                    1.0,
                )
                pts = round(inst.puntos_ciencia_base * cal_esp * rend_sub, 1)
                gb = round(
                    inst.datos_gb_dia * max(1, estado.dias_en_destino // 2) * rend_sub,
                    2,
                )
                puntos_totales += pts
                datos_totales += gb
                energia_consumida += inst.consumo_w * 1.2

            estado.puntos_ciencia_generados = round(
                estado.puntos_ciencia_generados + puntos_totales, 1
            )
            estado.datos_generados_gb = round(
                estado.datos_generados_gb + datos_totales, 2
            )
            estado.bateria_actual_wh = round(
                max(0.0, estado.bateria_actual_wh - energia_consumida), 1
            )
            estado.calidad_datos_promedio = round(
                min(100.0, estado.calidad_tarea_equipo * 92.0), 1
            )
            if estado.datos_generados_gb > (estado.ventanas_comm_restantes * 3.0):
                if (
                    "exceso_datos_cuello_botella"
                    not in estado.banderas_penalizacion_diferida
                ):
                    estado.banderas_penalizacion_diferida.append(
                        "exceso_datos_cuello_botella"
                    )
            resumen = (
                f"Operación en Laboratorio completada: +{puntos_totales:.1f} pts de ciencia, "
                f"+{datos_totales:.1f} GB de datos almacenados (-{energia_consumida:.0f} Wh). "
                "¡Listos para transmitir a Tierra!"
            )
            estado.bitacora_decisiones.append(resumen)

    elif decision == "tarea_tripulacion":
        # Etapa 8: Operaciones de tripulación (mantenimiento común, estabilización de ánimo, reciclaje)
        subtipo = params.get("subtipo", "mantenimiento_general")
        vel, cal = calcular_rendimiento_tripulacion(
            estado.tripulacion,
            especialidad_requerida="ingenieria"
            if subtipo == "mantenimiento_general"
            else "medicina",
            es_tarea_comun=True,
        )
        if subtipo == "mantenimiento_general":
            for k in estado.rendimiento_subsistemas:
                estado.rendimiento_subsistemas[k] = round(
                    min(1.0, estado.rendimiento_subsistemas[k] + 0.12 * cal), 2
                )
            estado.bateria_actual_wh = round(
                max(0.0, estado.bateria_actual_wh - 110.0), 1
            )
            recalcular_subsistemas_mision(estado)
            resumen = (
                f"Mantenimiento preventivo ejecutado (Velocidad equipo: {vel}x, Calidad: {cal}x). "
                "Subsistemas recalibrados."
            )
        else:
            # Apoyo psicológico y racionamiento en Módulo de Vida
            for miembro in estado.tripulacion:
                if miembro.vivo:
                    miembro.estado_animo = EstadoAnimo.SOL
                    miembro.salud_mental = min(
                        100.0, round(miembro.salud_mental + 18.0 * cal, 1)
                    )
            recalcular_subsistemas_mision(estado)
            resumen = "Sesión de estabilización y descanso en Módulo de Vida: la tripulación recupera estado Sol."
        estado.bitacora_decisiones.append(resumen)

    elif decision == "usar_ventana_comm":
        # Etapa 7 a 9: Transmitir datos científicos a Tierra
        pendientes = round(
            max(0.0, estado.datos_generados_gb - estado.datos_transmitidos_gb), 2
        )
        if estado.datos_generados_gb <= 0:
            resumen = (
                "Aún no tienes datos científicos en memoria (0 GB). "
                "Paso 1: Pulsa '🔬 Recolectar Datos en Laboratorio' (o usa [E] en el Laboratorio) antes de transmitir."
            )
        elif pendientes <= 0:
            resumen = (
                f"¡Todos los datos en memoria ({estado.datos_transmitidos_gb} GB) ya fueron transmitidos a Tierra! "
                "No se consumió ninguna ventana adicional."
            )
        elif estado.ventanas_comm_restantes <= 0:
            resumen = (
                "No quedan ventanas de comunicación disponibles en esta órbita/ciclo."
            )
        elif estado.bateria_actual_wh < 80.0:
            resumen = "Energía en baterías insuficiente para alimentar el amplificador de transmisión."
        else:
            estado.ventanas_comm_restantes -= 1
            estado.bateria_actual_wh = round(
                max(0.0, estado.bateria_actual_wh - 100.0), 1
            )
            # Capacidad por ventana calibrada para transmitir de forma clara y fluida
            gb_por_ventana = max(
                2.5,
                round(
                    (estado.tasa_transmision_kbps / 1000.0)
                    * estado.probabilidad_enlace_comm
                    * 2.2,
                    2,
                ),
            )
            transmitido_ahora = round(min(pendientes, gb_por_ventana), 2)
            estado.datos_transmitidos_gb = round(
                estado.datos_transmitidos_gb + transmitido_ahora, 2
            )
            resumen = (
                f"📡 Transmisión exitosa a Tierra: +{transmitido_ahora} GB enviados "
                f"(Total transmitido: {estado.datos_transmitidos_gb} / {estado.datos_generados_gb} GB · "
                f"Quedan {estado.ventanas_comm_restantes} ventanas)."
            )
            estado.bitacora_decisiones.append(resumen)

    despues = capturar_instantanea_variables(estado)
    cambios = construir_tabla_cambios(antes, despues)
    estado.ultimos_cambios_variables = cambios
    return estado, cambios, resumen


def resolver_evento_activo(
    estado: EstadoMision,
    event_id: str,
    option_id: str,
) -> tuple[EstadoMision, list[CambioVariable], str]:
    """Resuelve o diagnostica un evento activo aplicando sus costes financieros, energéticos o de ventana.

    Args:
        estado: Estado de la misión.
        event_id: ID del evento activo.
        option_id: ID de la opción elegida por el jugador.

    Returns:
        tuple[EstadoMision, list[CambioVariable], str]: (estado, cambios_variables, mensaje_resultado).
    """
    antes = capturar_instantanea_variables(estado)
    evento = next((e for e in estado.eventos_activos if e.id == event_id), None)
    if not evento:
        return estado, [], "Evento no encontrado."

    opcion = next((o for o in evento.opciones if o.id == option_id), evento.opciones[0])

    # Verificar límite duro de presupuesto financiero si la opción cuesta dinero
    if (
        opcion.costo_presupuesto_usd > 0
        and estado.presupuesto_restante_usd < opcion.costo_presupuesto_usd
    ):
        return (
            estado,
            [],
            f"Acción denegada: el coste imprevisto ({opcion.costo_presupuesto_usd:,.0f} USD) supera el presupuesto restante.",
        )

    # Descontar costes en tiempo real (separando presupuesto financiero de energía)
    estado.presupuesto_restante_usd = round(
        max(0.0, estado.presupuesto_restante_usd - opcion.costo_presupuesto_usd), 2
    )
    estado.bateria_actual_wh = round(
        max(0.0, estado.bateria_actual_wh - opcion.costo_energia_wh), 1
    )
    estado.delta_v_disponible_ms = round(
        max(0.0, estado.delta_v_disponible_ms - opcion.costo_delta_v_ms), 1
    )

    if opcion.consume_ventana_comm:
        estado.ventanas_comm_restantes = max(0, estado.ventanas_comm_restantes - 1)

    # Caso especial: Consultar a Tierra consume 1 ventana + energía y revela el diagnóstico, pero no repara gratis
    if opcion.tipo_accion == "consultar_tierra":
        evento.diagnosticado_por_tierra = True
        narr = (
            f"Telemetría enviada a Tierra (-1 ventana de comunicación, -{opcion.costo_energia_wh:.0f} Wh). "
            f"Diagnóstico recibido: {evento.diagnostico_detallado}"
        )
        evento.resultado_narrativo = narr
        estado.bitacora_decisiones.append(narr)
        despues = capturar_instantanea_variables(estado)
        cambios = construir_tabla_cambios(antes, despues)
        estado.ultimos_cambios_variables = cambios
        return estado, cambios, narr

    # Resolver el evento según el tipo de acción
    vel, cal = calcular_rendimiento_tripulacion(
        estado.tripulacion,
        especialidad_requerida=opcion.especialidad_ideal,
        es_tarea_comun=True,
    )
    sub = evento.subsistema_afectado
    if sub in estado.rendimiento_subsistemas:
        recuperacion = (
            0.20 * cal if opcion.tipo_accion == "reparacion_tripulacion" else 0.18
        )
        estado.rendimiento_subsistemas[sub] = round(
            min(1.0, estado.rendimiento_subsistemas[sub] + recuperacion), 2
        )

    evento.resuelto = True
    evento.resultado_narrativo = (
        f"Resuelto mediante '{opcion.texto}'. "
        f"Rendimiento de equipo aplicado: {vel}x velocidad, {cal}x calidad."
    )
    estado.eventos_activos = [e for e in estado.eventos_activos if e.id != event_id]
    estado.historial_eventos.append(evento)

    # Limpiar alerta de la habitación 2D si ya no quedan eventos en ese subsistema
    for hab in estado.habitaciones_2d:
        hab.alerta_activa = False
        hab.color_alerta = "cyan"

    recalcular_subsistemas_mision(estado)
    estado.bitacora_decisiones.append(evento.resultado_narrativo)
    despues = capturar_instantanea_variables(estado)
    cambios = construir_tabla_cambios(antes, despues)
    estado.ultimos_cambios_variables = cambios
    return estado, cambios, evento.resultado_narrativo


def avanzar_etapa_mision(
    estado: EstadoMision,
    rng: random.Random | None = None,
) -> tuple[EstadoMision, list[CambioVariable], str]:
    """Ejecuta la simulación al avanzar de la etapa actual a la siguiente (1 -> 10).

    Args:
        estado: Estado actual de la misión.
        rng: Generador aleatorio opcional.

    Returns:
        tuple[EstadoMision, list[CambioVariable], str]:
            (estado_actualizado, tabla_variables_afectadas, narrativa_transicion).
    """
    antes = capturar_instantanea_variables(estado)
    params_destino = DESTINOS_CATALOGO[estado.destino]
    narrativa = ""

    # Si estamos en Etapa 5 (Lanzamiento), verificar límites físicos críticos
    if estado.etapa_actual == 5:
        if estado.masa_total_kg > estado.masa_lanzamiento_max_kg:
            estado.estado_juego = "fallo_inmediato"
            estado.causa_fallo = (
                f"Sobrecarga estructural: masa de nave ({estado.masa_total_kg} kg) superó "
                f"masa máxima de lanzamiento ({estado.masa_lanzamiento_max_kg} kg)."
            )
            estado.etapa_actual = 10
            estado.nombre_etapa = NOMBRES_ETAPAS[10]
            despues = capturar_instantanea_variables(estado)
            return estado, construir_tabla_cambios(antes, despues), estado.causa_fallo

        if estado.delta_v_disponible_ms < params_destino.delta_v_lanzamiento_ms:
            estado.estado_juego = "fallo_inmediato"
            estado.causa_fallo = (
                f"Empuje/Impulso insuficiente en ascenso: {estado.delta_v_disponible_ms} m/s disponibles "
                f"frente a {params_destino.delta_v_lanzamiento_ms} m/s requeridos."
            )
            estado.etapa_actual = 10
            estado.nombre_etapa = NOMBRES_ETAPAS[10]
            despues = capturar_instantanea_variables(estado)
            return estado, construir_tabla_cambios(antes, despues), estado.causa_fallo

        # Descontar delta-v de lanzamiento e inserción inicial
        estado.delta_v_disponible_ms = round(
            estado.delta_v_disponible_ms - params_destino.delta_v_lanzamiento_ms, 1
        )
        narrativa = f"Ascenso orbital completado. Se consumieron {params_destino.delta_v_lanzamiento_ms:.0f} m/s de Delta-v."

    elif estado.etapa_actual == 6:
        # Tránsito hacia el destino
        dv_transito = round(
            params_destino.delta_v_transito_insercion_ms
            * (1.18 if estado.perfil_trayectoria == "rapida" else 1.0),
            1,
        )
        if estado.delta_v_disponible_ms < dv_transito:
            estado.estado_juego = "perdida_mision"
            estado.causa_fallo = f"Delta-v agotado en maniobra de inyección ({estado.delta_v_disponible_ms} m/s < {dv_transito} m/s)."
            estado.etapa_actual = 10
            estado.nombre_etapa = NOMBRES_ETAPAS[10]
            despues = capturar_instantanea_variables(estado)
            return estado, construir_tabla_cambios(antes, despues), estado.causa_fallo

        estado.delta_v_disponible_ms = round(
            estado.delta_v_disponible_ms - dv_transito, 1
        )
        estado.dias_transcurridos += estado.dias_transito
        estado.o2_dias_disponibles = round(
            max(0.0, estado.o2_dias_disponibles - estado.dias_transito), 1
        )
        estado.comida_dias_disponibles = round(
            max(0.0, estado.comida_dias_disponibles - estado.dias_transito), 1
        )
        # Coste operativo en tiempo real durante el tránsito (reducido en modo Fácil)
        tarifa_dia_transito = (
            600.0 if estado.dificultad == DificultadId.FACIL else 1100.0
        )
        costo_ops_transito = estado.dias_transito * tarifa_dia_transito
        estado.presupuesto_restante_usd = round(
            max(0.0, estado.presupuesto_restante_usd - costo_ops_transito), 2
        )
        narrativa = (
            f"Tránsito a {estado.destino.value} completado en {estado.dias_transito} día(s). "
            f"Coste de seguimiento en tiempo real: -{costo_ops_transito:,.0f} USD."
        )

    elif estado.etapa_actual in (7, 8, 9):
        # Coste diario operativo y degradación progresiva si faltan recursos operativos
        estado.dias_transcurridos += 1
        consumo_diario_vital = 0.7 if estado.dificultad == DificultadId.FACIL else 1.0
        estado.o2_dias_disponibles = round(
            max(0.0, estado.o2_dias_disponibles - consumo_diario_vital), 1
        )
        estado.comida_dias_disponibles = round(
            max(0.0, estado.comida_dias_disponibles - consumo_diario_vital), 1
        )
        costo_diario_ops = 450.0 if estado.dificultad == DificultadId.FACIL else 850.0
        estado.presupuesto_restante_usd = round(
            max(0.0, estado.presupuesto_restante_usd - costo_diario_ops), 2
        )

        if estado.balance_potencia_w < 0:
            deficit_wh = abs(estado.balance_potencia_w) * 4.0
            estado.bateria_actual_wh = round(
                max(0.0, estado.bateria_actual_wh - deficit_wh), 1
            )

        # Degradación progresiva si se agota batería o soporte vital
        if (
            estado.bateria_actual_wh <= 0
            or estado.o2_dias_disponibles <= 0
            or estado.comida_dias_disponibles <= 0
        ):
            for miembro in estado.tripulacion:
                if miembro.vivo:
                    miembro.salud = round(max(0.0, miembro.salud - 38.0), 1)
                    miembro.estado_animo = EstadoAnimo.LLUVIA
                    if miembro.salud <= 0:
                        miembro.vivo = False

    # Avanzar índice de etapa
    if estado.etapa_actual < 10:
        estado.etapa_actual += 1
        estado.nombre_etapa = NOMBRES_ETAPAS[estado.etapa_actual]
        if estado.etapa_actual == 10:
            # Verificar maniobra de retorno
            dv_retorno = params_destino.delta_v_retorno_ms
            if estado.delta_v_disponible_ms >= dv_retorno:
                estado.delta_v_disponible_ms = round(
                    estado.delta_v_disponible_ms - dv_retorno, 1
                )
                estado.estado_juego = "completada"
                narrativa = "Maniobra de retorno completada. Entrando al despacho del Director para la evaluación final."
            else:
                estado.estado_juego = "completada"
                if "sin_deltav_retorno" not in estado.banderas_penalizacion_diferida:
                    estado.banderas_penalizacion_diferida.append("sin_deltav_retorno")
                narrativa = (
                    f"ALERTA CRÍTICA DE RETORNO: Delta-v restante ({estado.delta_v_disponible_ms} m/s) "
                    f"insuficiente para el retorno nominal ({dv_retorno} m/s). Se procede a evaluación de emergencia."
                )

    # Actualizar ánimo aleatorio y generar eventos contextuales en etapas operativas
    if estado.etapa_actual in (6, 7, 8, 9):
        actualizar_estados_animo_aleatorios(estado, rng=rng)
        nuevos = generar_eventos_contextuales(estado, rng=rng)
        estado.eventos_activos.extend(nuevos)

    recalcular_subsistemas_mision(estado)
    if not narrativa:
        narrativa = f"Avanzando a {estado.nombre_etapa}."
    estado.bitacora_decisiones.append(narrativa)

    despues = capturar_instantanea_variables(estado)
    cambios = construir_tabla_cambios(antes, despues)
    estado.ultimos_cambios_variables = cambios
    return estado, cambios, narrativa
