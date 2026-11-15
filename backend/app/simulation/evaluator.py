"""Motor de evaluación multidimensional, selección de finales ramificados e informe del Gato Jefe."""

from __future__ import annotations

from app.repositories.seed import ACUERDOS_FINANCIACION, DESTINOS_CATALOGO
from app.schemas.mission import DimensionEvaluacion, EstadoMision, InformeFinal


def generar_informe_final(estado: EstadoMision) -> InformeFinal:
    """Calcula las 7 dimensiones de evaluación, determina el final ramificado (1 a 5) y construye la escena del Gato Jefe.

    Adapta todos los diálogos según:
    - Si el jugador voló en solitario (sin contratar tripulación) o con especialistas a bordo.
    - El destino elegido (OTB vs Cráter Lunar Shackleton).
    - Si recolectó datos en el Laboratorio y si logró transmitirlos por la antena.

    Args:
        estado: Estado final de la misión.

    Returns:
        InformeFinal: Estructura completa con diálogo del Gato Jefe, monólogo de cuarta pared y reporte técnico.
    """
    acuerdo = next(
        (a for a in ACUERDOS_FINANCIACION if a["id"] == estado.acuerdo_financiacion_id),
        ACUERDOS_FINANCIACION[1],
    )
    meta_ciencia = float(acuerdo["exigencia_ciencia"])
    params_destino = DESTINOS_CATALOGO[estado.destino]
    nombre_destino_corto = (
        "la Órbita Terrestre Baja (OTB)"
        if estado.destino.value == "OTB"
        else "el Cráter Lunar Shackleton"
    )

    vivos = [t for t in estado.tripulacion if t.vivo]
    total_crew = max(1, len(estado.tripulacion))
    especialistas = [t for t in estado.tripulacion if not t.es_jugador]
    fue_en_solitario = len(especialistas) == 0
    nombres_especialistas = ", ".join(t.nombre for t in especialistas)

    # Ineficiencias de diseño (para coherencia y finales ramificados)
    from app.repositories.seed import COMPONENTES_CATALOGO

    catalogo = {c.id: c for c in COMPONENTES_CATALOGO}
    motor_id = None
    tiene_robot = getattr(estado, "tiene_robot_autonomo", False)
    for cid in estado.componentes_instalados:
        comp = catalogo.get(cid)
        if comp and comp.categoria == "motor":
            motor_id = cid
    instrumentos_instalados = [
        catalogo[cid]
        for cid in estado.componentes_instalados
        if catalogo.get(cid) and catalogo[cid].categoria in ("instrumento", "robot")
    ]
    especialidades_trip = {t.especialidad for t in estado.tripulacion}
    instrumento_sin_especialista = any(
        c.especialidad_requerida and c.especialidad_requerida not in especialidades_trip
        for c in instrumentos_instalados
    )
    motor_excesivo = (
        estado.destino.value == "OTB" and motor_id == "motor_crio_avanzado"
    ) or (
        estado.destino.value == "OTB" and motor_id == "motor_biprop_estandar"
        and estado.delta_v_requerido_total_ms < 2200
    )
    robot_sin_uso = tiene_robot and estado.datos_generados_gb <= 0.2
    ineficiente = motor_excesivo or instrumento_sin_especialista or robot_sin_uso

    sin_retorno = "sin_deltav_retorno" in estado.banderas_penalizacion_diferida
    fallo_temprano = estado.estado_juego in ("fallo_inmediato", "perdida_mision")
    hubo_bajas = (len(vivos) < total_crew) or sin_retorno or fallo_temprano

    # 1. Dimensión Científica
    score_ciencia = (
        0.0
        if fallo_temprano
        else round(
            min(
                100.0,
                (estado.puntos_ciencia_generados / max(10.0, meta_ciencia)) * 100.0,
            ),
            1,
        )
    )

    # 2. Dimensión Transmisión y Calidad de Datos
    ratio_tx = (
        0.0
        if estado.datos_generados_gb <= 0
        else min(1.0, estado.datos_transmitidos_gb / estado.datos_generados_gb)
    )
    score_datos = round(ratio_tx * (estado.calidad_datos_promedio / 100.0) * 100.0, 1)

    # 3. Dimensión Supervivencia y Salud de Tripulación (penaliza aislamiento si fue en solitario)
    if fallo_temprano or len(vivos) == 0:
        score_supervivencia = 0.0
    elif sin_retorno:
        score_supervivencia = 20.0
    else:
        salud_media = sum((t.salud + t.salud_mental) / 2.0 for t in vivos) / total_crew
        penalizacion_solitario = 0.85 if fue_en_solitario else 1.0
        score_supervivencia = round(
            (len(vivos) / total_crew) * salud_media * penalizacion_solitario, 1
        )

    # 4. Dimensión Presupuesto Global
    ratio_presupuesto = max(
        0.0, estado.presupuesto_restante_usd / max(1.0, estado.presupuesto_inicial_usd)
    )
    score_presupuesto = round(min(100.0, 45.0 + ratio_presupuesto * 110.0), 1)

    # 5. Dimensión Tiempo y Ventana Orbital
    dias_nominales = (
        params_destino.dias_transito_estandar + params_destino.dias_operacion_destino
    )
    desviacion_dias = max(0, estado.dias_transcurridos - dias_nominales)
    score_tiempo = (
        0.0 if fallo_temprano else round(max(25.0, 100.0 - desviacion_dias * 12.0), 1)
    )

    # 6. Dimensión Estado Final de la Nave
    integridad_media = sum(estado.rendimiento_subsistemas.values()) / max(
        1, len(estado.rendimiento_subsistemas)
    )
    score_nave = 0.0 if fallo_temprano else round(integridad_media * 100.0, 1)

    # 7. Dimensión Capacidad de Retorno
    if fallo_temprano or sin_retorno:
        score_retorno = 0.0
    else:
        score_retorno = round(
            min(100.0, 65.0 + (estado.delta_v_disponible_ms / 400.0) * 35.0), 1
        )

    puntuacion_global = round(
        (
            score_ciencia * 0.20
            + score_datos * 0.20
            + score_supervivencia * 0.25
            + score_presupuesto * 0.10
            + score_tiempo * 0.05
            + score_nave * 0.10
            + score_retorno * 0.10
        ),
        1,
    )

    # Diagnóstico narrativo específico sobre la ciencia y los datos
    if estado.datos_generados_gb <= 0:
        diagnostico_ciencia_narrativo = (
            "Llegaste hasta la órbita de destino, pero no activaste ni una sola vez el Laboratorio Científico "
            "(0 GB recolectados)."
        )
    elif estado.datos_transmitidos_gb <= 0:
        diagnostico_ciencia_narrativo = (
            f"Recolectaste {estado.datos_generados_gb:.1f} GB de datos valiosos en el Laboratorio, pero olvidaste "
            "transmitirlos por la antena en la Sala de Sistemas antes de emprender el regreso (0 GB recibidos en Tierra)."
        )
    elif estado.datos_transmitidos_gb < estado.datos_generados_gb:
        diagnostico_ciencia_narrativo = (
            f"Lograste enviar {estado.datos_transmitidos_gb:.1f} GB de los {estado.datos_generados_gb:.1f} GB recolectados, "
            "dejando parte de los descubrimientos sin transmitir por falta de ventanas o ancho de banda."
        )
    else:
        diagnostico_ciencia_narrativo = (
            f"Transmitiste íntegramente los {estado.datos_transmitidos_gb:.1f} GB de telemetría científica a nuestras estaciones."
        )

    # Selección de uno de los 5 finales ramificados con diálogos reactivos (Solitario vs Con Tripulación)
    if fallo_temprano or (hubo_bajas and estado.datos_transmitidos_gb <= 0.2):
        final_id = "fallo_total"
        numero_final = 5
        titulo_final = "Final 5 — Fallo Total de la Misión"
        subtitulo_final = "Pérdida del vehículo espacial y ausencia de retorno científico."
        if fue_en_solitario:
            dialogo_apertura = (
                "El despacho del Comisionado Félix Vance (El Gato Jefe) está en penumbra. Sobre su escritorio de acero "
                "reposa tu expediente de vuelo en solitario con el sello de siniestro total: "
                f"«Quisiste hacerlo todo tú solo rumbo a {nombre_destino_corto}, sin especialistas a bordo. "
                f"{estado.causa_fallo or 'El vehículo no resistió la misión.'}»"
            )
        else:
            dialogo_apertura = (
                "El despacho del Comisionado Félix Vance (El Gato Jefe) está en penumbra. Sobre el escritorio de acero "
                f"reposan las fichas de {nombres_especialistas}. El Jefe te mira en silencio: "
                f"«{estado.causa_fallo or 'Perdimos la nave y la expedición por completo.'}»"
            )
        frase_despedida = (
            "«La física orbital no negocia con la improvisación, Director. Cada kilogramo de masa y cada metro por segundo "
            "de Delta-v deciden quién vuelve a casa.»"
        )
    elif hubo_bajas and estado.datos_transmitidos_gb > 0.2:
        final_id = "perdida_tripulacion_datos_recuperados"
        numero_final = 4
        titulo_final = "Final 4 — Pérdida Humana, Datos Recuperados"
        subtitulo_final = "La ciencia llegó por antena a la Tierra, pero la nave no logró regresar a salvo."
        if fue_en_solitario:
            dialogo_apertura = (
                "En las pantallas del Comisionado Félix Vance brillan los paquetes de telemetría que alcanzaste a transmitir "
                f"desde {nombre_destino_corto} antes de que se agotaran tus reservas de retorno en solitario."
            )
        else:
            dialogo_apertura = (
                f"Las antenas de Tierra recibieron los {estado.datos_transmitidos_gb:.1f} GB enviados por tu equipo "
                f"({nombres_especialistas}), pero las sillas frente al escritorio del Gato Jefe están vacías."
            )
        frase_despedida = (
            "«Nuestros servidores tienen los datos de la anomalía Helios-9, pero el precio que pagamos en esa órbita "
            "jamás podrá justificarse en un balance contable.»"
        )
    elif (
        score_nave < 72.0
        or score_supervivencia < 65.0
        or estado.bateria_actual_wh < 180.0
    ):
        final_id = "retorno_emergencia"
        numero_final = 3
        titulo_final = "Final 3 — Retorno de Emergencia"
        subtitulo_final = (
            "Sobrevivencia al límite operativo con reservas críticas y sistemas desgastados."
        )
        if fue_en_solitario:
            dialogo_apertura = (
                "El Comisionado Félix Vance apoya las garras sobre la mesa iluminada con luz ámbar: "
                f"«Regresaste vivo de {nombre_destino_corto} por puro milagro, Director. Te lanzaste completamente solo, "
                "sin contratar a un solo especialista en la Etapa 3; el aislamiento te pasó factura y la cápsula aterrizó "
                f"con las baterías y el soporte vital al límite. {diagnostico_ciencia_narrativo}»"
            )
        else:
            dialogo_apertura = (
                "El Comisionado Félix Vance apoya las garras sobre la mesa iluminada con luz ámbar: "
                f"«Trajiste de vuelta a {nombres_especialistas} por los pelos, Director. La nave aterrizó con los sistemas "
                f"al límite tras el viaje a {nombre_destino_corto}. {diagnostico_ciencia_narrativo}»"
            )
        frase_despedida = (
            "«Sobrevivir a un vuelo al límite enseña más que diez simulaciones en tierra. "
            "Para la próxima misión, equilibra mejor tu dotación y tus reservas de energía.»"
        )
    elif score_ciencia >= 70.0 and score_datos >= 65.0 and not ineficiente:
        final_id = "exito_cientifico_pleno"
        numero_final = 1
        titulo_final = "Final 1 — Éxito Científico Pleno"
        subtitulo_final = (
            "Misión histórica: objetivos científicos cumplidos, datos transmitidos y retorno íntegro."
        )
        if fue_en_solitario:
            dialogo_apertura = (
                "El Comisionado Félix Vance se levanta de su sillón y aplaude con asombro mientras revisa tu telemetría: "
                f"«Increíble, Director. Volaste completamente en solitario hasta {nombre_destino_corto}, operaste tú mismo "
                "el Laboratorio y la Antena sin apoyo de especialistas, y aun así cumpliste la meta científica y regresaste "
                f"con la nave intacta. {diagnostico_ciencia_narrativo}»"
            )
        else:
            dialogo_apertura = (
                "El Comisionado Félix Vance se levanta al verte entrar junto a tu equipo y extiende el informe dorado: "
                f"«Un trabajo de dirección impecable en {nombre_destino_corto}. Coordinaste a {nombres_especialistas}, "
                "equilibraste masa, Delta-v, energía y ancho de banda, y trajiste a todo tu equipo sano y salvo. "
                f"{diagnostico_ciencia_narrativo}»"
            )
        frase_despedida = (
            "«Así se escribe la historia aeroespacial del Programa Zenit: leyendo cada ficha técnica y ejecutando "
            "cada ventana de transmisión con precisión quirúrgica. Enhorabuena, Director.»"
        )
    elif score_ciencia >= 70.0 and score_datos >= 65.0 and ineficiente:
        final_id = "exito_ineficiente"
        numero_final = 1
        titulo_final = "Final 1B — Éxito con Ineficiencias"
        subtitulo_final = (
            "Objetivos científicos cumplidos, pero con decisiones de diseño o gestión que costaron más de lo necesario."
        )
        motivos = []
        if motor_excesivo:
            motivos.append(
                "llevaste un motor de mayor Isp y coste del necesario para el destino (un motor más económico hubiera bastado)"
            )
        if instrumento_sin_especialista:
            motivos.append(
                "instalaste instrumentos sin contratar al especialista afín, reduciendo su rendimiento"
            )
        if robot_sin_uso:
            motivos.append(
                "compraste el robot autónomo pero no generó datos científicos"
            )
        detalle = "; ".join(motivos) if motivos else "hubo márgenes de diseño por encima de lo requerido"
        if fue_en_solitario:
            dialogo_apertura = (
                "El Comisionado Félix Vance sonríe con aprobación pero frunce el ceño al revisar la ficha de diseño: "
                f"«Cumpliste la meta científica en {nombre_destino_corto} volando en solitario, Director, pero {detalle}. "
                f"{diagnostico_ciencia_narrativo}»"
            )
        else:
            dialogo_apertura = (
                "El Comisionado Félix Vance sonríe con aprobación pero frunce el ceño al revisar la ficha de diseño: "
                f"«Buen trabajo de equipo en {nombre_destino_corto}, pero {detalle}. "
                f"{diagnostico_ciencia_narrativo}»"
            )
        frase_despedida = (
            "«Cumplir la misión es el primer paso; optimizar masa, energía y coste es lo que distingue a un director excelente. "
            "Revisa las fichas técnicas antes de la próxima expedición.»"
        )
    else:
        final_id = "supervivencia_mision_parcial"
        numero_final = 2
        titulo_final = "Final 2 — Supervivencia con Misión Parcial"
        subtitulo_final = (
            "Retorno seguro a Tierra, pero la cosecha o transmisión de datos científicos quedó incompleta."
        )
        if fue_en_solitario:
            dialogo_apertura = (
                "El Comisionado Félix Vance revisa las gráficas en su terminal ámbar y te observa con gesto serio: "
                f"«La nave regresó de una pieza y tú volviste sano y salvo de {nombre_destino_corto}, que es lo primero. "
                "Pero decidiste despegar completamente solo, sin contratar a ningún especialista en la Etapa 3. "
                f"Sin manos expertas en el Laboratorio, nos quedamos cortos en la meta científica. {diagnostico_ciencia_narrativo}»"
            )
        else:
            dialogo_apertura = (
                "El Comisionado Félix Vance revisa las gráficas en su terminal ámbar: "
                f"«La nave regresó de una pieza de {nombre_destino_corto} y tanto tú como tu equipo ({nombres_especialistas}) "
                "están en casa sanos y salvos, que es lo primero. Sin embargo, en el plano científico nos quedamos cortos "
                f"respecto al acuerdo firmado. {diagnostico_ciencia_narrativo}»"
            )
        frase_despedida = (
            "«Regresar con vida siempre es una victoria; para alcanzar el Éxito Pleno recuerda recolectar ciencia "
            "en el Laboratorio (Etapa 7) y transmitir todos los GB en la Sala de Sistemas antes de volver.»"
        )

    # Monólogo de ruptura de la cuarta pared si hubo pérdida de tripulación / sin retorno
    monologo_cuarta_pared: str | None = None
    silencio_previo = 0
    if hubo_bajas:
        silencio_previo = 4
        if fue_en_solitario:
            monologo_cuarta_pared = (
                "[Silencio absoluto en el despacho durante cuatro segundos. El Gato Jefe aparta los informes y "
                "mira directamente hacia la pantalla, hablándote a ti, el jugador]: "
                "«Pensaste que podías ahorrar presupuesto lanzando al Director en solitario y llevando los números al límite. "
                "Las fichas técnicas estuvieron frente a tus ojos desde el primer minuto: la masa máxima del cohete, "
                "los metros por segundo de Delta-v requeridos para volver y el consumo de oxígeno. "
                "Nadie te ocultó un solo parámetro. Tú pulsaste el botón de lanzamiento.»"
            )
        else:
            monologo_cuarta_pared = (
                "[Silencio absoluto en el despacho durante cuatro segundos. El Gato Jefe aparta los informes y "
                "mira directamente hacia la pantalla, hablándote a ti, el jugador]: "
                f"«Para ti, {nombres_especialistas} eran solo sprites estáticos con un icono de sol o de lluvia sobre la cabeza "
                "y una fila más en la tabla de masa y presupuesto. Pero los números de las fichas técnicas estaban ahí "
                "desde el minuto uno: sabías cuánto pesaba la nave, cuánto oxígeno llevabas y cuánto Delta-v exigía volver a casa. "
                "Nadie te ocultó un solo dato. Tú pulsaste el botón de lanzamiento asumiendo ese riesgo.»"
            )

    comentario_supervivencia = (
        (
            "Volaste en solitario (1/1): regresaste con vida, aunque el aislamiento redujo tu rendimiento mental."
            if fue_en_solitario
            else f"Regresaron los {len(vivos)}/{total_crew} integrantes de la expedición ({nombres_especialistas} + Director)."
        )
        if not hubo_bajas
        else (
            "Vuelo en solitario fallido: no lograste regresar con vida a la Tierra."
            if fue_en_solitario
            else f"Bajas críticas en la misión ({len(vivos)}/{total_crew} sobrevivientes)."
        )
    )

    dimensiones = [
        DimensionEvaluacion(
            id="ciencia",
            nombre="Objetivos Científicos",
            puntuacion=score_ciencia,
            estado_etiqueta="Óptimo"
            if score_ciencia >= 75
            else ("Parcial" if score_ciencia >= 40 else "Deficiente"),
            comentario_jefe=(
                f"Generaste {estado.puntos_ciencia_generados:.1f} puntos de ciencia frente a una meta de {meta_ciencia:.0f} pts."
            ),
            explicacion_tecnica=(
                "Se obtiene operando el Laboratorio Científico en la Etapa 7; rinde más si contratas al especialista afín al instrumento."
            ),
        ),
        DimensionEvaluacion(
            id="supervivencia",
            nombre="Supervivencia y Dotación",
            puntuacion=score_supervivencia,
            estado_etiqueta=(
                ("Solitario" if fue_en_solitario else "Íntegra")
                if not hubo_bajas
                else "Pérdida Crítica"
            ),
            comentario_jefe=comentario_supervivencia,
            explicacion_tecnica=(
                "Volar solo ahorra salarios y masa, pero penaliza la salud mental y la velocidad/calidad de las tareas."
            ),
        ),
        DimensionEvaluacion(
            id="datos",
            nombre="Calidad y Transmisión de Datos",
            puntuacion=score_datos,
            estado_etiqueta="Fluida" if score_datos >= 70 else "Incompleta",
            comentario_jefe=(
                f"Transmitiste {estado.datos_transmitidos_gb:.1f} GB de {estado.datos_generados_gb:.1f} GB recolectados "
                f"(Calidad media: {estado.calidad_datos_promedio:.0f}%)."
            ),
            explicacion_tecnica=(
                "Los datos generados en el Laboratorio deben enviarse a Tierra usando las ventanas de comunicación en las Etapas 7 a 9."
            ),
        ),
        DimensionEvaluacion(
            id="presupuesto",
            nombre="Gestión de Presupuesto Global",
            puntuacion=score_presupuesto,
            estado_etiqueta="Solvente"
            if estado.presupuesto_restante_usd >= 5000
            else "Al Límite",
            comentario_jefe=(
                f"Saldo final: {estado.presupuesto_restante_usd:,.0f} CZ de {estado.presupuesto_inicial_usd:,.0f} CZ iniciales."
            ),
            explicacion_tecnica=(
                "Límite duro que integra compra de componentes, salarios de especialistas y gastos operativos en tiempo real."
            ),
        ),
        DimensionEvaluacion(
            id="tiempo",
            nombre="Tiempo y Planificación Orbital",
            puntuacion=score_tiempo,
            estado_etiqueta="En Ventana" if score_tiempo >= 75 else "Con Demora",
            comentario_jefe=f"Duración operativa acumulada: {estado.dias_transcurridos} día(s) en misión hacia {estado.destino.value}.",
            explicacion_tecnica="La elección entre transferencia Hohmann o rápida intercambia días de soporte vital por consumo de Delta-v.",
        ),
        DimensionEvaluacion(
            id="nave",
            nombre="Estado Final de la Nave",
            puntuacion=score_nave,
            estado_etiqueta="Nominal" if score_nave >= 85 else "Degradada",
            comentario_jefe=f"Integridad media de subsistemas al cierre: {score_nave:.0f}%.",
            explicacion_tecnica="Refleja las anomalías sufridas en vuelo y las reparaciones realizadas por la tripulación.",
        ),
        DimensionEvaluacion(
            id="retorno",
            nombre="Capacidad de Retorno",
            puntuacion=score_retorno,
            estado_etiqueta="Asegurado" if score_retorno > 0 else "Fallido",
            comentario_jefe=f"Delta-v remanente tras maniobra de reentrada: {estado.delta_v_disponible_ms:.1f} m/s.",
            explicacion_tecnica=(
                "Calculado mediante la ecuación de Tsiolkovsky descontando lanzamiento, inyección, contingencias y retorno."
            ),
        ),
    ]

    # Construir trazabilidad causal y recomendaciones pedagógicas específicas
    trazabilidad: list[str] = list(estado.bitacora_decisiones[-7:])
    recomendaciones: list[str] = []
    if motor_excesivo:
        recomendaciones.append(
            "El motor criogénico LH2/LOX da más Delta-v del necesario para OTB: en misiones cercanas, un motor de menor Isp y coste (MMH/MON-3 o hidracina) habría liberado presupuesto y masa."
        )
    if robot_sin_uso:
        recomendaciones.append(
            "Compraste el robot autónomo pero no generó datos científicos: si no planeas operarlo en el destino, su masa y coste no aportaron al objetivo Helios-9."
        )
    if instrumento_sin_especialista:
        recomendaciones.append(
            "Había instrumentos instalados sin el especialista afín a bordo: su rendimiento científico y de calidad quedó por debajo de lo óptimo."
        )
    if fue_en_solitario:
        recomendaciones.append(
            "Contratar al menos 1 o 2 especialistas en la Etapa 3 (pestaña '🐶 2. Tripulación'): evitas el debuff de aislamiento en solitario y multiplicas los puntos de ciencia y reparación."
        )
    if estado.datos_generados_gb <= 0 and not fallo_temprano:
        recomendaciones.append(
            "En la Etapa 7 (Operaciones Científicas), recuerda pulsar '🔬 PASO 1: Recolectar Datos en Laboratorio' o usar la tecla [E] dentro del Laboratorio para generar ciencia."
        )
    elif estado.datos_generados_gb > estado.datos_transmitidos_gb + 0.2 and not fallo_temprano:
        recomendaciones.append(
            f"Dejaste {estado.datos_generados_gb - estado.datos_transmitidos_gb:.1f} GB sin enviar en la memoria de la nave: usa el botón '📡 PASO 2: Transmitir Datos a Tierra' antes de finalizar la Etapa 9."
        )
    if estado.masa_total_kg > estado.masa_lanzamiento_max_kg:
        recomendaciones.append(
            f"Reducir la masa total ({estado.masa_total_kg} kg) por debajo del límite fijo del lanzador ({estado.masa_lanzamiento_max_kg} kg)."
        )
    if estado.balance_potencia_w < 0:
        recomendaciones.append(
            f"Corregir el déficit eléctrico ({estado.balance_potencia_w} W) instalando paneles solares de mayor generación."
        )
    if sin_retorno or estado.delta_v_inicial_ms < estado.delta_v_requerido_total_ms:
        recomendaciones.append(
            f"Para {estado.destino.value}, asegurar al menos {estado.delta_v_requerido_total_ms} m/s de Delta-v combinando un motor de mayor Isp con menor masa seca."
        )
    if not recomendaciones:
        recomendaciones.append(
            "Ejecución sobresaliente: lograste coordinar diseño, dotación, recolección y transmisión. Prueba ahora el destino Lunar o una dificultad superior."
        )

    return InformeFinal(
        mission_id=estado.id,
        final_id=final_id,
        numero_final=numero_final,
        titulo_final=titulo_final,
        subtitulo_final=subtitulo_final,
        puntuacion_global=puntuacion_global,
        hubo_muertes_tripulacion=hubo_bajas,
        silencio_previo_segundos=silencio_previo,
        dialogo_jefe_apertura=dialogo_apertura,
        monologo_cuarta_pared=monologo_cuarta_pared,
        dimensiones=dimensiones,
        trazabilidad_causal=trazabilidad,
        recomendaciones_ingenieria=recomendaciones,
        frase_despedida=frase_despedida,
        resumen_tecnico_datos={
            "destino": estado.destino.value,
            "modo_dotacion": "En Solitario (1)" if fue_en_solitario else f"Equipo ({total_crew})",
            "masa_final_kg": estado.masa_total_kg,
            "masa_max_lanzador_kg": estado.masa_lanzamiento_max_kg,
            "delta_v_inicial_ms": estado.delta_v_inicial_ms,
            "delta_v_restante_ms": estado.delta_v_disponible_ms,
            "balance_potencia_w": estado.balance_potencia_w,
            "bateria_restante_wh": estado.bateria_actual_wh,
            "datos_generados_gb": estado.datos_generados_gb,
            "datos_transmitidos_gb": estado.datos_transmitidos_gb,
            "presupuesto_inicial_usd": estado.presupuesto_inicial_usd,
            "presupuesto_final_usd": estado.presupuesto_restante_usd,
            "tripulantes_vivos": f"{len(vivos)}/{total_crew}",
        },
    )
