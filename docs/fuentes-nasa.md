# Fuentes científicas (NASA) y estado de validación

Este documento registra de dónde sale cada valor físico del catálogo de Zenit, qué se corrigió y
qué queda pendiente de decisión. Los valores se verificaron contra documentos de NASA el 15-nov-2026.

Convención de estado:
- **Validado**: coincide con la fuente.
- **Corregido**: el valor o el nombre anterior no era válido y se reemplazó.
- **Valor de juego**: abstracción deliberada; no pretende ser físico.
- **Pendiente**: requiere una decisión de diseño (ver al final).

## 1. Propulsión

| Componente (id) | Antes | Ahora | Estado | Fuente |
|---|---|---|---|---|
| `motor_monoprop_basico` | "Propulsor Hidracina M-280", Isp 285 s | "Propulsor Monopropelente de Hidracina", Isp 225 s | Corregido | NASA, *State-of-the-Art of Small Spacecraft Technology*, cap. 4: la tabla 4-1 da 180–285 s para hidracina, y el texto indica que los propulsores de ≥1 N rinden típicamente 200–235 s. 285 s está en el extremo del rango, no es un valor típico. |
| `motor_biprop_estandar` | "Tobera Bipropelente Hyper-320", Isp 320 s (nombre inventado) | "Motor Bipropelente MMH/MON-3 (clase OMS-E)", Isp 315 s | Corregido | NASA, *Artemis I Engine Performance* (NTRS 20240003648): OMS-E de Orión, 26,7 kN, Isp 315,1 s, MMH/MON-3. Concuerda con el motor OME del transbordador: 26,7 kN (6.000 lbf) y 314–315 s (NTRS 19910014943). |
| `motor_crio_avanzado` | "Cámara Criogénica Methalox Z-360", Isp 360 s (nombre inventado) | "Motor Criogénico LH2/LOX (clase RL10)", Isp 444 s | Corregido | NASA, *Centaur RL10A-3-3A* (NTRS 20140011176): Isp de vacío 444,4 ± 2,5 s, 16.500 lbf (≈73 kN), LH2/LOX. |

Observaciones:
- Ningún motor del catálogo anterior correspondía a un motor real. El de 360 s "Methalox" tampoco tiene
  respaldo en NASA: el único motor LOX/metano NASA documentado (Morpheus, 4.200 lbf) tiene requisito de
  215 s y las pruebas midieron 150–205 s (NTRS 20110014012).
- Referencia adicional: el SPS de Apolo, 20.000 lbf y Isp 314,5 (NTRS 20100027319).
- La masa (65/80/95 kg) y el propelente (650/795/810 kg) siguen siendo **valores de juego** a escala de
  nave de 1,3 t.
- Efecto en el juego (configuración base, sin instrumentos, tripulación de 1 a 4): hidracina 2.257→2.002 m/s,
  MMH/MON-3 3.487→3.122 m/s, LH2/LOX 4.856→4.362 m/s. El motor criogénico pasa a ser claramente el de mayor margen.

## 2. Energía

| Componente (id) | Antes | Ahora | Estado | Fuente |
|---|---|---|---|---|
| `energia_hibrida_rtg` | "Matriz Solar + Auxiliar Isotópico P-780", 780 W, 85 kg | "Matriz Solar GaAs + MMRTG", 660 W, 90 kg | Corregido | NASA, hoja técnica del MMRTG: 110 W eléctricos al inicio de vida, 45 kg, ≈2.000 W térmicos, vida de diseño 17 años. 550 W (matriz) + 110 W = 660 W; 45 kg + 45 kg = 90 kg. |
| `energia_solar_compacto` | "Si-380" pero generaba 420 W | "Si-420" | Corregido | Inconsistencia interna nombre/valor. |
| `energia_solar_estandar` | "GaAs-550", 550 W | sin cambio | Valor de juego | Relación potencia/masa no verificada con NASA. |

El MMRTG no depende del Sol, pero la parte solar de la matriz sí sufre eclipses; el texto de la ficha
ya no dice "inmune a sombras" para todo el conjunto.

