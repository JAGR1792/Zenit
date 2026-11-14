# Guía de Contribución — Space Mission Design Game

Gracias por tu interés en contribuir. Esta guía explica cómo está organizado el proyecto,
cómo escribir código aceptable y cómo navegar la documentación.

## Estructura del repositorio

```
MDGN/
├── frontend/          # Vue 3 + TS + Vite + Tailwind
├── backend/           # FastAPI + simulación
│   ├── app/
│   └── tests/
├── docs/              # Arquitectura, dominio, API, simulación
├── docker-compose.yml
└── README.md
```

**Regla de oro:** el motor de simulación (`backend/app/simulation/`) NO puede depender
de FastAPI, frontend ni base de datos. Debe compilarse y testearse de forma aislada.

## Cómo empezar a contribuir

1. Leer `README.md` y `docs/`.
2. Crear rama: `git checkout -b contribucion/tu-funcionalidad` (o `agent/<nombre>/<tema>`).
3. Hacer cambios + tests.
4. Verificar calidad:
   - Backend: `cd backend && pytest -v`
   - Frontend: `cd frontend && npm run build && npm test`
5. Commit con Conventional Commits en español: `tipo(alcance): descripción corta`.
6. Push y Pull Request.

## Estándares de código

### Python (Backend)
- Type hints obligatorios en funciones públicas.
- Docstrings Google style.
- Nombres en español cuando sea natural.
- Validación con Pydantic.
- Sin `print()` en producción; usar logging.

### TypeScript / Vue (Frontend)
- Composition API con `<script setup>`.
- Tipado estricto.
- Componentes atómicos.

## Documentación obligatoria

Todo código nuevo DEBE incluir:
1. Doc comment en la función.
2. Entrada en `docs/` si es una decisión de diseño nueva.
3. Test que demuestre el comportamiento correcto.

## Tests

- Backend: `backend/tests/` (pytest). Al menos una prueba por regla crítica.
- Frontend: `frontend/src/**/*.test.ts` (Vitest).

## Convención de commits

Conventional Commits en español:
```
tipo(alcance): descripción corta en español
```
Ejemplos:
```
feat(simulation): agregar modelo de potencia con déficit de energía
fix(api): corregir timeout en validación de misión
docs(simulation-spec): explicar modelo de comunicaciones
```

## Proceso de revisión

1. Abres un PR con descripción clara.
2. CI corre automáticamente (tests, build).
3. Un revisor revisa el código.
4. Se aprueba o se piden cambios.
5. Se mergea a `main`.

Gracias por contribuir a Space Mission Design Game.