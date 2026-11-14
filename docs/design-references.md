# Zenit — Referencias de diseño frontend (de otros repos del equipo)

Documento para compartir con el equipo y con agentes que acepten imágenes. Resume patrones
visuales reutilizables tomados de repositorios del mismo autor.

## 1. Persona3-website (React + Vite) — estética Persona 3
Patrones destacables (`src/App.css`):
- **Glassmorphism con clip-path angular:** paneles con `background: rgba(7,8,24,0.82)`,
  `border: 1px solid rgba(255,255,255,0.2)`, `backdrop-filter: blur(2px)` y
  `clip-path: polygon(0 0, 100% 0, calc(100% - 10px) 100%, 0 100%)` (esquinas cortadas).
- **Botones con clip-path y hover con lift:** `transform: translateY(-1px)` al hover.
- **Acento de color fuerte** (rojo `#ca1c38`) sobre fondos oscuros, con estados `.on` que
  cambian fondo completo.
- **Sliders estilizados** con `accent-color`.

Aplicable a Zenit: paneles de misión y botones de decisión pueden usar clip-path angular
y glassmorphism para reforzar el retrofuturismo.

## 2. WB_CUENTAS (Astro + Tailwind) — tokens y micro-interacciones
Patrones destacables (`src/styles/global.css`):
- **Tokens CSS:** `--radio`, `--sombra`, colores semánticos por estado (pagada/proxima/vencida).
- **Acordeón inline:** `.surco` con `grid-template-columns`, chevron que rota 180° al abrir,
  borde izquierdo que cambia de color según estado.
- **Indicador de estado circular:** `::before` con color por estado y animación `latido`
  (pulso de box-shadow) para urgencia.
- **Accesibilidad:** `:focus-visible` con outline de 3px, `prefers-reduced-motion` para
  desactivar animaciones.
- **Sub-pestañas** tipo pill con `aria-selected`.

Aplicable a Zenit: estados de misión (nominal/advertencia/grave) pueden usar puntos de color
con animación de pulso; accesibilidad desde el inicio.

## 3. Zenit (actual) — paleta y estilo base
- Paleta Dirección A (ver `artboard.html`): vacío `#0B0E1A`, cabina `#1B2340`, acero
  `#3A4666`, ámbar fósforo `#FFB000`, oro `#F5D36B`, cian `#4FD1C5`, verde `#7BD88F`,
  naranja `#FF7A3D`, rojo `#E5484D`, lila `#6B5B95`.
- Tipografía: IBM Plex Mono (datos) + Source Serif 4 (narrativa).
- Efectos: scanlines CRT, viñeta, glow en títulos/botones (añadidos en `style.css`).

## 4. Sugerencias de mejora visual para el otro agente
1. Aplicar **clip-path angular** a paneles y botones (estilo Persona 3) para alejarse del
   rectángulo genérico.
2. Usar **glassmorphism** (`backdrop-filter: blur`) en overlays y terminales de habitación.
3. Añadir **indicadores de estado con pulso** (latido) para alertas graves.
4. Mantener **accesibilidad**: `prefers-reduced-motion`, `:focus-visible`, contraste suficiente.
5. Sprites: mantener spritesheet para runtime + extraer PNGs individuales + manifiesto JSON.
6. Iconos de ánimo ya corregidos (☀ ☁ 🌧).

## 5. Petición al agente con capacidad de imágenes
Si el agente acepta imágenes, pedirle que:
- Genere mockups de la cabina de mando y una habitación (laboratorio) aplicando la paleta
  Dirección A con los patrones anteriores.
- Proponga un sprite de tripulante (16×16 o 32×32) y su animación de caminar (4-6 frames).
- Valide el contraste y legibilidad de alertas sin cuantificar (naranja ambiguo).
- Entregue los assets como PNG con fondo transparente + manifiesto de coordenadas.
