<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <section class="space-y-4">
      <div class="bg-slate-800 rounded p-4">
        <h2 class="font-semibold mb-3">Mission configuration</h2>
        <label class="block text-sm mb-1">Mission name</label>
        <input v-model="name" class="w-full bg-slate-700 rounded px-3 py-2 mb-3" />

        <label class="block text-sm mb-1">Scenario</label>
        <select v-model="scenarioId" class="w-full bg-slate-700 rounded px-3 py-2 mb-3">
          <option v-for="s in scenarios" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>

        <label class="block text-sm mb-1">Launch vehicle</label>
        <select v-model="launchVehicleId" class="w-full bg-slate-700 rounded px-3 py-2 mb-3">
          <option v-for="lv in launchVehicles" :key="lv.id" :value="lv.id">{{ lv.name }}</option>
        </select>

        <label class="block text-sm mb-1">Components</label>
        <div class="grid grid-cols-2 gap-2 max-h-64 overflow-auto">
          <label v-for="c in components" :key="c.id" class="flex items-center gap-2 text-sm">
            <input type="checkbox" :value="c.id" v-model="selectedComponents" />
            {{ c.name }}
          </label>
        </div>
      </div>

      <div class="flex gap-3">
        <button @click="validate" class="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded">Validate</button>
        <button @click="simulate" class="bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded">Run simulation</button>
      </div>
    </section>

    <section class="space-y-4">
      <div v-if="result" class="bg-slate-800 rounded p-4">
        <h2 class="font-semibold mb-2">{{ result.mission_name }}</h2>
        <p class="mb-2" :class="result.feasible ? 'text-emerald-400' : 'text-red-400'">
          {{ result.feasible ? 'FEASIBLE' : 'NOT FEASIBLE' }} — score {{ result.score }}/100
        </p>
        <p class="text-sm text-slate-300 mb-3">{{ result.explanation }}</p>
        <ul class="text-sm space-y-1">
          <li v-for="e in result.events" :key="e">{{ e }}</li>
        </ul>
        <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div>Mass: {{ result.mass.total_kg.toFixed(1) }} / {{ result.mass.capacity_kg.toFixed(1) }} kg</div>
          <div>Power net: {{ result.power.net_w.toFixed(1) }} W</div>
          <div>Budget: ${{ result.budget.total_usd.toFixed(0) }}</div>
          <div>Delta-v: {{ result.orbit.delta_v_ms.toFixed(0) }} m/s</div>
        </div>
      </div>
      <div v-else class="text-slate-500">Run validation or simulation to see results.</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { SpaceApi } from '../services/api'

const scenarios = ref<any[]>([])
const components = ref<any[]>([])
const launchVehicles = ref<any[]>([])

const name = ref('My Mission')
const scenarioId = ref('')
const launchVehicleId = ref('')
const selectedComponents = ref<string[]>([])
const result = ref<any>(null)

onMounted(async () => {
  scenarios.value = await SpaceApi.scenarios()
  components.value = await SpaceApi.components()
  launchVehicles.value = await SpaceApi.launchVehicles()
  if (scenarios.value.length) scenarioId.value = scenarios.value[0].id
  if (launchVehicles.value.length) launchVehicleId.value = launchVehicles.value[0].id
})

function payload() {
  return {
    name: name.value,
    scenario_id: scenarioId.value,
    launch_vehicle_id: launchVehicleId.value,
    component_ids: selectedComponents.value,
  }
}

async function validate() {
  result.value = await SpaceApi.validate(payload())
}

async function simulate() {
  result.value = await SpaceApi.runSimulation(payload())
}
</script>