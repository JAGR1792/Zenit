# Zenit — Documento de diseño (Simulador narrativo de misiones espaciales)

Documento de diseño del juego serio educativo. Complementa `docs/implementation-plan.md`
(arquitectura técnica) y `artboard.html` (dirección de arte).

## 1. Arquitectura conceptual

### 1.1 Módulos y responsabilidades

- **Interfaz narrativa (frontend):** renderiza texto, opciones, tablas de variables afectadas,
  escenas pixel art y la nave visual. No calcula nada; solo presenta y captura decisiones.
- **Estado de la misión (backend):** fuente de verdad. Persiste diseño, recursos, tripulación,
  progreso de etapas y eventos activos.
- **Motor de validación (backend puro):** comprueba decisiones contra restricciones físicas
  (masa, presupuesto, energía) y devuelve `allowed / warning / fail`. No muta estado.
- **Cálculo de consecuencias (backend puro):** aplica una decisión aprobada al estado y
  devuelve la tabla de variables afectadas (masa, energía, delta-v, datos, presupuesto).
- **Sistema de eventos (backend puro):** genera eventos según estado + entorno + ánimo +
  decisiones previas, sin ser determinista.
- **Evaluación final (backend puro):** calcula puntuaciones multidimensionales y selecciona
  el final ramificado.

### 1.2 Flujo de una decisión

1. El jugador elige una opción en la interfaz narrativa.
2. El backend valida contra restricciones críticas (fallo inmediato si se supera la masa
   de lanzamiento o el presupuesto).
3. Si pasa, se aplican consecuencias y se devuelve la tabla de variables afectadas.
4. La interfaz muestra la tabla sin advertir del desastre resultante; el jugador interpreta.
5. El sistema de eventos puede disparar eventos derivados del nuevo estado.

---

## 2. Modelo de interdependencias entre subsistemas

### 2.1 Tabla de dependencias

| Subsistema | Entradas | Salidas | Variables compartidas | Restricciones que impone |
|---|---|---|---|---|
| Masa/Estructura | componentes, estructura | masa total (kg) | `mass_total` | No superar `mass_launch_max` (fallo inmediato). |
| Propulsión | motor, combustible, masa total | delta-v disponible, consumo | `delta_v`, `fuel` | Trayectoria requiere delta-v ≥ requerido. |
| Energía | paneles, baterías, consumo | generación W, autonomía h | `energy_gen`, `energy_cons` | Déficit → degradación progresiva. |
| Telecomunicaciones | antena, potencia | alcance km, tasa kbps, ventanas/día | `comm_range`, `data_rate`, `windows` | Datos no transmitidos se acumulan/pierden. |
| Soporte vital | tripulación, sistemas | O₂, agua, comida (días) | `o2_days`, `food_days` | Escasez → degradación de salud. |
| Tripulación | roles, especialidad, experiencia | velocidad de tarea, calidad | `crew_speed`, `crew_quality` | Salario afecta presupuesto; ánimo afecta velocidad. |
| Científico | instrumentos, especialista | puntos ciencia, datos generados | `science_points`, `data_volume` | Más instrumentos → más masa/consumo. |
| Orbital/Trayectoria | delta-v, ventanas, destino | tiempo de tránsito, factibilidad | `transit_days`, `feasible` | Sin delta-v suficiente → misión imposible. |
| Presupuesto | todos los costes | saldo | `budget_remaining` | Límite duro: no puede ser negativo. |
| Eventos | estado completo + entorno + ánimo | eventos activos | `events[]` | Pueden alterar cualquier variable compartida. |

### 2.2 Cadena causal (caso completo)

Decisión: añadir un espectrómetro (+50 kg, +120 W, +8.000 USD, +15 pts ciencia).

1. **Masa:** 1.200 → 1.250 kg. Si `mass_launch_max` = 1.300 kg, sigue dentro. Si fuera 1.240 kg, fallo inmediato.
2. **Propulsión:** con el motor MMH/MON-3 (Isp 315 s, clase OMS-E de Orión) y un tripulante, delta-v disponible baja de ≈3.490 a ≈3.230 m/s.
3. **Trayectoria:** la Luna requiere 3.100 m/s en el modelo de juego → margen de ≈130 m/s (ajustado).
4. **Energía:** consumo 480 → 600 W; generación 550 W → déficit de 50 W → degradación progresiva.
5. **Científico:** +15 pts ciencia, pero +2 GB de datos/día a transmitir.
6. **Telecomunicaciones:** antena de 2 Mbps → 2 GB en ≈133 min (≈2,2 h) de enlace continuo; con 2 ventanas/día se acumulan datos.
7. **Presupuesto:** saldo −8.000 USD; si quedan 3.000 USD, la decisión se bloquea por presupuesto.
8. **Visual:** la nave gana un módulo lateral (espectrómetro) con indicador de consumo.

