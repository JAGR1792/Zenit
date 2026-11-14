"""Motor de evaluación multidimensional, selección de finales ramificados e informe del jefe."""

from __future__ import annotations

from app.repositories.seed import ACUERDOS_FINANCIACION, DESTINOS_CATALOGO
from app.schemas.mission import DimensionEvaluacion, EstadoMision, InformeFinal


def generar_informe_final(estado: EstadoMision) -> InformeFinal:
    """Calcula las 7 dimensiones de evaluación, determina el final ramificado (1 a 5) y construye la escena del jefe.

    Args:
        estado: Estado final de la misión.

    Returns:
        InformeFinal: Estructura completa con diálogo del jefe, monólogo de cuarta pared y reporte técnico.
    """
    acuerdo = next(
        (a for a in ACUERDOS_FINANCIACION if a["id"] == estado.acuerdo_financiacion_id),
        ACUERDOS_FINANCIACION[1],
    )
    meta_ciencia = float(acuerdo["exigencia_ciencia"])
    params_destino = DESTINOS_CATALOGO[estado.destino]

    vivos = [t for t in estado.tripulacion if t.vivo]
    total_crew = max(1, len(estado.tripulacion))
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

    # 3. Dimensión Supervivencia y Salud de Tripulación
    if fallo_temprano or len(vivos) == 0:
        score_supervivencia = 0.0
    elif sin_retorno:
        score_supervivencia = 20.0
    else:
        salud_media = sum((t.salud + t.salud_mental) / 2.0 for t in vivos) / total_crew
        score_supervivencia = round((len(vivos) / total_crew) * salud_media, 1)

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

    # Selección de uno de los 5 finales ramificados
    if fallo_temprano or (hubo_bajas and estado.datos_transmitidos_gb <= 0.2):
        final_id = "fallo_total"
        numero_final = 5
        titulo_final = "Final 5 — Fallo Total de la Misión"
        subtitulo_final = "Pérdida de vehículo y ausencia de retorno científico."
        dialogo_apertura = (
            "La oficina está a oscuras. Sobre el escritorio de acero solo hay una carpeta cerrada con el sello "
            f"de investigación de siniestros. El jefe te mira en silencio: «{estado.causa_fallo or 'Perdimos la misión por completo.'}»"
        )
        frase_despedida = (
            "«La física no negocia con el optimismo, Director. Cuando vuelva a leer una ficha técnica, "
            "recuerde que cada número tiene peso.»"
        )
    elif hubo_bajas and estado.datos_transmitidos_gb > 0.2:
        final_id = "perdida_tripulacion_datos_recuperados"
        numero_final = 4
        titulo_final = "Final 4 — Pérdida de Tripulación, Datos Recuperados"
        subtitulo_final = "La telemetría llegó a las antenas terrenas, pero la nave no regresó con su dotación."
        dialogo_apertura = (
            "Las pantallas del despacho muestran los paquetes de datos descargados desde la antena, "
            "pero las sillas de la sala de espera están vacías."
        )
        frase_despedida = (
            "«Los servidores están llenos de ciencia nueva. Ojalá alguien en este edificio tuviera hoy "
            "el valor de celebrarlo.»"
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
            "La tripulación sobrevivió al límite operativo con telemetría parcial."
        )
        dialogo_apertura = (
            "El jefe apoya ambas manos sobre la mesa iluminada con luz fría: "
            "«Los trajiste de vuelta por los pelos, Director. El casco regresó con las reservas al mínimo, "
            "pero al menos podemos analizar qué salió mal.»"
        )
        frase_despedida = (
            "«Sobrevivir a un diseño al límite enseña más que diez simulaciones en tierra. "
            "Corrija los márgenes para el próximo vuelo.»"
        )
    elif score_ciencia >= 70.0 and score_datos >= 65.0:
        final_id = "exito_cientifico_pleno"
        numero_final = 1
        titulo_final = "Final 1 — Éxito Científico Pleno"
        subtitulo_final = (
            "Objetivos científicos cumplidos, datos transmitidos y retorno íntegro."
        )
        dialogo_apertura = (
            "El jefe se levanta al verte entrar en la oficina y extiende el informe encuadernado: "
            "«Un trabajo de ingeniería impecable. Equilibraste masa, impulso específico, energía y ancho de banda "
            "sin comprometer ni una sola vida.»"
        )
        frase_despedida = (
            "«Así se construye la exploración espacial real: leyendo cada parámetro y respetando cada restricción. "
            "Enhorabuena, Director.»"
        )
    else:
        final_id = "supervivencia_mision_parcial"
        numero_final = 2
        titulo_final = "Final 2 — Supervivencia con Misión Parcial"
        subtitulo_final = "La tripulación regresó sana y salva, pero el retorno de datos científicos quedó incompleto."
        dialogo_apertura = (
            "El jefe revisa las gráficas en su terminal ámbar: "
            "«La nave regresó de una pieza y tu gente está en casa, que es lo primero. "
            "Sin embargo, desde el punto de vista científico nos quedamos cortos respecto a lo prometido.»"
        )
        frase_despedida = (
            "«Traer a la tripulación con vida siempre es una victoria; lograr además toda la ciencia exige "
            "afinar el cuello de botella entre instrumentos y comunicaciones.»"
        )

    # Monólogo de ruptura de la cuarta pared si hubo pérdida de tripulación / sin retorno
    monologo_cuarta_pared: str | None = None
    silencio_previo = 0
    if hubo_bajas:
        silencio_previo = 4
        monologo_cuarta_pared = (
            "[Silencio absoluto en la oficina durante cuatro segundos. El jefe aparta los papeles técnicos y "
            "mira directamente hacia la pantalla, hablándote a ti, el jugador]: "
            "«Para ti eran perfiles deterministas con un icono de sol o de lluvia sobre la cabeza y una fila más "
            "en la tabla de masa y presupuesto. Los números de las fichas técnicas estaban ahí desde el minuto uno: "
            "sabías cuánto pesaba la nave, cuánto oxígeno llevabas y cuántos metros por segundo exigía volver a casa. "
            "Nadie te ocultó un solo dato. Tú pulsaste el botón de lanzamiento asumiendo ese riesgo.»"
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
                f"Generaste {estado.puntos_ciencia_generados:.1f} puntos de ciencia frente a una meta de {meta_ciencia:.0f}."
            ),
            explicacion_tecnica=(
                "Depende de los instrumentos instalados, la presencia del especialista afín y su estado de concentración."
            ),
        ),
        DimensionEvaluacion(
            id="supervivencia",
            nombre="Supervivencia y Tripulación",
            puntuacion=score_supervivencia,
            estado_etiqueta="Íntegra" if not hubo_bajas else "Pérdida Crítica",
            comentario_jefe=(
                f"Regresaron {len(vivos)}/{total_crew} tripulantes en condiciones de retorno nominal."
                if not hubo_bajas
                else "No lograste traer de vuelta a toda la tripulación a salvo."
            ),
            explicacion_tecnica=(
                "Condicionada por la autonomía de soporte vital (O2/comida), el aislamiento y el Delta-v de retorno."
            ),
        ),
        DimensionEvaluacion(
            id="datos",
            nombre="Calidad y Transmisión de Datos",
            puntuacion=score_datos,
            estado_etiqueta="Fluida" if score_datos >= 70 else "Cuello de Botella",
            comentario_jefe=(
                f"Transmitiste {estado.datos_transmitidos_gb:.1f} GB de {estado.datos_generados_gb:.1f} GB generados "
                f"(Calidad media: {estado.calidad_datos_promedio:.0f}%)."
            ),
            explicacion_tecnica=(
                "Los datos sin transmitir en las ventanas de comunicación fijas no puntúan. "
                "Usar ventanas para pedir diagnóstico a Tierra reduce el margen de descarga."
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
                f"Saldo final: {estado.presupuesto_restante_usd:,.0f} USD de {estado.presupuesto_inicial_usd:,.0f} USD iniciales."
            ),
            explicacion_tecnica=(
                "Límite duro que integra compra de componentes, salarios y gastos de contingencia en tiempo real."
            ),
        ),
        DimensionEvaluacion(
            id="tiempo",
            nombre="Tiempo y Planificación Orbital",
            puntuacion=score_tiempo,
            estado_etiqueta="En Ventana" if score_tiempo >= 75 else "Con Demora",
            comentario_jefe=f"Duración operativa acumulada: {estado.dias_transcurridos} día(s) en {estado.destino.value}.",
            explicacion_tecnica="La elección entre transferencia estándar o rápida intercambia tiempo (consumibles) por Delta-v.",
        ),
        DimensionEvaluacion(
            id="nave",
            nombre="Estado Final de la Nave",
            puntuacion=score_nave,
            estado_etiqueta="Nominal" if score_nave >= 85 else "Degradada",
            comentario_jefe=f"Integridad media de subsistemas al cierre: {score_nave:.0f}%.",
            explicacion_tecnica="Refleja los fallos aleatorios ocurridos y la eficacia de las reparaciones ejecutadas.",
        ),
        DimensionEvaluacion(
            id="retorno",
            nombre="Capacidad de Retorno",
            puntuacion=score_retorno,
            estado_etiqueta="Asegurado" if score_retorno > 0 else "Fallido",
            comentario_jefe=f"Delta-v remanente tras reentrada/retorno: {estado.delta_v_disponible_ms:.1f} m/s.",
            explicacion_tecnica=(
                "Calculado por la ecuación de Tsiolkovsky descontando ascenso, inyección, maniobras imprevistas y retorno."
            ),
        ),
    ]

    # Construir trazabilidad causal y recomendaciones pedagógicas
    trazabilidad: list[str] = list(estado.bitacora_decisiones[-6:])
    recomendaciones: list[str] = []
    if estado.masa_total_kg > estado.masa_lanzamiento_max_kg:
        recomendaciones.append(
            f"Reducir la masa total ({estado.masa_total_kg} kg) por debajo del límite fijo del lanzador ({estado.masa_lanzamiento_max_kg} kg)."
        )
    if estado.balance_potencia_w < 0:
        recomendaciones.append(
            f"Corregir el déficit eléctrico ({estado.balance_potencia_w} W): la potencia generada por los paneles debe superar el consumo simultáneo."
        )
    if estado.datos_generados_gb > estado.datos_transmitidos_gb + 0.5:
        recomendaciones.append(
            "Dimensionar la antena (kbps y ventanas/día) acorde al volumen de datos generado por los instrumentos científicos."
        )
    if sin_retorno or estado.delta_v_inicial_ms < estado.delta_v_requerido_total_ms:
        recomendaciones.append(
            f"Para {estado.destino.value}, asegurar al menos {estado.delta_v_requerido_total_ms} m/s de Delta-v combinando un motor de mayor Isp con menor masa seca."
        )
    if not recomendaciones:
        recomendaciones.append(
            "Configuración sobresaliente: puedes intentar ahora el destino lunar con el acuerdo de financiación austero."
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
