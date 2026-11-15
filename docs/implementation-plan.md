# Zenit — Plan de implementación técnica (MVP)

Documento de referencia para construir el MVP del "Simulador narrativo de misiones espaciales".
Complementa `vercel.json` (infraestructura) y `artboard.html` (dirección de arte).

---

## 1. Arquitectura técnica

### 1.1 Módulos y responsabilidades

| Módulo | Ubicación sugerida | Responsabilidad |
|---|---|---|
| `narrative-ui` | frontend (Vue 3) | Renderiza texto, opciones, tablas de variables afectadas, escenas pixel art, nave visual. No calcula nada. |
| `mission-state` | backend (FastAPI) | Fuente de verdad del estado de la misión (diseño, recursos, tripulación, progreso de etapas). Persiste y valida transiciones. |
| `validation-engine` | backend puro | Valida decisiones contra restricciones físicas (masa, presupuesto, energía) y devuelve `allowed / warning / fail`. |
| `consequence-engine` | backend puro | Aplica una decisión aprobada al estado: actualiza masa, energía, delta-v, presupuesto, puntuaciones. |
| `event-engine` | backend puro | Genera eventos según estado + entorno + ánimo + decisiones previas (no deterministas). |
| `evaluation-engine` | backend puro | Calcula puntuaciones multidimensionales y selecciona final ramificado. |
| `report-renderer` | frontend | Presenta informe final y escena del jefe. |

### 1.2 Contratos de datos (API)

- `POST /api/v1/missions` → crea misión (destino, presupuesto, tripulación). Devuelve `mission_id`.
- `GET /api/v1/missions/{id}` → estado completo.
- `POST /api/v1/missions/{id}/decisions` → `{stage, decision, params}` → `{allowed, warnings, affected_variables[], new_state_summary}`.
- `POST /api/v1/missions/{id}/advance` → avanza etapa si válida.
- `GET /api/v1/missions/{id}/events` → eventos activos.
- `POST /api/v1/missions/{id}/events/{eid}/resolve` → resuelve evento con opción elegida.
- `GET /api/v1/missions/{id}/report` → informe final + final seleccionado.

### 1.3 Flujo de una decisión

1. UI envía decisión al backend.
2. `validation-engine` comprueba restricciones críticas → si falla, devuelve `fail` inmediato (sin mutar estado).
3. Si pasa, `consequence-engine` muta el estado y devuelve tabla de variables afectadas (masa, energía, delta-v, datos, presupuesto).
4. UI muestra la tabla; el jugador interpreta riesgos (sin advertencias de desastre).
5. `event-engine` puede disparar eventos derivados del nuevo estado.

---

## 2. Modelo de interdependencias

### 2.1 Tabla de dependencias

| Subsistema | Entradas | Salidas | Variables compartidas | Restricciones que impone |
|---|---|---|---|---|
| Masa/Estructura | componentes seleccionados, estructura | masa total (kg) | `mass_total` | No puede superar `mass_launch_max` (fallo inmediato). |
| Propulsión | motor, combustible, masa total | delta-v disponible, consumo | `delta_v`, `fuel` | Trayectoria requiere delta-v ≥ delta-v requerido. |
| Energía | paneles, baterías, consumo | generación W, autonomía h | `energy_gen`, `energy_cons` | Déficit → degradación progresiva. |
| Telecomunicaciones | antena, potencia | alcance km, tasa kbps, ventanas/día | `comm_range`, `data_rate`, `windows` | Datos no transmitidos se pierden/acumulan. |
| Soporte vital | tripulación, sistemas | O₂, agua, comida (días) | `o2_days`, `food_days` | Escasez → degradación de salud. |
| Tripulación | roles, especialidad, experiencia | velocidad de tarea, calidad | `crew_speed`, `crew_quality` | Salario afecta presupuesto; ánimo afecta velocidad. |
| Científico | instrumentos, tripulación especialista | puntos ciencia, datos generados | `science_points`, `data_volume` | Más instrumentos → más masa/consumo. |
| Orbital/Trayectoria | delta-v, ventanas de lanzamiento, destino | tiempo de tránsito, factibilidad | `transit_days`, `feasible` | Si no hay delta-v suficiente → misión imposible. |
| Presupuesto | todos los costes | saldo | `budget_remaining` | Límite duro: no puede ser negativo. |
| Eventos | estado completo + entorno + ánimo | eventos activos | `events[]` | Pueden alterar cualquier variable compartida. |

