# Diseño de misiones científicas NASA (resumen para Zenit)

Resumen de los documentos PDF aportados por el equipo (NASA, 2025) y su relación con
Zenit. Fuentes:
- `13-3547_A1b.pdf` — *Space Mission Concept Development Using Concept Maturity Levels* (JPL, CML).
- `250323-design-and-develop-science-mission.pdf` — *Design and Develop Science Missions* (NASA SMD webinar, 26-mar-2025).

## 1. Proceso de alto nivel (NASA)
Para diseñar y desarrollar una misión científica se sigue una secuencia:
1. **Identificar necesidad y objetivos** (Need & Goals).
2. **Definir el concepto** (Concept).
3. **Definir requisitos** (Requirements).
4. **Diseñar** (Design).
5. **Construir y verificar** (Build & Verify).
6. **Implementar** (Implement).

Mapeo a Zenit (etapas 1–10):
| Paso NASA | Etapas Zenit |
|---|---|
| Necesidad y objetivos | Etapa 1 (definición de misión) + trama Helios-9 |
| Concepto | Etapa 2 (negociación de financiación) |
| Requisitos | Etapa 3 (diseño de nave y tripulación) |
| Diseño | Etapa 4 (planificación orbital) |
| Construir y verificar | Etapa 5 (lanzamiento) |
| Implementar / operar | Etapas 6–9 (tránsito, ciencia, tripulación, comunicaciones) |
| Evaluación final | Etapa 10 (Sala de Juicio) |

## 2. Segmentos de una misión (NASA SMD)
Toda misión científica se descompone en segmentos:
- **Lanzamiento**: vehículo y servicios para poner la nave en órbita.
- **Espacial (space segment)**: nave y componentes (orbitadores, landers, rovers, instrumentos) que recolectan datos.
- **Tierra (ground segment)**: estaciones y centro de control que comunican, reciben datos y gestionan la misión.
- **Usuario (user segment)**: científicos y público que usan los datos para investigación y educación.

Zenit ya modela estos segmentos: lanzamiento (Etapa 5), espacio (nave y laboratorio), tierra (comunicaciones/antena) y usuario (informe final y evaluación).

## 3. Concept of Operations (ConOps)
Según NPR 7123.1, el ConOps describe de forma secuenciada cómo se usará el sistema para
cumplir las expectativas de los stakeholders. Sirve para:
- Facilitar la comprensión de los objetivos del sistema.
- Estimular el desarrollo de requisitos y arquitectura.
- Servir de base para documentos posteriores.
- Proporcionar criterios de validación.

Principio clave: **“begin with the end in mind”** — primero se define qué dato/publicación se necesita
y a partir de ahí se derivan requisitos (cantidad y calidad de muestras, masa, volumen, etc.).

Aplicación a Zenit: la misión Helios-9 y el informe final (Etapa 10) son el “fin”; las etapas
anteriores derivan de esa meta.

## 4. Concept Maturity Levels (CML) — JPL
Los CML miden la madurez de un concepto de misión en Pre-Fase A. Niveles 1–9:
- **CML 1 — Cocktail napkin**: objetivos científicos articulados, observaciones propuestas, boceto rudimentario.
- **CML 2 — Initial feasibility**: objetivos de bajo nivel, parámetros clave cuantificados, cálculos de primer orden.
- **CML 3 — Trade space**: exploración de arquitecturas (nave, tierra, diseño orbital) y relación ciencia/coste/riesgo.
- **CML 4 — Point design**: diseño específico con márgenes y reservas aceptables; trades de subsistemas.
- **CML 5 — Baseline concept**: enfoque de implementación, socios, contratación, coste y calendario (nivel para Step 1 / MCR).
- **CML 6 — Integrated concept**: detalles técnicos/gestión/coste documentados (Step 2 CSR).
- **CML 7–9**: preliminar/implementación/PDR/CDR.

El CML se organiza en una matriz de 24 filas (ciencia, técnica, gestión, coste y “otros”) y
checklists por nivel. Una misión se considera en un CML si ≥80 % de los atributos están
completados (verde), aplicando juicio de ingeniería.

Uso en JPL: CMLs 1–3 por el A-Team (ideas abiertas, factibilidad, trade space); CML 4 por Team X
(point design).

## 5. Ejemplos de misiones científicas (NASA)
PUNCH, PILOT, Dawn, Mars Moon Sampler (Phobos/Deimos), SLS, Artemis. Zenit se inspira en
misiones de ciencia espacial (Helios-9, OTB 400 km, Cráter Shackleton).

## 6. Relación con el realismo de Zenit
Los valores del catálogo de Zenit se contrastaron con fuentes NASA (ver `docs/fuentes-nasa.md`).
Los pendientes de decisión (delta-v de lanzamiento, consumibles, capacidad de lanzamiento, etc.)
son decisiones de diseño: pueden ajustarse para mayor realismo educativo, pero cambian el balance.

## 7. Ideas para el juego (educativas)
- Mostrar el “segmento” activo (lanzamiento/espacio/tierra/usuario) en cada etapa.
- Añadir una “madurez del concepto” (CML simplificado) que sube con cada etapa completada.
- Incluir un “ConOps” como texto de misión (ya existe la crónica narrativa por etapa).
- En el informe final, evaluar por dimensiones alineadas con NASA (ciencia, técnica, gestión, coste, “otros”).
- Usar “begin with the end in mind”: el objetivo científico (Helios-9) guía todas las decisiones.

## Referencias
- NASA System Engineering Handbook SP-2016-6105 (Rev 2); NPR 7123.1; NPR 7120.5; NPR 7120.8; NPR 8705.4.
- NASA Science Mission Directorate: https://science.nasa.gov/learn/
- NTRS 20210021839, System Engineering Curriculum Intro.
- Wessen et al., JPL, *Space Mission Concept Development Using Concept Maturity Levels* (CML 1–4).