El jugador ve la tabla de variables afectadas (masa, energía, delta-v, datos, presupuesto)
y decide si asume el riesgo, sin que el juego anticipe el desastre.

---

## 3. Sistema de eventos

### 3.1 Generación
- No deterministas: dependen de `estado + entorno + ánimo + decisiones previas`.
- `probabilidad_base` modificada por factores (ej.: fuga más probable si el tanque está
  cerca del límite térmico).
- Entorno: terreno lunar helado aumenta probabilidad de que un robot resbale; radiación
  afecta electrónica.
- Ánimo: tripulante con "lluvia" tiene debuff de desconcentración → más tiempo y menor
  calidad en la tarea.

### 3.2 Comunicación al jugador
- Alertas sin cuantificar: "Se detecta una anomalía en el módulo de energía."
- Opción de usar una ventana de comunicación para informar y pedir retroalimentación
  (coste: 1 ventana + energía). No siempre es óptimo.
- Fallos de componentes se comunican por mensajes de alerta.

### 3.3 Estados de ánimo
- Visuales: sol/nube/lluvia sobre la cabeza del tripulante.
- Aparecen de forma aleatoria.
- Afectan velocidad y calidad de tareas.

---

## 4. Evaluación final

### 4.1 Finales ramificados propuestos: 5
Justificación: suficiente variedad narrativa sin sobrecargar el alcance del MVP. Verificables
por combinación de umbrales.

1. **Éxito científico pleno:** objetivos cumplidos, tripulación viva, retorno exitoso.
2. **Supervivencia con misión parcial:** tripulación viva, objetivos incompletos.
3. **Retorno de emergencia:** aborto con datos parciales.
4. **Pérdida de tripulación, datos recuperados:** tripulación muere, datos llegan a Tierra.
5. **Fallo total:** sin retorno ni datos.

### 4.2 Dimensiones de evaluación
Objetivos científicos, supervivencia, tiempo, presupuesto, calidad y transmisión de datos,
estado final de la nave, capacidad de retorno.

### 4.3 Informe final
- Escena con el jefe (oficina desaturada): retroalimentación conversacional por dimensión.
- Si la tripulación murió: silencio total antes del monólogo (rompe la cuarta pared).
- Luego documento de reporte técnico con los datos principales.
- Frase final motivadora o no.

---

## 5. Decisiones de diseño abiertas

1. **Realismo vs jugabilidad:** valores reales de delta-v vs simplificados. Tradeoff:
   educativo vs accesible.
2. **Costes imprevistos:** separar presupuesto financiero de energía; verificar en tránsito
   y en órbita.
3. **Representación gráfica de la nave:** esquemático técnico (barato, claro) vs pixel art
   (más caro, más inmersivo).
4. **Especialidad vs experiencia:** tareas comunes (reparación) las puede hacer cualquiera;
   el especialista es mejor. ¿Un no-especialista puede fallar? (Opción A: nunca, solo más
   lento. Opción B: probabilidad de fallo.)
5. **Accesibilidad (daltonismo):** reforzar color con forma/parpadeo.
6. **Reserva del rojo:** ¿solo para fallos graves o también decoración?
7. **Persistencia en Vercel:** SQLite efímero en `/tmp`. ¿Usar DB gestionada (Postgres/Neon)?

---

## 6. Producto mínimo viable (MVP)

### Fase 1 — Núcleo
Estado de misión + validación + consecuencias. Una misión completa en OTB: definición,
diseño, lanzamiento, retorno. Sin eventos complejos ni tripulación detallada.

### Fase 2 — Mecánica orbital + tripulación
Planificación orbital (delta-v, ventanas). Tripulación (máx. 4, roles, especialidades).
Eventos básicos (fugas, ánimo).

### Fase 3 — Destino Luna + evaluación
Segundo destino. Sistema de eventos completo. Evaluación + 5 finales + informe final.

### Fase 4 — Pulido visual
Pixel art de habitaciones (tecla E). Nave visual esquemática con cambios reflejados.
Música adaptativa.

---

## Preguntas abiertas para el equipo

1. ¿Cuántos tripulantes mínimo para que una misión sea viable? (propuesta: 2 para OTB,
   3 para Luna)
2. ¿Los robots son opcionales en el MVP o se incluyen? (propuesta: opcionales, post-MVP)
3. ¿El presupuesto es global o por etapa? (decidido: global, límite duro)
4. ¿Se permite guardar partida? (propuesta: sí, un slot)
5. ¿El informe final es el único output o también hay ranking? (propuesta: solo informe)