### 2.2 Cadena causal de ejemplo (con números)

Decisión del jugador: añadir un espectrómetro (+50 kg, +120 W consumo, +8.000 USD, +15 puntos ciencia).

1. **Masa**: 1.200 kg → 1.250 kg. Si `mass_launch_max` = 1.300 kg, sigue dentro (sin fallo). Si fuera 1.240 kg, fallo inmediato.
2. **Propulsión**: con el motor MMH/MON-3 de impulso específico 315 s (clase OMS-E de Orión, fuente NASA) y un tripulante, delta-v disponible baja de ≈3.490 m/s a ≈3.230 m/s (Tsiolkovsky).
3. **Trayectoria**: la Luna requiere 3.100 m/s de delta-v en el modelo de juego → margen queda en ≈130 m/s (ajustado). Ver `docs/fuentes-nasa.md` para el presupuesto real (≈5.100 m/s desde OTB).
4. **Energía**: consumo pasa de 480 W a 600 W; generación 550 W → déficit de 50 W → baterías se descargan → degradación progresiva de sistemas.
5. **Científico**: +15 puntos ciencia, pero genera +2 GB de datos/día que deben transmitirse.
6. **Telecomunicaciones**: antena de 2 Mbps → transmitir 2 GB exige ≈133 min (≈2,2 h) de enlace continuo (2 GB × 8 / 2 Mbps); si solo hay 2 ventanas/día, se acumulan datos.
7. **Presupuesto**: saldo −8.000 USD; si quedan 3.000 USD, queda negativo → decisión bloqueada por presupuesto.
8. **Visual**: la nave en pantalla gana un módulo lateral (espectrómetro) con indicador de consumo.

Lección: el jugador ve la tabla de variables afectadas (masa, energía, delta-v, datos, presupuesto) y decide si asume el riesgo.

---

## 3. Sistema de eventos

### 3.1 Generación
- No deterministas: dependen de `estado + entorno + ánimo + decisiones previas`.
- Cada evento tiene `probabilidad_base` modificada por factores (ej.: fuga de combustible más probable si el tanque está cerca del límite térmico).
- Entorno: terreno lunar helado aumenta probabilidad de resbalar de un robot; radiación afecta electrónica.
- Ánimo: tripulante con "lluvia" tiene debuff de desconcentración → más tiempo y menor calidad en la tarea.

### 3.2 Comunicación al jugador
- Alertas sin cuantificar: "Se detecta una anomalía en el módulo de energía." (sin decir cuánto).
- El jugador puede usar una ventana de comunicación para informar y pedir retroalimentación (coste: 1 ventana + energía). No siempre es óptimo.
- Eventos aleatorios (fugas, accidentes) y fallos de componentes se comunican por mensajes de alerta.

### 3.3 Estados de ánimo
- Representados visualmente como sol/nube/lluvia sobre la cabeza del tripulante.
- Aparecen de forma aleatoria.
- Afectan velocidad y calidad de tareas.

---

## 4. Evaluación final

### 4.1 Número de finales propuesto: 5
Justificación: suficiente para variedad narrativa sin sobrecargar el alcance del MVP. Verificables por combinación de umbrales.

1. **Éxito científico pleno**: todos los objetivos científicos cumplidos, tripulación viva, retorno exitoso.
2. **Supervivencia con misión parcial**: tripulación viva pero objetivos científicos incompletos.
3. **Retorno de emergencia**: se aborta y regresa con datos parciales.
4. **Pérdida de tripulación, datos recuperados**: tripulación muere, pero los datos llegan a Tierra.
5. **Fallo total**: no hay retorno ni datos.

