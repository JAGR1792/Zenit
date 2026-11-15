# Estado del proyecto Zenit

Última actualización: 2026-11-15 (rama `dev`).

## Qué funciona

- **Backend (FastAPI + motor puro)**: masa/Tsiolkovsky, energía, comunicaciones, presupuesto como límite duro, eventos, evaluación en 7 dimensiones con finales reactivos (en solitario vs. con dotación) y tope de 3 rondas en `negociar_presupuesto`.
- **Flujo de 10 etapas** con bloqueo de operaciones orbitales mientras la nave sigue en Tierra (etapas 1–5).
- **Menú de inicio** con dificultad (`Cadete`/`Director`/`Comandante`) y guía de 4 pasos.
- **Negociación estilo novela visual** (solo Etapa 2) con el Gato Jefe y 2 ayudantes (+ bono de presupuesto), límite de 3 rondas sin bucle de reinicio infinito y paridad con el modo local offline (`localSimulationFallback.ts`).
- **Sala de Juicio** al final (`BossReportScene.vue`): veredicto del Gato Jefe y sus 2 ayudantes con retratos enmarcados y monólogo de cuarta pared.
- **Cubierta 2D con zonas RPG/novela visual** (`DestinationRooms2D.vue`):
  - Fondos pixel art por sala, ventana con vista de Tierra/Luna y zonas separadas para puertas, estación central y tripulantes estáticos.
  - Ajuste de altura del piso (`--piso`): `1%` en `laboratorio` y `soporte_vital`, `2%` en `sala_sistemas`, y `12%` en `cabina_mando`.
  - Diálogos RPG con tripulantes caninos mediante `[E]`, clic directo sobre el personaje o botón `💬 Bitácora de Mando` en salas en solitario, con retrato `CAPITÁN [TÚ]` y opciones de diagnóstico o acción directa.
- **Contrato de API y pruebas**: especificación OpenAPI en `docs/api-contract.yaml` y batería ampliada de pruebas en backend (`pytest`) y frontend (`Vitest` en `App.test.ts` y `GameComponents.test.ts`).
- **Recursos** organizados en `Pixel-art/` (fuentes) y `frontend/public/sprites/` (uso en el juego).

## Qué falta / siguiente

1. Revisión visual en navegador vivo de la alineación final del perro en cada sala (`laboratorio`, `soporte_vital`, `sala_sistemas`, `cabina_mando`) y de la caja de diálogo RPG.
2. Equilibrio fino de dificultad y costos a partir de partidas completas de prueba.
3. Decisiones abiertas de `docs/implementation-plan.md` §5 (pendientes de definición con el equipo).

## Notas técnicas

- El Gato Jefe usa `/sprites/iconos/icono_gato_jefe.png` (ya no la hoja `GATO.jpeg`).
- La limpieza de fondo de sprites usa relleno por inundación desde los bordes (conserva pelaje blanco).
- La pestaña de Oficina de Planificación solo existe en la Etapa 2.
