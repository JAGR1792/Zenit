<script setup lang="ts">
import { ref } from 'vue'
import type { DestinoId, DificultadId } from '../services/api'

export interface OpcionDificultadMenu {
  id: DificultadId
  title: string
  badge: string
  desc: string
  perks: string[]
}

const props = defineProps<{
  loading?: boolean
  hasActiveMission?: boolean
  errorMessage?: string | null
  initialMissionName?: string
  initialDestination?: DestinoId
  initialDifficulty?: DificultadId
  difficultyOptions: OpcionDificultadMenu[]
}>()

const emit = defineEmits<{
  (
    e: 'start',
    payload: { nombre_mision: string; destino: DestinoId; dificultad: DificultadId },
  ): void
  (e: 'resume'): void
}>()

type VistaMenu = 'main' | 'new_game' | 'howto' | 'cast' | 'credits'

const activeView = ref<VistaMenu>('main')
const missionName = ref<string>(props.initialMissionName || 'Expedición Zenit-1')
const selectedDiff = ref<DificultadId | null>(null)

function handleStart(): void {
  if (!selectedDiff.value) return
  emit('start', {
    nombre_mision: missionName.value.trim() || 'Expedición Zenit-1',
    destino: props.initialDestination || 'OTB',
    dificultad: selectedDiff.value,
  })
}
</script>