### 4.2 Dimensiones de evaluación
- Objetivos científicos (0-100)
- Supervivencia (viva/muerta, salud)
- Tiempo (dentro/fuera de ventana)
- Presupuesto (saldo final)
- Calidad de datos transmitidos
- Estado final de la nave
- Capacidad de retorno (delta-v restante)

### 4.3 Informe final
- Escena con el jefe (oficina desaturada): retroalimentación conversacional por dimensión.
- Si la tripulación murió: silencio total antes del monólogo (rompe la cuarta pared).
- Luego documento de reporte técnico con datos principales.
- Frase final motivadora o no.

---

## 5. Decisiones técnicas abiertas y resueltas

1. **Realismo vs jugabilidad (Resuelta — Opción A)**: Usar valores físicos reales en propulsión y energía (ecuación de Tsiolkovsky, $I_{\text{sp}}$, $\text{W}$ y $\text{Wh}$) y valores simplificados en soporte vital y tripulación (días-persona de $\text{O}_2$ y comida).
2. **Costes imprevistos (Implementado)**: Separar presupuesto financiero de energía. En tránsito y en órbita, los costes de soporte terrestre consumen presupuesto financiero en tiempo real; las maniobras y sistemas redundantes consumen energía ($\text{Wh}$) y $\Delta v$.
3. **Representación gráfica de la nave (En progreso — Placeholders activos)**: Esquemático técnico SVG reactivo (`ShipSchematic.vue`) y vista 2D lateral de habitaciones (`DestinationRooms2D.vue` / `Sala2D.vue`) con la paleta de `artboard.html` listos mientras se integran los sprites definitivos.
4. **Especialidad vs experiencia (Resuelta — Opción A)**: La especialidad habilita tareas científicas y optimiza las comunes; la experiencia modifica la velocidad. En tareas comunes (como reparación), un no-especialista **nunca falla**, únicamente tarda más tiempo y obtiene menor rendimiento/calidad.
5. **Accesibilidad (daltonismo)**: Reforzar color con forma (`▲`, `?`) y parpadeo suave (`blink-warning`).
6. **Reserva del rojo**: Reservado para fallos graves y ruptura de cuarta pared.
7. **Persistencia de datos en Vercel**: SQLite con respaldo en `/tmp/zenit_missions.db` y memoria para entornos serverless efímeros.

---

## 6. MVP por fases

### Fase 1 — Núcleo (2-3 semanas)
- Estado de misión + validación + consecuencias (backend puro).
- Una misión completa en OTB: definición, diseño, lanzamiento, retorno.
- Sin eventos complejos ni tripulación detallada.

### Fase 2 — Mecánica orbital + tripulación (2-3 semanas)
- Planificación orbital (delta-v, ventanas).
- Tripulación (4 max, roles, especialidades).
- Eventos básicos (fugas, ánimo).

### Fase 3 — Destino Luna + evaluación (2 semanas)
- Segundo destino.
- Sistema de eventos completo.
- Evaluación + 5 finales + informe final.

### Fase 4 — Pulido visual (2 semanas)
- Pixel art de habitaciones (tecla E).
- Nave visual esquemática con cambios reflejados.
- Música adaptativa.

---

## Preguntas abiertas para el equipo

1. ¿Cuántos tripulantes mínimo para que una misión sea viable? (propuesta: 2 para OTB, 3 para Luna)
2. ¿Los robots son opcionales en el MVP o se incluyen? (propuesta: opcionales, post-MVP)
3. ¿El presupuesto es global o por etapa? (decidido: global, límite duro)
4. ¿Se permite guardar partida? (propuesta: sí, un slot)
5. ¿El informe final es el único output o también hay ranking? (propuesta: solo informe)