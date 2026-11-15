# Estado del proyecto Zenit

Última actualización: 2026-11-15 (rama `dev`).

## Qué funciona

- **Backend (FastAPI + motor puro)**: masa/Tsiolkovsky, energía, comunicaciones, presupuesto como límite duro, eventos, evaluación en 7 dimensiones con finales reactivos (en solitario vs. con dotación). 13 pruebas pytest.
- **Flujo de 10 etapas** con bloqueo de recursos mientras la nave sigue en Tierra.
- **Menú de inicio** con dificultad (Cadete/Director/Comandante) y guía de 4 pasos.
- **Negociación estilo novela visual** (solo Etapa 2) con el Gato Jefe y 2 ayudantes (+ bono de presupuesto).
- **Sala de Juicio** al final: veredicto del jefe y los ayudantes con retratos enmarcados.
- **Cubierta 2D** con fondos pixel art por sala, ventana con vista de Tierra/Luna, perro alineado al piso por sala.
- **Recursos** organizados en `Pixel-art/` (fuentes) y `frontend/public/sprites/` (uso en el juego).

## Qué falta / siguiente

1. Revisión visual en navegador de la alineación del perro en cada sala (valores `piso` en `DestinationRooms2D.vue`).
2. Zonas RPG/novela visual dentro de la nave (diálogos con la tripulación canina).
3. Equilibrio fino de dificultad y costos con partidas reales.
4. Pruebas de frontend: solo hay 2 (App); faltan componentes clave.
5. Actualizar `docs/api-contract.yaml` si se agrega `negociar_presupuesto` al contrato.
6. Decisiones abiertas de `docs/implementation-plan.md` §5.

## Notas técnicas

- El Gato Jefe usa `/sprites/iconos/icono_gato_jefe.png` (ya no la hoja `GATO.jpeg`).
- La limpieza de fondo de sprites usa relleno por inundación desde los bordes (conserva pelaje blanco).
- La pestaña de Oficina de Planificación solo existe en la Etapa 2.
