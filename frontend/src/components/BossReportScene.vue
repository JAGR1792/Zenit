<script setup lang="ts">
import { computed, ref } from 'vue'
import type { InformeFinal } from '../services/api'

const props = defineProps<{
  report: InformeFinal
}>()

const emit = defineEmits<{
  (e: 'restart'): void
}>()

// Selector de orador activo en el Tribunal de Evaluación (El Gato Jefe + sus 2 Ayudantes)
const activeSpeaker = ref<'jefe' | 'asistente_blanco' | 'asistente_negro'>('jefe')

const finDim = computed(
  () => props.report.dimensiones.find((d) => d.id === 'eficiencia_financiera') ?? props.report.dimensiones[0],
)
const sciDim = computed(
  () => props.report.dimensiones.find((d) => d.id === 'exito_cientifico') ?? props.report.dimensiones[0],
)
const crewDim = computed(
  () => props.report.dimensiones.find((d) => d.id === 'supervivencia_salud') ?? props.report.dimensiones[0],
)

const tribunalQuotes = computed(() => ({
  jefe: {
    name: 'GATO JEFE · COMISIONADO FÉLIX VANCE',
    role: 'PRESIDENTE DEL TRIBUNAL DE EVALUACIÓN',
    icon: '/sprites/iconos/icono_gato_jefe.png',
    mood:
      props.report.puntuacion_global >= 75
        ? '/sprites/elementos/Sol.png'
        : props.report.puntuacion_global >= 45
          ? '/sprites/elementos/Nube.png'
          : '/sprites/elementos/Lluvia.png',
    text: props.report.dialogo_jefe_apertura,
  },
  asistente_blanco: {
    name: 'AUDITORA BLANCA · FINANZAS Y MASA',
    role: 'AYUDANTE 1 DEL JEFE (PRESUPUESTO Y TELEMETRÍA)',
    icon: '/sprites/iconos/icono_gato_asistente_blanco.png',
    mood:
      (finDim.value?.puntuacion ?? 50) >= 70
        ? '/sprites/elementos/Sol.png'
        : (finDim.value?.puntuacion ?? 50) >= 40
          ? '/sprites/elementos/Nube.png'
          : '/sprites/elementos/Lluvia.png',
    text: `«${finDim.value?.comentario_jefe ?? ''} (${finDim.value?.explicacion_tecnica ?? ''})»`,
  },
  asistente_negro: {
    name: 'ASESOR NEGRO · RIESGO, CIENCIA Y TRIPULACIÓN',
    role: 'AYUDANTE 2 DEL JEFE (OPERACIONES Y SEGURIDAD)',
    icon: '/sprites/iconos/icono_gato_asistente_negro.png',
    mood:
      (sciDim.value?.puntuacion ?? 50) >= 70 && !props.report.hubo_muertes_tripulacion
        ? '/sprites/elementos/Sol.png'
        : '/sprites/elementos/Lluvia.png',
    text: `«${sciDim.value?.comentario_jefe ?? ''} ${crewDim.value?.comentario_jefe ?? ''}»`,
  },
}))

const currentTribunalSpeech = computed(() => tribunalQuotes.value[activeSpeaker.value])
</script>

