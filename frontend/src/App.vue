<template>
  <div class="min-h-screen bg-slate-900 text-slate-100">
    <header class="border-b border-slate-700 px-6 py-4">
      <h1 class="text-xl font-bold">Space Mission Design Game</h1>
      <p class="text-sm text-slate-400">Design, validate and simulate a space mission.</p>
    </header>
    <main class="p-6">
      <MissionView />
    </main>
  </div>
</template>

<script setup lang="ts">
import MissionView from './views/MissionView.vue'
</script>