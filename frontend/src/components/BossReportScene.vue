<script setup lang="ts">
import type { InformeFinal } from '../services/api'

defineProps<{
  report: InformeFinal
}>()

const emit = defineEmits<{
  (e: 'restart'): void
}>()
</script>

<template>
  <div class="boss-office-scene">
    <div class="office-header">
      <div>
        <div class="ending-tag">DESPACHO DE DIRECCIÓN GENERAL · EVALUACIÓN POST-MISIÓN</div>
        <h2 class="ending-title">{{ report.titulo_final }}</h2>
        <p class="ending-sub">{{ report.subtitulo_final }}</p>
      </div>
      <div class="score-badge">
        <div class="score-label">ÍNDICE GLOBAL</div>
        <div class="score-num">{{ report.puntuacion_global }} / 100</div>
      </div>
    </div>

    <!-- Acto 1: Conversación con el Jefe y Ruptura de la Cuarta Pared -->
    <div class="panel-sub boss-dialogue-box">
      <div class="speaker-label">DIRECTOR DEL CONSORCIO AEROESPACIAL:</div>
      <p class="serif-narrative boss-quote">{{ report.dialogo_jefe_apertura }}</p>

      <div v-if="report.monologo_cuarta_pared" class="fourth-wall-box">
        <div class="silence-banner">
          [SILENCIO TOTAL EN SALA: {{ report.silencio_previo_segundos }} SEGUNDOS]
        </div>
        <p class="serif-narrative fourth-wall-text">{{ report.monologo_cuarta_pared }}</p>
      </div>
    </div>

    <!-- Acto 2: Retroalimentación por las 7 Dimensiones -->
    <div class="dimensions-section">
      <h3 class="section-heading">DESGLOSE MULTIDIMENSIONAL DEL JEFE</h3>
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
      <p class="serif-narrative closing-phrase">{{ report.frase_despedida }}</p>
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
.boss-dialogue-box {
  padding: 16px;
  border-left: 3px solid var(--mist);
}
.speaker-label {
  font-size: 11px;
  color: var(--amber);
  font-weight: 700;
  margin-bottom: 6px;
}
.boss-quote {
  font-size: 16px;
  color: var(--bone);
  line-height: 1.65;
}
.fourth-wall-box {
  margin-top: 14px;
  padding: 14px;
  background: rgba(229, 72, 77, 0.1);
  border: 1px solid var(--red);
  border-radius: 6px;
}
.silence-banner {
  font-size: 11px;
  color: var(--red);
  font-weight: 700;
  margin-bottom: 6px;
}
.fourth-wall-text {
  font-size: 15px;
  color: var(--bone);
  font-style: italic;
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
.closing-phrase {
  font-size: 16px;
  color: var(--gold);
  max-width: 720px;
}
</style>
