<script setup lang="ts">
import { computed } from 'vue'
import type { ComponenteCatalogo, EstadoMision } from '../services/api'
import PixelSprite, { obtenerSpriteTripulante } from './PixelSprite.vue'

const props = defineProps<{
  mission: EstadoMision
  catalog: ComponenteCatalogo[]
}>()

const installedSlots = computed(() => {
  const map = new Set<string>()
  for (const cid of props.mission.componentes_instalados) {
    const found = props.catalog.find((c) => c.id === cid)
    if (found) {
      map.add(found.slot_visual)
    }
  }
  return map
})

const moodColor = (mood: string): string => {
  if (mood === 'sol') return '#F5C84C'
  if (mood === 'nube') return '#9AA8B8'
  return '#4A78C2'
}
</script>

<template>
  <div class="panel-box schematic-wrapper">
    <div class="schematic-header">
      <div>
        <span class="label-amber">DISEÑO VISUAL DE LA NAVE Y DOTACIÓN PIXEL ART</span>
        <span class="dest-tag">{{
          mission.destino === 'LUNA' ? 'CONFIGURACIÓN CISLUNAR' : 'CONFIGURACIÓN OTB'
        }}</span>
      </div>
      <div class="sub-caption">
        Cada componente comprado se acopla al chasis; la tripulación muestra su sprite y estado de ánimo
      </div>
    </div>

    <div class="svg-stage">
      <svg viewBox="0 0 680 250" class="ship-svg" aria-label="Esquemático visual de la nave">
        <!-- Fondo estelar con gradiente y estrellas -->
        <defs>
          <radialGradient id="spaceGrad" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stop-color="#1B2340" />
            <stop offset="100%" stop-color="#05070F" />
          </radialGradient>
        </defs>
        <rect x="0" y="0" width="680" height="250" fill="url(#spaceGrad)" rx="6" />
        <g fill="#E8E4D8" opacity="0.5">
          <circle cx="40" cy="30" r="1" />
          <circle cx="120" cy="55" r="0.8" />
          <circle cx="200" cy="20" r="1.2" />
          <circle cx="300" cy="40" r="0.9" />
          <circle cx="420" cy="25" r="1" />
          <circle cx="500" cy="60" r="0.7" />
          <circle cx="620" cy="35" r="1.1" />
          <circle cx="80" cy="200" r="0.8" />
          <circle cx="260" cy="220" r="1" />
          <circle cx="480" cy="210" r="0.9" />
        </g>
        <circle
          v-if="mission.destino === 'OTB'"
          cx="590"
          cy="245"
          r="115"
          fill="#2E6FD8"
          opacity="0.32"
        />
        <circle
          v-else
          cx="590"
          cy="70"
          r="46"
          fill="#B8B2A7"
          stroke="#6E6A66"
          stroke-width="3"
          opacity="0.45"
        />

        <!-- Rejilla de telemetría -->
        <line x1="0" y1="125" x2="680" y2="125" stroke="#1B2340" stroke-dasharray="4 4" />
        <line x1="340" y1="0" x2="340" y2="250" stroke="#1B2340" stroke-dasharray="4 4" />

        <!-- PANELES SOLARES (SUPERIOR E INFERIOR) -->
        <g v-if="installedSlots.has('paneles_cortos')">
          <rect x="285" y="28" width="55" height="48" fill="#1B2340" stroke="#4FD1C5" stroke-width="2" />
          <rect x="285" y="174" width="55" height="48" fill="#1B2340" stroke="#4FD1C5" stroke-width="2" />
          <text x="290" y="22" fill="#4FD1C5" font-size="9">PANEL Si-380</text>
        </g>
        <g v-else-if="installedSlots.has('paneles_dobles')">
          <rect x="265" y="14" width="95" height="62" fill="#1B2340" stroke="#4FD1C5" stroke-width="2" />
          <line x1="312" y1="14" x2="312" y2="76" stroke="#4FD1C5" />
          <rect x="265" y="174" width="95" height="62" fill="#1B2340" stroke="#4FD1C5" stroke-width="2" />
          <line x1="312" y1="174" x2="312" y2="236" stroke="#4FD1C5" />
          <text x="268" y="11" fill="#4FD1C5" font-size="9">GA-AS 550W</text>
        </g>
        <g v-else-if="installedSlots.has('paneles_rtg')">
          <rect x="255" y="10" width="115" height="66" fill="#1B2340" stroke="#FFB000" stroke-width="2" />
          <rect x="255" y="174" width="115" height="66" fill="#1B2340" stroke="#FFB000" stroke-width="2" />
          <circle cx="235" cy="82" r="10" fill="#FF7A3D" stroke="#F5D36B" stroke-width="2" />
          <text x="256" y="9" fill="#FFB000" font-size="9">MATRIZ + RTG 780W</text>
        </g>

        <!-- TOBERA / MOTOR (IZQUIERDA - POPA) -->
        <g v-if="installedSlots.has('tobera_compacta')">
          <polygon points="155,102 190,110 190,140 155,148" fill="#3A4666" stroke="#FFB000" stroke-width="2" />
          <text x="95" y="128" fill="#FFB000" font-size="9">M-280 (285s)</text>
        </g>
        <g v-else-if="installedSlots.has('tobera_campana')">
          <polygon points="135,92 190,106 190,144 135,158" fill="#3A4666" stroke="#FFB000" stroke-width="2" />
          <text x="68" y="128" fill="#FFB000" font-size="9">HYPER-320 (320s)</text>
        </g>
        <g v-else-if="installedSlots.has('tobera_expansiva')">
          <polygon points="115,82 190,104 190,146 115,168" fill="#1B2340" stroke="#F5D36B" stroke-width="2.5" />
          <ellipse cx="115" cy="125" rx="6" ry="43" fill="none" stroke="#4FD1C5" stroke-width="1.5" />
          <text x="40" y="128" fill="#F5D36B" font-size="9">METHALOX (360s)</text>
        </g>

        <!-- CUERPO CENTRAL DE LA NAVE (4 HABITACIONES CONTIGUAS) -->
        <rect x="190" y="80" width="75" height="90" fill="#1B2340" stroke="#3A4666" stroke-width="2" />
        <text x="198" y="96" fill="#8FA3BF" font-size="8">SISTEMAS</text>

        <rect
          x="265"
          y="80"
          width="75"
          height="90"
          fill="#1B2340"
          :stroke="installedSlots.has('eclss_blindado') ? '#7BD88F' : '#3A4666'"
          stroke-width="2"
        />
        <text x="275" y="96" fill="#7BD88F" font-size="8">VIDA / O2</text>

        <rect x="340" y="80" width="80" height="90" fill="#1B2340" stroke="#3A4666" stroke-width="2" />
        <text x="348" y="96" fill="#4FD1C5" font-size="8">LABORATORIO</text>

        <polygon
          points="420,80 485,96 485,154 420,170"
          fill="#1B2340"
          stroke="#FFB000"
          stroke-width="2"
        />
        <rect x="445" y="108" width="24" height="34" fill="#2E6FD8" opacity="0.65" rx="3" />
        <text x="425" y="96" fill="#FFB000" font-size="8">CABINA</text>

        <!-- ANTENA (PROA SUPERIOR) -->
        <g v-if="installedSlots.has('antena_dipolo')">
          <line x1="455" y1="88" x2="475" y2="50" stroke="#8FA3BF" stroke-width="2" />
          <circle cx="475" cy="50" r="4" fill="#4FD1C5" />
          <text x="484" y="54" fill="#8FA3BF" font-size="9">Banda-S</text>
        </g>
        <g v-else-if="installedSlots.has('antena_plato')">
          <line x1="455" y1="88" x2="465" y2="56" stroke="#8FA3BF" stroke-width="2" />
          <path d="M 448 48 Q 468 68 486 46" fill="none" stroke="#4FD1C5" stroke-width="3" />
          <text x="492" y="54" fill="#4FD1C5" font-size="9">Banda-X 2Mbps</text>
        </g>
        <g v-else-if="installedSlots.has('antena_laser')">
          <rect x="448" y="52" width="26" height="18" fill="#1B2340" stroke="#F5D36B" stroke-width="2" />
          <line x1="474" y1="61" x2="525" y2="42" stroke="#4FD1C5" stroke-width="1.5" stroke-dasharray="3 2" />
          <text x="485" y="68" fill="#F5D36B" font-size="9">Óptica Ka</text>
        </g>

        <!-- PAYLOADS CIENTÍFICOS Y ROBOT ACOPLADOS -->
        <g v-if="installedSlots.has('payload_espectrometro')">
          <rect x="350" y="142" width="28" height="22" fill="#0B0E1A" stroke="#4FD1C5" stroke-width="1.5" />
          <text x="353" y="156" fill="#4FD1C5" font-size="7">SPEC</text>
        </g>
        <g v-if="installedSlots.has('payload_radar')">
          <rect x="382" y="142" width="30" height="22" fill="#0B0E1A" stroke="#FFB000" stroke-width="1.5" />
          <text x="385" y="156" fill="#FFB000" font-size="7">RADAR</text>
        </g>
        <g v-if="installedSlots.has('payload_biocapsula')">
          <rect x="350" y="114" width="62" height="20" fill="#0B0E1A" stroke="#7BD88F" stroke-width="1.5" />
          <text x="360" y="127" fill="#7BD88F" font-size="7">BIOCÁPSULA</text>
        </g>
        <g v-if="installedSlots.has('modulo_robot')">
          <rect x="198" y="140" width="56" height="24" fill="#0B0E1A" stroke="#F5D36B" stroke-width="1.5" />
          <text x="204" y="155" fill="#F5D36B" font-size="7">ROBOT KIBO</text>
        </g>
      </svg>
    </div>

    <!-- Roster de Tripulación con Sprites Pixel Art Animados y Estado de Ánimo -->
    <div class="crew-strip">
      <div v-for="member in mission.tripulacion" :key="member.id" class="crew-card">
        <div class="crew-sprite-row">
          <PixelSprite
            :animacion="obtenerSpriteTripulante(member.especialidad, member.es_jugador)"
            :width="64"
            :height="76"
            :animar="false"
            :animo="member.estado_animo"
          />
          <div class="crew-info-col">
            <div class="crew-top">
              <span
                class="mood-dot"
                :style="{ backgroundColor: moodColor(member.estado_animo) }"
              ></span>
              <span class="mood-tag" :style="{ color: moodColor(member.estado_animo) }">
                {{ member.estado_animo.toUpperCase() }}
              </span>
              <span class="exp-tag">EXP {{ member.experiencia }}/5</span>
            </div>
            <div class="crew-name">{{ member.nombre }}</div>
            <div class="crew-role">{{ member.rol }} · [{{ member.especialidad.toUpperCase() }}]</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.schematic-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.schematic-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
}
.label-amber {
  color: var(--amber);
  font-weight: 700;
  font-size: 13px;
  margin-right: 10px;
}
.dest-tag {
  font-size: 11px;
  color: var(--cyan);
  border: 1px solid var(--steel);
  padding: 2px 6px;
  border-radius: 3px;
}
.sub-caption {
  font-size: 11px;
  color: var(--mist);
}
.svg-stage {
  border: 1px solid var(--steel);
  border-radius: 6px;
  overflow: hidden;
  background: var(--void);
}
.ship-svg {
  width: 100%;
  height: auto;
  display: block;
}
.crew-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}
.crew-card {
  background: var(--void);
  border: 1px solid var(--steel);
  border-radius: 4px;
  padding: 8px;
  font-size: 11px;
}
.crew-sprite-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.crew-info-col {
  flex: 1;
}
.crew-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.mood-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}
.mood-tag {
  font-weight: 700;
  font-size: 10px;
}
.exp-tag {
  margin-left: auto;
  color: var(--mist);
  font-size: 10px;
}
.crew-name {
  color: var(--bone);
  font-weight: 600;
}
.crew-role {
  color: var(--mist);
  font-size: 10px;
}
</style>