<template>
  <div class="boss-office-scene">
    <div class="office-header">
      <div>
        <div class="ending-tag">
          SALA DE JUICIO · TRIBUNAL DE EVALUACIÓN DE LA MISIÓN (EL GATO JEFE Y SUS 2 AYUDANTES)
        </div>
        <h2 class="ending-title">{{ report.titulo_final }}</h2>
        <p class="ending-sub">{{ report.subtitulo_final }}</p>
      </div>
      <div class="score-badge">
        <div class="score-label">ÍNDICE GLOBAL</div>
        <div class="score-num">{{ report.puntuacion_global }} / 100</div>
      </div>
    </div>

    <!-- ======================================================================= -->
    <!-- ACTO 1: ESCENA GRANDE NOVELA VISUAL - SALA DE JUICIO CON LOS 3 GATOS   -->
    <!-- ======================================================================= -->
    <div class="vn-tribunal-stage">
      <!-- Fondo pixel-art grande separado de la Sala de Juicio -->
      <img
        src="/sprites/escenas/sala_juicio_tribunal.png"
        alt="Sala de Juicio - Tribunal de Evaluación de la Misión"
        class="tribunal-bg-img"
      />
      <div class="tribunal-vignette"></div>

      <!-- Cinta superior de escena estilo debriefing -->
      <div class="tribunal-top-hud">
        <div>
          <div class="thud-main">ZENIT · TRIBUNAL DE EVALUACIÓN DE LA MISIÓN</div>
          <div class="thud-sub">FASE: EVALUACIÓN / RETORNO · COMITÉ DE LOS 3 GATOS</div>
        </div>
        <div class="tribunal-tabs">
          <button
            class="trib-tab-btn"
            :class="{ active: activeSpeaker === 'jefe' }"
            @click="activeSpeaker = 'jefe'"
          >
            <img src="/sprites/iconos/icono_gato_jefe.png" alt="Gato Jefe" class="tab-mini-icon" />
            <span>Gato Jefe (Veredicto)</span>
          </button>
          <button
            class="trib-tab-btn"
            :class="{ active: activeSpeaker === 'asistente_blanco' }"
            @click="activeSpeaker = 'asistente_blanco'"
          >
            <img
              src="/sprites/iconos/icono_gato_asistente_blanco.png"
              alt="Auditora Blanca"
              class="tab-mini-icon"
            />
            <span>Ayudante 1: Finanzas</span>
          </button>
          <button
            class="trib-tab-btn"
            :class="{ active: activeSpeaker === 'asistente_negro' }"
            @click="activeSpeaker = 'asistente_negro'"
          >
            <img
              src="/sprites/iconos/icono_gato_asistente_negro.png"
              alt="Asesor Negro"
              class="tab-mini-icon"
            />
            <span>Ayudante 2: Ciencia/Tripulación</span>
          </button>
        </div>
      </div>

      <!-- Globo de diálogo principal con el icono enmarcado de quien habla -->
      <div class="tribunal-speech-zone">
        <div class="tribunal-speech-bubble">
          <div class="tspeech-speaker-bar">
            <span class="tspeech-name">{{ currentTribunalSpeech.name }}</span>
            <span class="tspeech-role">{{ currentTribunalSpeech.role }}</span>
          </div>

          <div class="tspeech-body">
            <div class="tspeech-portrait-box">
              <img
                :src="currentTribunalSpeech.icon"
                :alt="currentTribunalSpeech.name"
                class="tspeech-portrait-img"
              />
              <img :src="currentTribunalSpeech.mood" alt="Estado" class="tspeech-mood-icon" />
            </div>

            <div class="tspeech-copy">
              <p class="serif-narrative boss-quote">{{ currentTribunalSpeech.text }}</p>

              <div v-if="report.monologo_cuarta_pared && activeSpeaker === 'jefe'" class="fourth-wall-box">
                <div class="silence-banner">
                  [SILENCIO TOTAL EN LA SALA DE JUICIO: {{ report.silencio_previo_segundos }} SEGUNDOS]
                </div>
                <p class="serif-narrative fourth-wall-text">{{ report.monologo_cuarta_pared }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Barra inferior Novela Visual: Opciones de consulta al Tribunal + Retrato del Capitán Perro -->
      <div class="tribunal-bottom-bar">
        <div class="tribunal-choices-box">
          <div class="tchoice-tag">CAPITÁN PERRO · RESPUESTAS ANTE EL TRIBUNAL</div>
          <button
            class="tchoice-line"
            :class="{ selected: activeSpeaker === 'jefe' }"
            @click="activeSpeaker = 'jefe'"
          >
            &gt; ESCUCHAR DICTAMEN GENERAL DEL GATO JEFE (COMISIONADO FÉLIX VANCE)
          </button>
          <button
            class="tchoice-line"
            :class="{ selected: activeSpeaker === 'asistente_blanco' }"
            @click="activeSpeaker = 'asistente_blanco'"
          >
            &gt; CONSULTAR INFORME FINANCIERO DE LA AUDITORA BLANCA (AYUDANTE 1)
          </button>
          <button
            class="tchoice-line"
            :class="{ selected: activeSpeaker === 'asistente_negro' }"
            @click="activeSpeaker = 'asistente_negro'"
          >
            &gt; CONSULTAR EVALUACIÓN CIENTÍFICA Y HUMANA DEL ASESOR NEGRO (AYUDANTE 2)
          </button>
        </div>

        <div class="tribunal-player-card">
          <img
            :src="
              report.puntuacion_global >= 65
                ? '/sprites/elementos/Sol.png'
                : report.puntuacion_global >= 40
                  ? '/sprites/elementos/Nube.png'
                  : '/sprites/elementos/Lluvia.png'
            "
            alt="Ánimo"
            class="tplayer-sun"
          />
          <div class="tplayer-frame">
            <img
              src="/sprites/iconos/icono_captain_dog_casco.png"
              alt="Captain Dog"
              class="tplayer-img"
            />
          </div>
          <div class="tplayer-label">CAPTAIN DOG</div>
        </div>
      </div>
    </div>

    <!-- Acto 2: Retroalimentación por las 7 Dimensiones -->
    <div class="dimensions-section">
      <h3 class="section-heading">DESGLOSE MULTIDIMENSIONAL DEL COMITÉ (7 DIMENSIONES)</h3>
      <div class="dimensions-grid">
        <div v-for="dim in report.dimensiones" :key="dim.id" class="dim-card">
          <div class="dim-top">
            <span class="dim-name">{{ dim.nombre }}</span>
            <span class="dim-score">{{ dim.puntuacion }}/100 · {{ dim.estado_etiqueta }}</span>
          </div>
          <div class="dim-bar">
            <div
              :style="{
                width: `${Math.min(100, dim.puntuacion)}%`,
                background:
                  dim.puntuacion >= 70 ? 'var(--green)' : dim.puntuacion >= 40 ? 'var(--amber)' : 'var(--red)',
              }"
            ></div>
          </div>
          <p class="serif-narrative dim-boss">{{ dim.comentario_jefe }}</p>
          <p class="dim-tech">{{ dim.explicacion_tecnica }}</p>
        </div>
      </div>
    </div>

    <!-- Documento de Reporte Técnico y Trazabilidad Causal -->
    <div class="technical-dossier">
      <div class="dossier-col">
        <h3 class="section-heading">TRAZABILIDAD CAUSAL DE LA MISIÓN</h3>
        <ul class="causal-list">
          <li v-for="(item, idx) in report.trazabilidad_causal" :key="idx">{{ item }}</li>
        </ul>
      </div>
      <div class="dossier-col">
        <h3 class="section-heading">DIAGNÓSTICO DE INGENIERÍA (QUÉ MEJORAR)</h3>
        <ul class="causal-list">
          <li v-for="(rec, idx) in report.recomendaciones_ingenieria" :key="idx">{{ rec }}</li>
        </ul>
      </div>
    </div>

    <!-- Acto 3: Frase Final de Despedida -->
    <div class="closing-box">
      <div class="closing-left">
        <img
          src="/sprites/iconos/icono_gato_jefe.png"
          alt="Gato Jefe"
          class="closing-icon"
        />
        <p class="serif-narrative closing-phrase">{{ report.frase_despedida }}</p>
      </div>
      <button class="btn-primary" @click="emit('restart')">
        Planificar Nueva Expedición Espacial
      </button>
    </div>
  </div>
