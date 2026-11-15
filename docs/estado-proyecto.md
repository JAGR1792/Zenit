# Estado del proyecto Zenit

Última actualización: 2026-11-15 (rama `dev`).

## Qué funciona

- **Backend (FastAPI + motor puro)**: masa/Tsiolkovsky, energía, comunicaciones, presupuesto como límite duro, eventos, evaluación en 7 dimensiones con finales reactivos (en solitario vs. con dotación) y tope de 3 rondas en `negociar_presupuesto`.
- **Flujo de 10 etapas** con bloqueo de operaciones orbitales mientras la nave sigue en Tierra (etapas 1–5).
- **Menú de inicio** con dificultad (`Cadete`/`Director`/`Comandante`) y guía de 4 pasos.
- **Negociación estilo novela visual** (`VisualNovelNegotiation.vue`, solo Etapa 2, pantalla enfocada sin columna derecha distractora) con 3 escenarios distintos (`Recorte de la Junta`, `Crisis Helios-9`, `Auditoría de Hangar`): usa `escena_inicial.jpg` como fondo predeterminado con globo anclado inferior y sprites animados `gatoJefe1.png`–`gatoJefe5.png` (junto con `negociacion_sala_crisis.jpg` y `negociacion_auditoria_hangar.jpg`) y retrato de `CAPITÁN PERRO`. Las opciones no revelan de antemano cuánto suben o bajan el presupuesto y una mala respuesta recorta fondos; tope de 3 rondas sincronizado con `localSimulationFallback.ts`.
- **Evaluación final estilo novela visual** (`BossReportScene.vue`): vista widescreen 16:9 con selector entre `Comité Zenit` (`escena_final.jpg` con Gato Jefe naranja parpadeando) y `Sala de Juicio` (`sala_juicio_tribunal_wide.jpg`) para el veredicto y reflexión de cuarta pared de los 3 gatos con retrato de `CAPITÁN PERRO [TÚ]`.
- **Esquema de la nave en Diseño** (`ShipSchematic.vue`): integra la ilustración pixel art oficial `/sprites/escenarios/nave/nave.png` con los 4 módulos transversales sincronizada con las zonas de carga útil, antena, motores y escudo ECLSS.
- **Cuadro de diálogo estilo Undertale (máquina de escribir)** (`TypewriterText.vue` + `useTypewriter.ts`): las letras aparecen una a una en negociaciones, juicio y diálogos RPG, con "blip" de sonido por carácter (Web Audio API) y clic/Espacio/Enter para saltar la animación. Integrado en `VisualNovelNegotiation`, `BossReportScene`, `DestinationRooms2D` y la crónica narrativa de `MissionView`.
- **Cubierta 2D con zonas RPG/novela visual** (`DestinationRooms2D.vue`):
  - Escenarios 100% de ancho completo (`min-height: 340px`, reemplazando `cabina_v2.png` por `sala_sistemas.jpg` panorámica `1331x544`), ventana con vista de Tierra/Luna y desplazamiento equilibrado del perro director (`0.43`/frame).
  - Ajuste de altura del piso (`--piso`): `1%` en `laboratorio`, `soporte_vital` y `sala_sistemas`, y `12%` en `cabina_mando`.
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
