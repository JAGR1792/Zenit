# AGENTS.md - Guía para Agentes de IA en Zenit (Simulador narrativo de misiones espaciales)

Este archivo define las reglas de colaboración, estructura y comandos para agentes de IA
(Claude, Cursor, Copilot, OpenCode, etc.) que trabajen en **Zenit**, un simulador narrativo
de misiones espaciales educativo.

Los agentes de IA **DEBEN** leer, respetar y adherirse estrictamente a todas las instrucciones,
estándares y restricciones de flujo de trabajo descritas a continuación.

---

## 0. Contexto del proyecto (LEER PRIMERO)

**Proyecto actual:** Zenit — Simulador narrativo de misiones espaciales (juego serio educativo).
El jugador es director de una misión espacial tripulada y debe planificar, diseñar, ejecutar
y evaluar una expedición científica. Experiencia principalmente textual/narrativa, apoyada
por visualizaciones y pixel art de habitaciones.

**Documentos de referencia obligatorios (leer antes de codear):**
- `docs/implementation-plan.md` — arquitectura técnica y plan de implementación.
- `docs/game-design.md` — documento de diseño del juego (experiencia, sistemas, evaluación).
- `artboard.html` — dirección de arte (paleta, tipografía, boceto de cabina).
- `vercel.json` — infraestructura de despliegue multi-service.

**Estado actual del repo:** MVP en fase 0 (hello world). Backend FastAPI + frontend Vue/Vite,
desplegado en Vercel como proyecto multi-service. No hay aún lógica de juego.

**Decisiones clave ya tomadas:**
- Múltiples finales: ruta lineal con finales ramificados según decisiones clave.
- MVP: un solo tipo de misión (exploración científica), dos destinos (OTB y Luna).
- Presupuesto global como límite duro, costes de ejecución descontados en tiempo real.
- Capacidad de lanzamiento fija (masa máxima), independiente del proveedor.
- Catálogo de componentes con ficha técnica visible, sin avisos de incompatibilidad.
- Interfaz de gestión de recursos en destino: vista 2D pixel art, habitaciones contiguas,
  interacción con tecla "e".

**Decisiones abiertas** (ver `docs/implementation-plan.md` §5): realismo vs jugabilidad,
costes imprevistos, representación gráfica de la nave, especialidad vs experiencia, etc.
No resolverlas por cuenta propia; plantear opciones y preguntar.

---

## 1. Descripción General

**Proyecto:** Zenit — simulador narrativo de misiones espaciales educativo (director de misión).

**Stack tecnológico:**
- **Frontend:** Vue 3 + TypeScript, Vite, Tailwind CSS, Three.js
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, NumPy
- **Pruebas:** Pytest (backend), Vitest (frontend)
- **Contenedores:** Docker Compose

**Arquitectura:** monolito modular. El motor de simulación (`backend/app/simulation/`) es un
paquete Python puro, independiente de FastAPI, frontend y base de datos.

---

## 2. Reglas de Colaboración Multi-Agente

### 2.1 Ramificación Aislada
- **NUNCA** commitear directamente a `main` ni a `dev`.
- Crear rama: `agent/<nombre-agente>/<caracteristica>`
  - Ejemplo: `agent/claude/mass-model`, `agent/opencode/frontend-view`
- `dev` integra, `main` solo entregas.

### 2.2 Commits Atómicos
- Un commit = un cambio lógico completo. Nada de `wip`.
- Mensaje convencional: `tipo(scope): descripción`
  - `feat(simulation): agregar modelo de masa con margen`
  - `fix(api): corregir validación de misión`
  - `test(mass): agregar caso de masa que excede capacidad`
  - Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`

### 2.3 Sincronización de Documentación (CACM)
**OBLIGATORIO:** al modificar código, actualizar en la misma tarea:
- `docs/decisiones.md` (si existe) o `docs/architecture.md` / `docs/domain-model.md`
- Docstrings en código (Google style en Python, JSDoc/TSDoc en TS)
- `README.md` si hay cambios en setup/arquitectura
- `docs/simulation-spec.md` si cambian fórmulas o unidades
- `docs/api-contract.yaml` si cambian endpoints

No dejar "se actualiza después".

### 2.4 No Reescritura Masiva
- Respetar estilo existente (type hints, docstrings, nomenclatura en español).
- Cambios incrementales, no refactors completos sin solicitar.

### 2.5 Coordinación de Bloqueos
- Al editar archivos, verificar si otro agente cambió el mismo archivo recientemente.
- Coordinar con los operadores humanos si los cambios en paralelo se superponen.

---

## 3. Entorno y Comandos Estándar

### Backend
```bash
cd backend