<template>
  <div class="game-menu-screen">
    <!-- Escena pixel art de fondo completo (Tierra + Nave + Perro EVA + Luna) -->
    <img
      src="/sprites/escenas/menu_principal_bg.jpg"
      alt="Fondo espacial pixel art de Zenit"
      class="menu-bg-art"
      loading="eager"
      decoding="async"
      fetchpriority="high"
    />
    <div class="menu-bg-atmosphere"></div>

    <div class="menu-stage-column">
      <!-- LOGOTIPO SUPERIOR ESTILO VIDEOJUEGO PIXEL ART -->
      <header class="zenit-logo-header">
        <div class="zenit-emblem-row" aria-hidden="true">
          <span class="emblem-star">✦</span>
          <span class="emblem-tag">AGENCIA ESPACIAL ZENIT</span>
          <span class="emblem-star">✦</span>
        </div>

        <h1 class="zenit-wordmark" aria-label="ZENIT">
          <span class="wordmark-letter">Z</span>
          <span class="wordmark-letter">E</span>
          <span class="wordmark-letter letter-o">
            <span class="visor-dot"></span>
            N
          </span>
          <span class="wordmark-letter">I</span>
          <span class="wordmark-letter">T</span>
        </h1>

        <p class="zenit-tagline">SIMULADOR NARRATIVO DE MISIONES ESPACIALES</p>
      </header>

      <!-- MARCO METÁLICO CENTRAL FLOTANTE (ESTILO VIDEOJUEGO CLÁSICO) -->
      <main
        class="arcade-menu-frame"
        :class="{ 'is-wide': activeView !== 'main' }"
        data-tutorial="menu"
        aria-label="Menú principal de Zenit"
      >
        <!-- Remaches metálicos en las 4 esquinas -->
        <span class="frame-rivet tl" aria-hidden="true"></span>
        <span class="frame-rivet tr" aria-hidden="true"></span>
        <span class="frame-rivet bl" aria-hidden="true"></span>
        <span class="frame-rivet br" aria-hidden="true"></span>

        <!-- Barra superior del marco -->
        <div class="frame-top-cap">
          <span class="frame-status-dot"></span>
          <span class="frame-title-code">
            {{
              activeView === 'main'
                ? 'MENÚ PRINCIPAL'
                : activeView === 'new_game'
                  ? 'NUEVA EXPEDICIÓN'
                  : activeView === 'howto'
                    ? 'MANUAL DE VUELO'
                    : activeView === 'cast'
                      ? 'TRIPULACIÓN Y COMITÉ'
                      : 'CRÉDITOS Y ESCALA'
            }}
          </span>
          <span class="frame-status-dot"></span>
        </div>

        <!-- VISTA 1: PORTADA PRINCIPAL LIMPIA (BOTONES CENTRADOS) -->
        <div v-if="activeView === 'main'" class="arcade-btn-stack">
          <button
            v-if="hasActiveMission"
            type="button"
            class="arcade-btn arcade-btn-resume"
            @click="emit('resume')"
          >
            Continuar Expedición
          </button>

          <button
            type="button"
            class="arcade-btn arcade-btn-primary"
            @click="activeView = 'new_game'"
          >
            Nueva Expedición
          </button>

          <button type="button" class="arcade-btn" @click="activeView = 'howto'">
            Cómo Jugar
          </button>

          <button type="button" class="arcade-btn" @click="activeView = 'cast'">
            Tripulación y Comité
          </button>

          <button type="button" class="arcade-btn" @click="activeView = 'credits'">
            Créditos y Fuentes
          </button>
        </div>

        <!-- VISTA 2: CONFIGURAR NUEVA EXPEDICIÓN -->
        <div v-else-if="activeView === 'new_game'" class="submenu-body">
          <div class="submenu-field">
            <label class="submenu-label" for="zenit-mission-name">Nombre de la Misión</label>
            <input
              id="zenit-mission-name"
              v-model="missionName"
              type="text"
              class="submenu-input"
              placeholder="Expedición Zenit-1"
            />
          </div>

          <div class="submenu-field">
            <span class="submenu-label">Nivel de Dificultad (elige uno)</span>
            <div class="submenu-diff-list">
              <button
                v-for="diff in difficultyOptions"
                :key="diff.id"
                type="button"
                class="submenu-diff-item"
                :class="{ selected: selectedDiff === diff.id }"
                @click="selectedDiff = diff.id"
              >
                <div class="submenu-diff-top">
                  <span class="submenu-diff-name">{{ diff.title }}</span>
                  <span class="submenu-diff-badge">{{ diff.badge }}</span>
                </div>
                <p class="submenu-diff-desc">{{ diff.desc }}</p>
                <ul class="submenu-diff-perks">
                  <li v-for="(perk, idx) in diff.perks" :key="idx">{{ perk }}</li>
                </ul>
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="submenu-error">⚠ {{ errorMessage }}</div>

          <div class="submenu-actions">
            <button type="button" class="arcade-btn arcade-btn-back" @click="activeView = 'main'">
              ← Volver
            </button>
            <button
              type="button"
              class="arcade-btn arcade-btn-primary arcade-btn-launch"
              :disabled="loading || !selectedDiff"
              @click="handleStart"
            >
              {{
                loading
                  ? 'Iniciando Consola...'
                  : !selectedDiff
                    ? 'Selecciona una dificultad'
                    : `🚀 Despegar (${selectedDiff.toUpperCase()})`
              }}
            </button>
          </div>
        </div>

        <!-- VISTA 3: MANUAL RÁPIDO (CÓMO JUGAR) -->
        <div v-else-if="activeView === 'howto'" class="submenu-body">
          <div class="howto-compact-list">
            <div class="howto-item">
              <span class="howto-num">1</span>
              <div>
                <strong>Negocia ante el Comité (Etapa 2)</strong>
                <p>
                  Argumenta frente al Gato Jefe y sus 2 ayudantes para conseguir más Créditos Zenit
                  (CZ) antes de entrar al hangar.
                </p>
              </div>
            </div>

            <div class="howto-item">
              <span class="howto-num">2</span>
              <div>
                <strong>Diseña sin superar 1.300 kg ni quedarte corto de Delta-v (Etapas 3-4)</strong>
                <p>
                  Lee la ficha técnica de cada componente y contrata hasta 3 perros especialistas.
                </p>
              </div>
            </div>

            <div class="howto-item accent">
              <span class="howto-num">3</span>
              <div>
                <strong>Camina con A/D e interactúa con E en Destino (Etapas 6-9)</strong>
                <p>
                  Primero recolecta datos en el <strong>Laboratorio Científico</strong> y luego
                  transmítelos desde la <strong>Sala de Sistemas</strong> antes del retorno.
                </p>
              </div>
            </div>

            <div class="howto-item">
              <span class="howto-num">4</span>
              <div>
                <strong>Veredicto Final del Gato Jefe (Etapa 10)</strong>
                <p>
                  Tus decisiones determinan uno de los múltiples finales ante el Comité Zenit.
                </p>
              </div>
            </div>
          </div>

          <div class="submenu-actions single">
            <button type="button" class="arcade-btn arcade-btn-back" @click="activeView = 'main'">
              ← Volver al Menú
            </button>
          </div>
        </div>

        <!-- VISTA 4: TRIPULACIÓN Y COMITÉ -->
        <div v-else-if="activeView === 'cast'" class="submenu-body">
          <div class="cast-panel-section">
            <span class="cast-panel-title">TRIPULACIÓN CANINA (A BORDO DE LA NAVE)</span>
            <div class="cast-sprites-row">
              <div class="cast-sprite-item">
                <img
                  src="/sprites/perro/PerroDer1.png"
                  alt="Director"
                  width="54"
                  height="68"
                  loading="lazy"
                  decoding="async"
                  class="cast-sprite-img"
                />
                <span>DIRECTOR</span>
              </div>
              <div class="cast-sprite-item">
                <img
                  src="/sprites/elementos/PerroC.png"
                  alt="Ciencia"
                  width="54"
                  height="68"
                  loading="lazy"
                  decoding="async"
                  class="cast-sprite-img"
                />
                <span>CIENCIA</span>
              </div>
              <div class="cast-sprite-item">
                <img
                  src="/sprites/elementos/PerroI.png"
                  alt="Ingeniería"
                  width="54"
                  height="68"
                  loading="lazy"
                  decoding="async"
                  class="cast-sprite-img"
                />
                <span>INGENIERÍA</span>
              </div>
              <div class="cast-sprite-item">
                <img
                  src="/sprites/elementos/PerroD.png"
                  alt="Medicina"
                  width="54"
                  height="68"
                  loading="lazy"
                  decoding="async"
                  class="cast-sprite-img"
                />
                <span>MEDICINA</span>
              </div>
              <div class="cast-sprite-item">
                <img
                  src="/sprites/elementos/PerroCom.png"
                  alt="Comms"
                  width="54"
                  height="68"
                  loading="lazy"
                  decoding="async"
                  class="cast-sprite-img"
                />
                <span>COMMS</span>
              </div>
            </div>
          </div>

          <div class="cast-panel-section">
            <span class="cast-panel-title amber">COMITÉ DE LA AGENCIA (GATO JEFE + 2 AYUDANTES)</span>
            <div class="cast-sprites-row">
              <div class="cat-badge-item">
                <img
                  src="/sprites/iconos/icono_gato_jefe_naranja.jpg"
                  alt="Gato Jefe"
                  class="cat-badge-img"
                  loading="lazy"
                  decoding="async"
                />
                <span>GATO JEFE</span>
              </div>
              <div class="cat-badge-item">
                <img
                  src="/sprites/iconos/icono_gato_asistente_blanco.png"
                  alt="Auditora Blanca"
                  class="cat-badge-img"
                  loading="lazy"
                  decoding="async"
                />
                <span>FINANZAS</span>
              </div>
              <div class="cat-badge-item">
                <img
                  src="/sprites/iconos/icono_gato_asistente_negro.png"
                  alt="Asesor Negro"
                  class="cat-badge-img"
                  loading="lazy"
                  decoding="async"
                />
                <span>RIESGO</span>
              </div>
            </div>
          </div>

          <div class="submenu-actions single">
            <button type="button" class="arcade-btn arcade-btn-back" @click="activeView = 'main'">
              ← Volver al Menú
            </button>
          </div>
        </div>

        <!-- VISTA 5: CRÉDITOS Y FUENTES -->
        <div v-else class="submenu-body">
          <div class="credits-card">
            <p class="credits-lead">
              <strong>ZENIT</strong> es un simulador narrativo educativo sobre toma de decisiones en
              misiones espaciales tripuladas.
            </p>
            <ul class="credits-list">
              <li>
                <strong>Economía ficticia:</strong> Todas las partidas operan en
                <strong>Créditos Zenit (CZ)</strong> para equilibrar costes y jugabilidad sin
                depender de presupuestos reales en dólares.
              </li>
              <li>
                <strong>Modelo físico simplificado:</strong> Ecuación del cohete de Tsiolkovsky,
                balance eléctrico orbital con eclipses, autonomía de O₂/alimento y ventanas reales
                de enlace.
              </li>
              <li>
                <strong>Referencias científicas:</strong> Datos de propulsión y órbitas inspirados en
                publicaciones abiertas de NASA (Artemis I, STS OME, Apollo SPS y documentación
                técnica de la Luna/OTB).
              </li>
            </ul>
          </div>

          <div class="submenu-actions single">
            <button type="button" class="arcade-btn arcade-btn-back" @click="activeView = 'main'">
              ← Volver al Menú
            </button>
          </div>
        </div>
      </main>

      <footer class="menu-footer-note">
        ZENIT · EXPEDICIÓN CIENTÍFICA · CONTROL EN TIERRA (CZ)
      </footer>
    </div>
  </div>
