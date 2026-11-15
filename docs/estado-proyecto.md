# Estado del proyecto Zenit

Última actualización: 2026-11-15 (rama `dev`).

## Qué funciona

- **Backend (FastAPI + motor puro)**: masa/Tsiolkovsky, energía, comunicaciones, presupuesto como límite duro, eventos, evaluación en 7 dimensiones con finales reactivos (en solitario vs. con dotación) y tope de 3 rondas en `negociar_presupuesto`.
- **Flujo de 10 etapas** con bloqueo de operaciones orbitales mientras la nave sigue en Tierra (etapas 1–5).
- **Menú de inicio** con dificultad (`Cadete`/`Director`/`Comandante`) y guía de 4 pasos.
- **Negociación estilo novela visual** (solo Etapa 2, pantalla enfocada sin columna derecha distractora) con 3 escenarios distintos (`Recorte de la Junta`, `Crisis Helios-9`, `Auditoría de Hangar`), fondos pixel art widescreen propios con el Gato Jefe y sus 2 ayudantes (`negociacion_oficina_jefe.jpg`, `negociacion_sala_crisis.jpg`, `negociacion_auditoria_hangar.jpg`), globo de diálogo superior derecho y retrato de `CAPITÁN PERRO`. Las opciones no revelan de antemano cuánto suben o bajan el presupuesto y una mala respuesta recorta fondos; tope de 3 rondas sincronizado con `localSimulationFallback.ts`.
- **Sala de Juicio** al final (`BossReportScene.vue`): mismo formato novela visual widescreen 16:9 (`sala_juicio_tribunal_wide.jpg`) para el veredicto y reflexión de cuarta pared del Gato Jefe y sus 2 ayudantes con retrato de `CAPITÁN PERRO [TÚ]`.
- **Cubierta 2D con zonas RPG/novela visual** (`DestinationRooms2D.vue`):
  - Escenarios 100% de ancho completo (`min-height: 340px`, sin recorte lateral estrecho en `sala_sistemas`/`cabina_v2.png`), ventana con vista de Tierra/Luna y desplazamiento equilibrado del perro director (`0.43`/frame).
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
