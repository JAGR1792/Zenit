# Fuentes científicas (NASA) y estado de validación

Este documento registra de dónde sale cada valor físico del catálogo de Zenit, qué se corrigió y
qué queda como aproximación o pendiente. Los valores se verificaron contra documentos de NASA el 15-nov-2026.

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
| Fracción de eclipse lunar | 0,25 | Valor de juego (dentro de la cota) | Cálculo propio con el radio lunar medio de NASA NSSDC (1.737,4 km): a 100 km de altitud la sombra máxima es asin(R/r)/π = 0,394 (46,5 min de un periodo de 117,8 min). La fracción real depende de la órbita, la estación y el ángulo beta (puede ser 0 en órbitas casi terminador). Prueba: `test_fraccion_eclipse_lunar_no_supera_el_maximo_teorico`. |
| Autonomía en eclipse | capacidad ÷ potencia neta | Corregido | En eclipse los paneles no generan: la batería cubre el consumo completo (menos el MMRTG, 110 W). Antes se multiplicaba el consumo por la fracción de eclipse, sobreestimando la autonomía. La fracción dice cuánto dura la sombra por órbita, no cuánta potencia se demanda. |
| Shackleton | "Cráter Shackleton" | Corregido (texto) | NASA SVS 4043 (https://svs.gsfc.nasa.gov/4043): el cráter está en sombra permanente. Se aclaró que la energía solar solo es viable en el borde. |

## 3. Telecomunicaciones

| Componente (id) | Antes | Ahora | Estado | Fuente |
|---|---|---|---|---|
| `antena_uhf_basica` | "Omnidireccional Banda-S" (el id dice UHF) | "Antena de Baja Ganancia Banda-S" | Corregido (nombre/descripción) | La banda S del sistema Unified S-band de Apolo daba "seguimiento y comunicaciones a distancia lunar" (NTRS 19670009664), así que el alcance de 1.500 km del catálogo es una abstracción de ganancia, no un límite de la banda. |
| `antena_parabolica_x` | "~2 GB/ventana" | "≈0,9 GB por hora de enlace" | Corregido | Aritmética: 2 Mbps = 0,9 GB/h. 2 GB exigen ≈133 min de enlace continuo. |
| `antena_laser_ka` | "Transceptor Óptico Banda-Ka DeepLink" | "Terminal de Comunicaciones Ópticas (láser infrarrojo)" | Corregido | La banda Ka es radiofrecuencia; las comunicaciones ópticas usan luz infrarroja (NASA, O2O: https://www.nasa.gov/goddard/esc/exploration-and-space-communications-o2o). |

Conversión de datos (corregida): `GB = kbps × 1000 × (horas × 3600) ÷ 8 ÷ 10⁹`, con la probabilidad de enlace como valor esperado. Se asume una ventana de **2 h** (`DURACION_VENTANA_COMM_H`, valor de juego: los pasos de la Red de Espacio Profundo duran varias horas). Resultado por ventana: banda S 1,2 Mbps → 0,78 GB; banda X 2 Mbps → 1,55 GB; óptica 4,5 Mbps → 3,85 GB. Se eliminó el mínimo artificial de 2,5 GB, que además permitía transmitir sin antena instalada. El umbral de «exceso de datos» usa ahora la misma capacidad por ventana.

## 4. Revisión de coherencia física: estado

Convención: **Resuelto** (corregido en código y probado), **Aproximación** (abstracción documentada,
no cambia el balance) o **Pendiente** (decisión de diseño abierta).

| # | Tema | Estado | Detalle |
|---|---|---|---|
| 1 | Delta-v de lanzamiento (1.450 m/s) | **Resuelto** | La velocidad orbital a 400 km es 7,669 km/s; ningún ascenso cuesta 1.450 m/s (la rotación terrestre aporta ≈0,46 km/s como máximo). El lanzador externo (capacidad fija) aporta el ascenso: `delta_v_lanzamiento_ms = 0` y la nave parte de OTB con todo su delta-v. Se mantiene el límite de masa y el fallo por sobrepeso. |
| 2 | Presupuesto de delta-v lunar (3.100 m/s) | **Resuelto como misión orbital** | Fases separadas: lanzamiento (lanzador), tránsito/inserción, descenso (no incluido) y retorno. La TLI la realiza la etapa superior del lanzador: el documento de misión de ULA para LRO/LCROSS indica que la etapa Centaur entrega ambas naves en sus órbitas translunares. La nave paga LOI = 913,5 + 41,1 ≈ 955 m/s y TEI = 1.072,6 ≈ 1.073 m/s (Apolo 8, post-launch report): **2.028 m/s**. La misión ya no se presenta como aterrizaje. |
| 3 | Transmisión de datos | **Resuelto** | Ver §3: conversión kbps → GB corregida y sin mínimo artificial. |
| 4 | Autonomía en eclipse | **Resuelto** | Ver §2b. |
| 5 | Delta-v lunar de descenso y ascenso | **Futura ampliación** | Un aterrizaje en Shackleton exigiría descenso, etapa de ascenso y encuentro con la nave orbital, además de masa y combustible adicionales. No se implementa en el MVP; el robot `robot_sonda_eva` es una abstracción de sonda desplegable, sin simulación de descenso. |
| 6 | Tránsito rápido a la Luna (2 días) | **Resuelto** | Apolo 8: más de 58 h entre la TLI (GET 2:56) y la segunda corrección (GET 61:00) (NASA SP-4029) y ≈66 h entre la TLI (GET 2 h 50 min) y la primera inserción lunar (GET 69 h 8 min) (NASA, *Apollo 8 Mission Details*). Ahora el perfil rápido dura **3 días** y el estándar 4. Son parámetros de trayectoria simplificados, no duraciones universales. El factor 1,18 de delta-v del perfil rápido y 1,10 de la ventana secundaria son valores de juego. |
| 7 | Masa de los consumibles de soporte vital | **Aproximación** | NASA: O₂ 0,89 kg, agua de bebida 2,79 kg, +0,50 kg de rehidratación y 2,39 kg de comida por tripulante-día (≈6,57 kg/día, humanos de 82 kg). Un módulo de 48 días-persona cargaría ≈315 kg y el catálogo pesa 75 kg. La masa `masa_kg` agrupa módulo y consumibles a escala de tripulante de 25 kg y reciclaje parcial. No se separó porque, con el límite fijo de 1.300 kg, la nave base ya queda al límite (con 4 tripulantes y motor bipropelente pesa exactamente 1.300 kg). |
| 8 | Capacidad de lanzamiento (1.300 kg) | **Pendiente (valor de juego)** | Orión (4 tripulantes, hasta 21 días) tiene una masa bruta de lanzamiento de 78.000 lb (≈35 t) (NASA). La nave del juego es una escala reducida. |
| 9 | Tasa del enlace óptico (4,5 Mbps) | **Aproximación** | NASA demostró hasta 260 Mbps con O2O en Artemis II. Usar el valor real eliminaría el cuello de botella de datos, que es una mecánica del juego. |

Efecto en el juego tras las correcciones (configuración base, 1 a 4 tripulantes, con espectrómetro):
- Luna con bipropelente: 2.900–3.200 m/s disponibles frente a 2.028 m/s requeridos (margen amplio); con monopropelente y 4 tripulantes el motor llega a la Luna pero no tiene delta-v para el retorno.
- OTB: el requerimiento propio de la nave es de 202 m/s (inserción 100 m/s de valor de juego y desorbitado ≈102 m/s calculado: de 400 km a un perigeo de 50 km con dos cuerpos).
- Las tensiones del juego pasan de «delta-v» a masa (límite del lanzador), energía y datos.

## 4b. Aproximaciones documentadas (abstracciones del juego)

Estos valores no pretenden ser físicos ni tienen respaldo NASA; se documentan para la presentación:

- **Presupuestos (95.000–155.000 USD) y costes:** unidades ficticias del juego, sin relación con costes reales.
- **Masa del tripulante (25 kg):** decisión narrativa (perritos antropomórficos); NASA usa 82 kg para humanos (*Logistics Beyond LEO*, ASCEND 2023).
- **Antenas y paneles solares:** alcances, tasas y potencias son valores simplificados, salvo el MMRTG (110 W, 45 kg, NASA) y las constantes de la §2b.
- **Fracción de eclipse:** el balance de potencia mostrado es el instantáneo con Sol; la batería debe cubrir el eclipse (autonomía en horas), pero no se modela el promedio orbital.
- **Puntuación y evaluación:** escalas propias del juego, no métricas científicas universales.
- **Probabilidad de enlace:** se aplica como valor esperado, no como evento aleatorio.

## 5. Lista de fuentes

- NASA NTRS 20240003648, *Artemis I Engine Performance*: https://ntrs.nasa.gov/api/citations/20240003648/downloads/382_BELAIR_ARTEMIS_I_ENGINE_PERFORMANCE_FINAL.pdf
- NASA NTRS 19910014943, motor OME del transbordador: https://ntrs.nasa.gov/api/citations/19910014943/downloads/19910014943.pdf
- NASA NTRS 20100027319, SPS de Apolo: https://ntrs.nasa.gov/citations/20100027319
- NASA NTRS 20140011176, RL10 de Centaur: https://ntrs.nasa.gov/api/citations/20140011176/downloads/20140011176.pdf
- NASA NTRS 20110014012, Project Morpheus (LOX/metano): https://ntrs.nasa.gov/api/citations/20110014012/downloads/20110014012.pdf
- NASA, *State-of-the-Art of Small Spacecraft Technology*, propulsión: https://www.nasa.gov/smallsat-institute/sst-soa/in-space_propulsion
- NASA, hoja técnica del MMRTG: https://science.nasa.gov/wp-content/uploads/2024/02/mmrtg-factsheet-updated-5-18-20-1.pdf
- ULA, *Atlas V LRO/LCROSS Mission Overview* (2011), Centaur entrega LRO a su órbita translunar: https://www.ulalaunch.com/docs/default-source/exploration/atlas-v-lro-lcross-mission-overview-2011.pdf
- NASA NSSDC, Earth Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html
- NASA NSSDC, Moon Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
- NASA, Moon Facts: https://science.nasa.gov/moon/facts/
- NASA, Apollo 8 post-launch report: https://www.nasa.gov/wp-content/uploads/static/history/afj/ap08fj/pdf/a08-postlaunch-rep.pdf
- NASA, Apollo 8 Mission Details: https://www.nasa.gov/history/apollo-8-mission-details/
- NASA SP-4029, Apollo 8 Translunar Phase: https://www.nasa.gov/wp-content/uploads/static/history/SP-4029/Apollo_08f_Translunar_Phase.htm
- NASA, O2O (Orion Artemis II Optical Communications System): https://www.nasa.gov/goddard/esc/exploration-and-space-communications-o2o
- NASA NTRS 19670009664, Unified S-band: https://ntrs.nasa.gov/citations/19670009664
- NASA, *Logistics Beyond LEO* (ASCEND 2023): https://ntrs.nasa.gov/api/citations/20230013896/downloads/Logistics_BeyondLEO-ASCEND2023-Pres.pdf
- NASA, Orion overview: https://www.nasa.gov/orion-overview/
- NASA SVS 4043, LRO y regiones en sombra permanente: https://svs.gsfc.nasa.gov/4043
