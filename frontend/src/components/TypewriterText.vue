<script setup lang="ts">
import { computed, watch } from 'vue'
import { useTypewriter } from '../composables/useTypewriter'

const props = withDefaults(
  defineProps<{
    text: string
    speed?: number
    sound?: boolean
    skipHint?: string
  }>(),
  {
    speed: 26,
    sound: true,
    skipHint: '',
  },
)

const emit = defineEmits<{
  (e: 'complete'): void
}>()

const textoFuente = computed(() => props.text)
const { textoMostrado, estaEscribiendo, completado, saltar } = useTypewriter(textoFuente, {
  velocidadMs: props.speed,
  sonido: props.sound,
})

// Notificar al padre cuando termina la animación.
watch(
  completado,
  (v) => {
    if (v) emit('complete')
  },
  { immediate: true },
)
</script>

<template>
  <span class="typewriter-text" :class="{ typing: estaEscribiendo }" @click="saltar" role="button" tabindex="0" @keydown.enter="saltar" @keydown.space.prevent="saltar">
    {{ textoMostrado }}<span v-if="estaEscribiendo" class="typewriter-caret" aria-hidden="true">▌</span>
    <span v-if="estaEscribiendo && skipHint" class="typewriter-skip-hint">{{ skipHint }}</span>
  </span>
</template>

<style scoped>
.typewriter-text {
  cursor: pointer;
  white-space: pre-wrap;
}
.typewriter-caret {
  display: inline-block;
  margin-left: 1px;
  color: var(--amber, #ffb000);
  animation: tw-blink 0.7s steps(2, start) infinite;
}
.typewriter-skip-hint {
  margin-left: 8px;
  font-size: 0.8em;
  color: var(--mist, #9aa0b8);
  font-style: italic;
}
@keyframes tw-blink {
  0%,
  50% {
    opacity: 1;
  }
  50.01%,
  100% {
    opacity: 0;
  }
}
</style>