</template>

<style scoped>
.boss-office-scene {
  background: #141926;
  border: 1px solid var(--mist);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.office-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
  border-bottom: 1px solid var(--steel);
  padding-bottom: 12px;
}
.ending-tag {
  font-size: 11px;
  color: var(--mist);
  letter-spacing: 0.05em;
}
.ending-title {
  color: var(--gold);
  font-size: 22px;
  margin-top: 4px;
}
.ending-sub {
  color: var(--mist);
  font-size: 13px;
}
.score-badge {
  background: var(--void);
  border: 1px solid var(--amber);
  border-radius: 6px;
  padding: 8px 14px;
  text-align: right;
}
.score-label {
  font-size: 10px;
  color: var(--mist);
}
.score-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--amber);
}

/* ========================================================================= */
/* ESCENA NOVELA VISUAL: SALA DE JUICIO / TRIBUNAL DE LOS 3 GATOS            */
/* ========================================================================= */
.vn-tribunal-stage {
  position: relative;
  min-height: 490px;
  border: 2px solid var(--amber);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: #0d101b;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
}

.tribunal-bg-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 22%;
  image-rendering: pixelated;
  z-index: 0;
}

.tribunal-vignette {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(8, 11, 20, 0.72) 0%,
    rgba(8, 11, 20, 0.12) 38%,
    rgba(8, 11, 20, 0.65) 72%,
    rgba(8, 11, 20, 0.94) 100%
  );
  z-index: 1;
}

.tribunal-top-hud {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(8, 11, 20, 0.86);
  border-bottom: 1px solid rgba(242, 209, 107, 0.45);
}

.thud-main {
  font-size: 13px;
  font-weight: 700;
  color: var(--bone);
  letter-spacing: 0.06em;
}

.thud-sub {
  font-size: 10px;
  color: var(--amber);
}

.tribunal-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.trib-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  font-size: 11px;
  background: rgba(15, 21, 38, 0.9);
  border: 1px solid var(--steel);
  border-radius: 5px;
  color: var(--mist);
  cursor: pointer;
}