# Crear/activar entorno virtual (OBLIGATORIO)
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API (puerto 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
pytest -v

# Lint y formato (si se configura ruff)
ruff check .
ruff format .
```

### Frontend
```bash
cd frontend

npm install

# Desarrollo (puerto 5173)
npm run dev

# Build producción
npm run build

# Preview build
npm run preview

# Tests
npm test
```

### Docker
```bash
docker-compose up --build
```

---

## 4. Descubrimiento de Contexto (Leer ANTES de codear)

### 4.1 Documentación del Proyecto
| Archivo | Qué contiene |
|---------|--------------|
| `README.md` | Objetivos, stack, cómo arrancar |
| `docs/architecture.md` | Arquitectura lógica |
| `docs/domain-model.md` | Entidades de dominio |
| `docs/api-contract.yaml` | Contrato de API |
| `docs/simulation-spec.md` | Especificación del motor de simulación |
| `plan_stack_space_mission.md` (externo) | Plan técnico completo |

### 4.2 Estructura de Código Backend
```
backend/app/
├── main.py                 # FastAPI app, lifespan, init_db
├── api/v1.py               # Endpoints REST
├── schemas/mission.py      # Pydantic schemas
├── models/db.py            # SQLAlchemy engine/session
├── models/orm.py           # ORM models
├── services/mission_service.py  # Lógica de aplicación
├── repositories/data.py    # Acceso a datos + seed
├── repositories/seed.py    # Datos semilla
└── simulation/             # Motor puro: mass, power, communications, budget, orbit, evaluator
```

### 4.3 Estructura de Código Frontend
```
frontend/src/
├── main.ts, App.vue
├── views/MissionView.vue
├── services/api.ts
├── components/, composables/, stores/, three/
```

### 4.4 Tests
- Backend: `backend/tests/` (pytest). Al menos una prueba por regla crítica.
- Frontend: `frontend/src/**/*.test.ts` (Vitest).

---

## 5. Estilo de Código

### Python (Backend)
- **Type hints obligatorios** en funciones públicas.
- **Docstrings Google style** (args, returns, raises, example).
- **Nombres en español** (clases, funciones, variables) cuando sea natural.
- **Validación Pydantic** en modelos de datos y schemas.
- **Excepciones personalizadas** heredando de una base propia si aplica.
- **Logging estructurado**; no usar `print()` en producción.
- **Motor de simulación puro**: sin dependencias de FastAPI/DB/frontend.

### TypeScript/Vue (Frontend)
- **Composition API** con `<script setup>`.
- **Composables** para lógica reactiva.
- **Tipado estricto** (`strict: true` en tsconfig).
- **Componentes atómicos** y reutilizables.

---

## 6. Gestión de Dependencias
- Backend: `requirements.txt` con versiones fijadas con `==`. Actualizar tras `pip install`.
- Frontend: `package.json`. Usar lockfile.

---

## 7. Guardrails (Límites Estrictos)

1. **NO** commitear secretos (`.env`, keys), `node_modules/`, `.venv/`, `__pycache__/`, `*.db`.
2. **NO** usar `print()` para logs en producción.
3. **NO** mezclar lógica de simulación con lógica de API — capas separadas.
4. **NO** afirmar que una animación visual es simulación física de alta fidelidad.
5. **NO** integrar GMAT ni APIs externas no documentadas en el MVP.
6. **SÍ** validar entrada en API con Pydantic.
7. **SÍ** manejar errores con códigos HTTP apropiados (404, 422, 500).
8. **SÍ** escribir test ANTES o JUNTO con código (TDD ligero).
9. **SÍ** mantener el motor de simulación ejecutable directamente desde Python.

---

## 8. Protocolo CACM (Mantenimiento Continuo)

Al terminar cada tarea:
1. Ejecutar tests: `pytest` (backend) y `npm test` (frontend).
2. Ejecutar lint/format si está configurado.
3. Verificar docs sincronizadas.
4. Actualizar documentación con: qué se hizo, por qué (trade-offs), qué sigue.
5. Commit atómico con mensaje convencional.

El incumplimiento de mantener la documentación sincronizada con el código base
se considera una regresión de ingeniería.

---

## 9. Flujo de Trabajo Típico

```
Leer docs/ + plan → Crear/ajustar modelos y schemas → Implementar servicio/repositorio
→ Implementar endpoint → Actualizar frontend → Tests → Actualizar docs → Commit + Push rama agent/...
```