</template>

<style scoped>
.game-menu-screen {
  position: fixed;
  inset: 0;
  z-index: 50;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  background: #060914;
}

.menu-bg-art {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center center;
  image-rendering: pixelated;
  z-index: 0;
  pointer-events: none;
}

.menu-bg-atmosphere {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    radial-gradient(circle at 50% 18%, rgba(79, 209, 197, 0.14) 0%, transparent 45%),
    radial-gradient(circle at 50% 58%, rgba(7, 10, 22, 0.35) 0%, rgba(5, 8, 18, 0.72) 100%);
}

.menu-stage-column {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 720px;
  margin: auto 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

/* ========================================================================= */
/* LOGOTIPO SUPERIOR ESTILO VIDEOJUEGO PIXEL ART                             */
/* ========================================================================= */
.zenit-logo-header {
  text-align: center;
  user-select: none;
}

.zenit-emblem-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'Silkscreen', 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--cyan);
  margin-bottom: 4px;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.emblem-star {
  color: var(--gold);
}

.zenit-wordmark {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: 'Silkscreen', 'IBM Plex Mono', monospace;
  font-size: clamp(46px, 8vw, 72px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.06em;
  color: var(--gold);
  text-shadow:
    0 5px 0 #171f3b,
    0 9px 22px rgba(0, 0, 0, 0.92),
    0 0 26px rgba(245, 211, 107, 0.28);
  margin: 0;
}

.wordmark-letter {
  position: relative;
  display: inline-block;
}

.wordmark-letter.letter-o {
  color: #fff3c4;
}

.visor-dot {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 10px;
  height: 4px;
  border-radius: 2px;
  background: var(--cyan);
  box-shadow: 0 0 10px var(--cyan);
}

.zenit-tagline {
  margin-top: 8px;
  font-size: 11px;
  letter-spacing: 0.22em;
  color: var(--bone);
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.95);
}

