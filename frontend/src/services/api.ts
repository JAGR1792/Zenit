const BASE = '/api/v1'

async function request(path: string, init?: RequestInit): Promise<any> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const SpaceApi = {
  health: () => request('/health'),
  components: () => request('/catalog/components'),
  destinations: () => request('/catalog/destinations'),
  crew: () => request('/catalog/crew'),
  financing: () => request('/catalog/financing'),
  createMission: (p: any) => request('/missions', { method: 'POST', body: JSON.stringify(p) }),
  getMission: (id: string) => request(`/missions/${id}`),
  decision: (id: string, payload: any) => request(`/missions/${id}/decisions`, { method: 'POST', body: JSON.stringify(payload) }),
  advance: (id: string) => request(`/missions/${id}/advance`, { method: 'POST' }),
  resolveEvent: (id: string, eventId: string, optionId: string, crewId?: string) =>
    request(`/missions/${id}/events/${eventId}/resolve`, { method: 'POST', body: JSON.stringify({ option_id: optionId, crew_id: crewId }) }),
  report: (id: string) => request(`/missions/${id}/report`),
}
