import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export interface Scenario {
  id: string; name: string; objective: string; destination: string
  duration_days: number; required_comm_distance_km: number; budget_limit_usd: number
  orbit_origin_radius_km: number; orbit_destination_radius_km: number; data_source: string
}
export interface Component {
  id: string; name: string; category: string; mass_kg: number
  power_consumption_w: number; power_generation_w: number; cost_usd: number
  comm_range_km: number; comm_data_rate_kbps: number; battery_wh: number
  description: string; data_source: string
}
export interface LaunchVehicle {
  id: string; name: string; payload_capacity_kg: number
  compatible_destinations: string[]; cost_usd: number; data_source: string
}
export interface SimResult {
  mission_name: string; feasible: boolean; score: number
  mass: any; power: any; communications: any; budget: any; orbit: any
  events: string[]; explanation: string
}

export const SpaceApi = {
  scenarios: () => api.get<Scenario[]>('/scenarios').then(r => r.data),
  components: () => api.get<Component[]>('/components').then(r => r.data),
  launchVehicles: () => api.get<LaunchVehicle[]>('/launch-vehicles').then(r => r.data),
  createMission: (p: any) => api.post('/missions', p).then(r => r.data),
  validate: (p: any) => api.post<SimResult>('/missions/validate', p).then(r => r.data),
  runSimulation: (p: any) => api.post<SimResult>('/simulations', p).then(r => r.data),
}