.trib-tab-btn.active {
  border-color: var(--gold);
  color: var(--gold);
  background: rgba(245, 158, 11, 0.18);
}

.tab-mini-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
  border-radius: 3px;
}

.tribunal-speech-zone {
  position: relative;
  z-index: 2;
  padding: 14px 18px;
  margin-top: auto;
}

.tribunal-speech-bubble {
  max-width: 820px;
  background: rgba(8, 11, 20, 0.93);
  border: 2px solid #d6c59a;
  border-radius: 6px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.85);
  overflow: hidden;
}

.tspeech-speaker-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(27, 35, 64, 0.95);
  border-bottom: 1px solid #d6c59a;
}

.tspeech-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.05em;
}

.tspeech-role {
  font-size: 10px;
  color: var(--cyan);
}

.tspeech-body {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 14px;
}

.tspeech-portrait-box {
  position: relative;
  flex-shrink: 0;
}

.tspeech-portrait-img {
  width: 74px;
  height: 74px;
  object-fit: contain;
  image-rendering: pixelated;
  border-radius: 4px;
}

.tspeech-mood-icon {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 28px;
  height: 28px;
  image-rendering: pixelated;
}

.tspeech-copy {
  flex: 1;
}

.boss-quote {
  font-size: 15px;
  color: var(--bone);
  line-height: 1.55;
}

.fourth-wall-box {
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(229, 72, 77, 0.14);
  border: 1px solid var(--red);
  border-radius: 6px;
}

.silence-banner {
  font-size: 10px;
  color: var(--red);
  font-weight: 700;
  margin-bottom: 4px;
}

.fourth-wall-text {
  font-size: 14px;
  color: var(--bone);
  font-style: italic;
}

.tribunal-bottom-bar {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 140px;
  gap: 12px;
  align-items: end;
  padding: 0 18px 14px;
}

@media (max-width: 760px) {
  .tribunal-bottom-bar {
    grid-template-columns: 1fr;
  }
}

.tribunal-choices-box {
  background: rgba(8, 11, 20, 0.94);
  border: 2px solid #d6c59a;
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.tchoice-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.06em;
  margin-bottom: 2px;
}

.tchoice-line {
  text-align: left;
  background: rgba(20, 27, 45, 0.85);
  border: 1px solid rgba(138, 153, 173, 0.3);
  border-radius: 4px;
  padding: 6px 10px;
  color: var(--bone);
  font-size: 11px;
  font-family: var(--font-mono);
  cursor: pointer;
}

.tchoice-line:hover,
.tchoice-line.selected {
  border-color: var(--gold);
  color: var(--gold);
  background: rgba(245, 158, 11, 0.14);
}

.tribunal-player-card {
  position: relative;
  background: rgba(8, 11, 20, 0.94);
  border: 2px solid #d6c59a;
  border-radius: 6px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tplayer-sun {
  position: absolute;
  top: -12px;
  right: -10px;
  width: 30px;
  height: 30px;
  image-rendering: pixelated;
}

.tplayer-frame {
  width: 100%;
  height: 92px;
  background: #2c4a6f;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.tplayer-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  image-rendering: pixelated;
}

.tplayer-label {
  margin-top: 5px;
  font-size: 10px;
  font-weight: 700;
  color: var(--bone);
  letter-spacing: 0.06em;
}

.section-heading {
  font-size: 13px;
  color: var(--amber);
  margin-bottom: 10px;
}
.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 10px;
}
.dim-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 10px;
}
.dim-top {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 6px;
}
.dim-name {
  color: var(--bone);
}
.dim-score {
  color: var(--cyan);
}
.dim-bar {
  height: 5px;
  background: var(--steel);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}
.dim-bar > div {
  height: 100%;
}
.dim-boss {
  font-size: 13px;
  color: var(--bone);
  margin-bottom: 4px;
}
.dim-tech {
  font-size: 10px;
  color: var(--mist);
}
.technical-dossier {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 760px) {
  .technical-dossier {
    grid-template-columns: 1fr;
  }
}
.dossier-col {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 5px;
  padding: 12px;
}
.causal-list {
  padding-left: 16px;
  font-size: 11px;
  color: var(--mist);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.closing-box {
  border-top: 1px solid var(--steel);
  padding-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.closing-left {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 760px;
}
.closing-icon {
  width: 52px;
  height: 52px;
  image-rendering: pixelated;
  flex-shrink: 0;
}
.closing-phrase {
  font-size: 16px;
  color: var(--gold);
}
</style>
