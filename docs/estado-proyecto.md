# Estado del proyecto Zenit

Última actualización: 2026-11-15 (rama `dev`).

## Qué funciona

- **Backend (FastAPI + motor puro)**: masa/Tsiolkovsky, energía, comunicaciones, presupuesto como límite duro, eventos, evaluación en 7 dimensiones con finales reactivos (en solitario vs. con dotación) y tope de 3 rondas en `negociar_presupuesto`.
- **Flujo de 10 etapas** con bloqueo de operaciones orbitales mientras la nave sigue en Tierra (etapas 1–5).
- **Menú principal estilo videojuego** (`GameMainMenu.vue`): portada a pantalla completa con ilustración pixel art propia (`/sprites/escenas/menu_principal_bg.jpg`: Tierra, nave Zenit, perro astronauta EVA y Luna), logotipo superior **ZENIT** y marco metálico central flotante (`data-tutorial="menu"`) con navegación por submenús (`Continuar Expedición`, `Nueva Expedición` sin dificultad preseleccionada, `Cómo Jugar`, `Tripulación y Comité` y `Créditos y Fuentes`).
- **Tutorial reactivo interactivo por etapa** (`TutorialOverlay.vue` + `MissionView.vue`): overlay spotlight **no bloqueante** (`pointer-events: none` en máscara y anillo de enfoque, `pointer-events: auto` solo en la tarjeta flotante) que permite jugar y hacer clic en los controles mientras acompaña las etapas 1–10 automáticamente en la primera partida (`zenit_tutorial_activo !== '0'`), reacciona al cambio de etapa/paso/redimensionamiento sin bucles de `MutationObserver`, respeta la prioridad de selectores separados por coma, mantiene la tarjeta dentro del viewport y permite navegar (`← Anterior` / `Siguiente →`), ocultar la etapa (`✕` / `Esc`), reabrir con `AYUDA / TUTORIAL` o desactivar permanentemente (`No mostrar más`).
- **Decisiones limpias sin guías ni preselecciones forzadas** (`MissionView.vue`): retirado el banner superior `.stage-guide-banner` en favor de un tutorial dedicado posterior, y eliminada la preselección visual por defecto de destino (Etapa 1) y trayectoria (Etapa 4).
- **Negociación estilo novela visual** (`VisualNovelNegotiation.vue`, solo Etapa 2, pantalla enfocada sin columna derecha distractora) con 3 escenarios distintos (`Recorte de la Junta`, `Crisis Helios-9`, `Auditoría de Hangar`): usa `escena_inicial.jpg` como fondo predeterminado con globo anclado inferior y sprites animados `gatoJefe1.png`–`gatoJefe5.png` (junto con `negociacion_sala_crisis.jpg` y `negociacion_auditoria_hangar.jpg`) y retrato de `CAPITÁN PERRO`. Las opciones no revelan de antemano cuánto suben o bajan el presupuesto y una mala respuesta recorta fondos; tope de 3 rondas sincronizado con `localSimulationFallback.ts`.
- **Evaluación final estilo novela visual** (`BossReportScene.vue`): vista widescreen 16:9 con selector entre `Comité Zenit` (`escena_final.jpg` con Gato Jefe naranja parpadeando) y `Sala de Juicio` (`sala_juicio_tribunal_wide.jpg`) para el veredicto y reflexión de cuarta pared de los 3 gatos con retrato de `CAPITÁN PERRO [TÚ]`.
- **Esquema de la nave en Diseño** (`ShipSchematic.vue`): integra la ilustración pixel art oficial `/sprites/escenarios/nave/nave.png` con los 4 módulos transversales sincronizada con las zonas de carga útil, antena, motores y escudo ECLSS.
- **Cuadro de diálogo estilo Undertale (máquina de escribir)** (`TypewriterText.vue` + `useTypewriter.ts`): las letras aparecen una a una en negociaciones, juicio y diálogos RPG, con "blip" de sonido por carácter (Web Audio API) y clic/Espacio/Enter para saltar la animación. Las opciones de respuesta se bloquean hasta que el orador termina de hablar. Integrado en `VisualNovelNegotiation`, `BossReportScene`, `DestinationRooms2D` y la crónica narrativa de `MissionView`.
- **Dificultad en negociación**: el selector de dificultad limita los escenarios disponibles (Cadete solo "Recorte de la Junta" y "Revisión de Costes") y muestra la dificultad activa; los bonos se multiplican según dificultad en el motor local. En difícil se ocultan las pistas de consecuencia.
- **Cuarto escenario de negociación**: "Revisión de Costes y Redundancias" con 3 rondas sobre redundancia, masa viva y eficiencia integral (opciones con trade-offs menos obvias).
- **Pistas pedagógicas**: cada opción de negociación muestra una línea de "Consecuencia posible" (sin revelar montos), que en modo difícil se oculta.
- **Coherencia en el informe final**: detección de ineficiencias (motor criogénico excesivo en OTB, instrumentos sin especialista afín, robot comprado sin generar datos) y nuevo final "Final 1B — Éxito con Ineficiencias" con diálogo y recomendaciones específicas.
- **Cubierta 2D con zonas RPG/novela visual** (`DestinationRooms2D.vue`):
  - Escenarios 100% de ancho completo (`min-height: 340px`, reemplazando `cabina_v2.png` por `sala_sistemas.jpg` panorámica `1331x544`), ventana con vista de Tierra/Luna y desplazamiento equilibrado del perro director (`0.43`/frame).
  - Ajuste de altura del piso (`--piso`): `1%` en `laboratorio`, `soporte_vital` y `sala_sistemas`, y `12%` en `cabina_mando`.
  - Diálogos RPG con tripulantes caninos mediante `[E]`, clic directo sobre el personaje o botón `💬 Bitácora de Mando` en salas en solitario, con retrato `CAPITÁN [TÚ]` y opciones de diagnóstico o acción directa.
- **Contrato de API y pruebas**: especificación OpenAPI en `docs/api-contract.yaml` y batería ampliada de pruebas en backend (`pytest`), frontend (`Vitest` en `App.test.ts` y `GameComponents.test.ts`, incluyendo pruebas de `TutorialOverlay`) y verificación E2E en navegador headless con Playwright/Edge.
- **Recursos** organizados en `Pixel-art/` (fuentes) y `frontend/public/sprites/` (uso en el juego).

## Qué falta / siguiente

1. Revisión visual en navegador vivo de la alineación final del perro en cada sala (`laboratorio`, `soporte_vital`, `sala_sistemas`, `cabina_mando`) y de la caja de diálogo RPG.
2. Equilibrio fino de dificultad y costos a partir de partidas completas de prueba.
3. Decisiones abiertas de `docs/implementation-plan.md` §5 (pendientes de definición con el equipo).

## Notas técnicas

- **Moneda ficticia**: toda la interfaz, bitácoras y evaluaciones muestran **Créditos Zenit (`CZ`)** en lugar de dólares reales (`USD`), manteniendo internamente los identificadores técnicos `*_usd` en los modelos JSON/Pydantic para preservar compatibilidad de API y base de datos.
- El Gato Jefe usa `/sprites/iconos/icono_gato_jefe_naranja.jpg` y `gatoJefe1.png`–`gatoJefe5.png` en las escenas oficiales (`Comité Zenit` y `escena_inicial`), y `/sprites/iconos/icono_gato_jefe.png` en los fondos alternos (ya no la hoja `GATO.jpeg`).
- La limpieza de fondo de sprites usa relleno por inundación desde los bordes (conserva pelaje blanco).
- La pestaña de Oficina de Planificación solo existe en la Etapa 2.