/* ========================================================================= */
/* MARCO CENTRAL METÁLICO FLOTANTE (REFERENCIA VIDEOJUEGO)                   */
/* ========================================================================= */
.arcade-menu-frame {
  position: relative;
  width: 100%;
  max-width: 400px;
  background: linear-gradient(180deg, rgba(25, 34, 62, 0.94) 0%, rgba(10, 14, 28, 0.96) 100%);
  border: 2px solid #6379a8;
  border-radius: 8px;
  padding: 16px 18px 18px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -3px 0 rgba(4, 6, 14, 0.8),
    0 18px 46px rgba(0, 0, 0, 0.85),
    0 0 0 3px rgba(7, 10, 22, 0.85);
  backdrop-filter: blur(4px);
  transition: max-width 0.2s ease;
}

.arcade-menu-frame.is-wide {
  max-width: 680px;
}

.frame-rivet {
  position: absolute;
  width: 7px;
  height: 7px;
  background: #8fa3bf;
  border: 1px solid #070a14;
  border-radius: 1px;
}

.frame-rivet.tl {
  top: 6px;
  left: 6px;
}
.frame-rivet.tr {
  top: 6px;
  right: 6px;
}
.frame-rivet.bl {
  bottom: 6px;
  left: 6px;
}
.frame-rivet.br {
  bottom: 6px;
  right: 6px;
}

.frame-top-cap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(99, 121, 168, 0.45);
}

.frame-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 8px var(--cyan);
}

.frame-title-code {
  font-family: 'Silkscreen', 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--cyan);
}

/* PILA DE BOTONES PRINCIPALES */
.arcade-btn-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.arcade-btn {
  width: 100%;
  padding: 11px 16px;
  font-family: 'Silkscreen', 'IBM Plex Mono', monospace;
  font-size: 13px;
  letter-spacing: 0.06em;
  color: var(--bone);
  text-align: center;
  background: linear-gradient(180deg, #1b2442 0%, #0d1326 55%, #161f3a 100%);
  border: 1px solid #4d618f;
  border-radius: 999px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 3px 10px rgba(0, 0, 0, 0.55);
  transition:
    transform 0.12s ease,
    border-color 0.14s ease,
    box-shadow 0.14s ease,
    color 0.14s ease;
}

.arcade-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: var(--cyan);
  color: #ffffff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    0 0 16px rgba(79, 209, 197, 0.28);
}