## 2b. Constantes y entorno

| Valor | En el código | Estado | Fuente |
|---|---|---|---|
| Gravedad estándar g₀ | 9,80665 m/s² | Validado | NASA NSSDC, *Earth Fact Sheet* (https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html). |
| Distancia Tierra–Luna | 384.400 km | Validado | NASA, *Moon Facts* (https://science.nasa.gov/moon/facts/) y NSSDC *Moon Fact Sheet* (semieje mayor 384,4 × 10³ km). |
| Fracción de eclipse en OTB | 0,38 | Validado (cota) | Cálculo propio con constantes NASA (R⊕ = 6.378,137 km, GM = 398.600 km³/s²): a 400 km, v = 7,669 km/s, T = 92,6 min y la fracción máxima en sombra es 0,390 (36,1 min). 0,38 es coherente como caso desfavorable. |
| Fracción de eclipse lunar | 0,25 | Valor de juego | No verificada. |
| Shackleton | "Cráter Shackleton" | Corregido (texto) | NASA SVS 4043 (https://svs.gsfc.nasa.gov/4043): el cráter está en sombra permanente. Se aclaró que la energía solar solo es viable en el borde. |

## 3. Telecomunicaciones

| Componente (id) | Antes | Ahora | Estado | Fuente |
|---|---|---|---|---|
| `antena_uhf_basica` | "Omnidireccional Banda-S" (el id dice UHF) | "Antena de Baja Ganancia Banda-S" | Corregido (nombre/descripción) | La banda S del sistema Unified S-band de Apolo daba "seguimiento y comunicaciones a distancia lunar" (NTRS 19670009664), así que el alcance de 1.500 km del catálogo es una abstracción de ganancia, no un límite de la banda. |
| `antena_parabolica_x` | "~2 GB/ventana" | "≈0,9 GB por hora de enlace" | Corregido | Aritmética: 2 Mbps = 0,9 GB/h. 2 GB exigen ≈133 min de enlace continuo. |
| `antena_laser_ka` | "Transceptor Óptico Banda-Ka DeepLink" | "Terminal de Comunicaciones Ópticas (láser infrarrojo)" | Corregido | La banda Ka es radiofrecuencia; las comunicaciones ópticas usan luz infrarroja (NASA, O2O: https://www.nasa.gov/goddard/esc/exploration-and-space-communications-o2o). |

El cálculo del juego (`gb_por_ventana = Mbps × prob × 2,2`) equivale a ventanas de ≈4,9 h, razonable para
pasos de red de espacio profundo, pero no para pasos de estación en OTB. No se modificó para no alterar el balance.

## 4. Pendientes de decisión (no se aplicaron: cambian el balance del juego)

`docs/implementation-plan.md` §5 pide no resolver por cuenta propia las decisiones abiertas de realismo
frente a jugabilidad. Estos puntos son los que siguen sin ser científicamente válidos:

1. **Delta-v de lanzamiento (1.450 m/s).** La nave "asciende" con su propio motor. La velocidad orbital a
   400 km es 7,669 km/s, así que ningún ascenso desde la superficie puede costar 1.450 m/s (la rotación de
   la Tierra aporta como máximo ≈0,46 km/s). Si el lanzador es externo y fijo (decisión ya tomada), el delta-v
   de la nave debería empezar en OTB y esta etapa no debería descontarlo.
2. **Presupuesto de delta-v lunar (3.100 m/s).** Con datos del Apolo 8 (post-launch report, NASA): LOI-1 2.997 ft/s
   (913,5 m/s), LOI-2 134,8 ft/s (41,1 m/s), TEI 3.519 ft/s (1.072,6 m/s) → LOI+TEI ≈ 2.028 m/s. La TLI desde
   400 km calculada con dos cuerpos es ≈3.082 m/s. Total ≈ 5.110 m/s desde OTB, sin descenso ni ascenso
   lunar a Shackleton. Eso exige una razón de masas de ≈3,2 con el motor LH2/LOX y ≈5,2 con MMH/MON-3,
   inalcanzable con las masas actuales.
3. **Masa por tripulante (25 kg).** Resuelto: es una decisión de diseño (los personajes son perritos
   antropomórficos). NASA usa 82 kg para humanos (*Logistics Beyond LEO*, ASCEND 2023). Con 25 kg, los
   consumibles del punto 4 también deberían escalarse a esa masa corporal.
4. **Los consumibles no tienen masa.** NASA: O₂ 0,89 kg, agua de bebida 2,79 kg, +0,50 kg de rehidratación y
   2,39 kg de comida por tripulante-día (≈6,57 kg/día). Los módulos de 18/32/48 días-persona cargarían
   ≈118/210/315 kg de consumibles, y su masa es 35/50/75 kg.
5. **Capacidad de lanzamiento (1.300 kg).** Orión (4 tripulantes, hasta 21 días) tiene una masa bruta de
   lanzamiento de 78.000 lb (≈35 t) según NASA (https://www.nasa.gov/orion-overview/).
6. **Tasa del enlace óptico (4,5 Mbps).** NASA demostró hasta 260 Mbps con O2O en Artemis II. Usar el valor real
   eliminaría el cuello de botella de datos, que es una mecánica del juego.
7. **Tránsito rápido a la Luna (2 días).** Las fuentes consultadas no respaldan 2 días: en el Apolo 8 pasaron
   más de 58 h entre la TLI (GET 2:56) y la segunda corrección (GET 61:00) (NASA SP-4029, *Translunar Phase*).
8. **Presupuestos de 95.000–155.000 Créditos Zenit (CZ).** Moneda ficticia y escala de juego propia de Zenit, sin relación con costes reales en dólares.

## 5. Lista de fuentes

- NASA NTRS 20240003648, *Artemis I Engine Performance*: https://ntrs.nasa.gov/api/citations/20240003648/downloads/382_BELAIR_ARTEMIS_I_ENGINE_PERFORMANCE_FINAL.pdf
- NASA NTRS 19910014943, motor OME del transbordador: https://ntrs.nasa.gov/api/citations/19910014943/downloads/19910014943.pdf
- NASA NTRS 20100027319, SPS de Apolo: https://ntrs.nasa.gov/citations/20100027319
- NASA NTRS 20140011176, RL10 de Centaur: https://ntrs.nasa.gov/api/citations/20140011176/downloads/20140011176.pdf
- NASA NTRS 20110014012, Project Morpheus (LOX/metano): https://ntrs.nasa.gov/api/citations/20110014012/downloads/20110014012.pdf
- NASA, *State-of-the-Art of Small Spacecraft Technology*, propulsión: https://www.nasa.gov/smallsat-institute/sst-soa/in-space_propulsion
- NASA, hoja técnica del MMRTG: https://science.nasa.gov/wp-content/uploads/2024/02/mmrtg-factsheet-updated-5-18-20-1.pdf
- NASA NSSDC, Earth Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html
- NASA NSSDC, Moon Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
- NASA, Moon Facts: https://science.nasa.gov/moon/facts/
- NASA, Apollo 8 post-launch report: https://www.nasa.gov/wp-content/uploads/static/history/afj/ap08fj/pdf/a08-postlaunch-rep.pdf
- NASA SP-4029, Apollo 8 Translunar Phase: https://www.nasa.gov/wp-content/uploads/static/history/SP-4029/Apollo_08f_Translunar_Phase.htm
- NASA, O2O (Orion Artemis II Optical Communications System): https://www.nasa.gov/goddard/esc/exploration-and-space-communications-o2o
- NASA NTRS 19670009664, Unified S-band: https://ntrs.nasa.gov/citations/19670009664
- NASA, *Logistics Beyond LEO* (ASCEND 2023): https://ntrs.nasa.gov/api/citations/20230013896/downloads/Logistics_BeyondLEO-ASCEND2023-Pres.pdf
- NASA, Orion overview: https://www.nasa.gov/orion-overview/
- NASA SVS 4043, LRO y regiones en sombra permanente: https://svs.gsfc.nasa.gov/4043