.arcade-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.arcade-btn-primary {
  background: linear-gradient(180deg, #324a7a 0%, #172748 55%, #233b66 100%);
  border-color: var(--amber);
  color: var(--gold);
}

.arcade-btn-primary:hover:not(:disabled) {
  border-color: var(--gold);
  color: #fff8db;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 18px rgba(255, 176, 0, 0.35);
}

.arcade-btn-resume {
  border-color: var(--cyan);
  color: var(--cyan);
}

.arcade-btn-back {
  border-radius: 6px;
  font-size: 11px;
  width: auto;
  padding: 9px 16px;
}

.arcade-btn-launch {
  border-radius: 6px;
  font-size: 12px;
  flex: 1;
}

/* SUBVISTAS DENTRO DEL MARCO CENTRAL */
.submenu-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 66vh;
  overflow-y: auto;
  padding-right: 4px;
}

.submenu-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.submenu-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--mist);
  letter-spacing: 0.05em;
}

.submenu-input {
  background: rgba(7, 10, 20, 0.9);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 8px 10px;
  color: var(--bone);
  font-family: inherit;
  font-size: 12px;
}

.submenu-dest-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.submenu-chip-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 8px 10px;
  background: rgba(7, 10, 20, 0.85);
  border: 1px solid var(--steel);
  border-radius: 6px;
  text-align: left;
  color: var(--mist);
}

.submenu-chip-btn strong {
  font-size: 11.5px;
  color: var(--bone);
}

.submenu-chip-btn small {
  font-size: 10px;
}

.submenu-chip-btn.active {
  border-color: var(--cyan);
  background: rgba(79, 209, 197, 0.14);
}

.submenu-diff-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.submenu-diff-item {
  width: 100%;
  text-align: left;
  padding: 9px 11px;
  background: rgba(7, 10, 20, 0.85);
  border: 1px solid var(--steel);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.submenu-diff-item.selected {
  border-color: var(--amber);
  background: rgba(255, 176, 0, 0.12);
}

.submenu-diff-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.submenu-diff-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--gold);
}

.submenu-diff-badge {
  font-size: 9px;
  font-weight: 700;
  color: var(--amber);
  border: 1px solid rgba(255, 176, 0, 0.45);
  border-radius: 3px;
  padding: 2px 6px;
}

.submenu-diff-desc {
  font-size: 11px;
  color: var(--bone);
}

.submenu-diff-perks {
  padding-left: 16px;
  font-size: 10px;
  color: var(--cyan);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.submenu-error {
  padding: 8px 10px;
  border-radius: 5px;
  border: 1px solid var(--red);
  background: rgba(229, 72, 77, 0.15);
  color: #ffb3b3;
  font-size: 11px;
}

.submenu-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-top: 4px;
}

.submenu-actions.single {
  justify-content: flex-start;
}

/* CÓMO JUGAR COMPACTO */
.howto-compact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.howto-item {
  display: flex;
  gap: 10px;
  background: rgba(7, 10, 20, 0.85);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 9px 11px;
  font-size: 11px;
  color: var(--mist);
}

.howto-item.accent {
  border-color: var(--cyan);
  background: rgba(79, 209, 197, 0.08);
}

.howto-item strong {
  color: var(--bone);
  display: block;
  margin-bottom: 2px;
}

.howto-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--amber);
  color: var(--void);
  font-weight: 700;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* TRIPULACIÓN Y COMITÉ */
.cast-panel-section {
  background: rgba(7, 10, 20, 0.85);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.cast-panel-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 0.08em;
}

.cast-panel-title.amber {
  color: var(--amber);
}

.cast-sprites-row {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
}

.cast-sprite-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  color: var(--mist);
}

.cast-sprite-img {
  width: 54px;
  height: 68px;
  object-fit: contain;
  image-rendering: pixelated;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.65));
}

.cat-badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  color: var(--mist);
}

.cat-badge-img {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  border: 1px solid var(--amber);
  image-rendering: pixelated;
  object-fit: cover;
}

/* CRÉDITOS */
.credits-card {
  background: rgba(7, 10, 20, 0.85);
  border: 1px solid var(--steel);
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 11.5px;
  color: var(--bone);
}

.credits-lead {
  margin-bottom: 8px;
}

.credits-list {
  padding-left: 16px;
  color: var(--mist);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.credits-list strong {
  color: var(--cyan);
}

.menu-footer-note {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: rgba(232, 228, 216, 0.72);
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
  text-align: center;
}

@media (max-width: 640px) {
  .submenu-dest-grid {
    grid-template-columns: 1fr;
  }
}
</style>
