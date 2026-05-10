/** Central API client — reads VITE_API_URL from env or falls back to proxy path */
const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── Match types ──────────────────────────────────────────────────────────────
export interface Match {
  id: number
  home_team: string
  away_team: string
  league: string
  season: string
  match_date: string
  status: 'scheduled' | 'live' | 'finished'
  home_goals: number
  away_goals: number
  home_form: number
  away_form: number
  venue: string
}

export interface ShapFeature {
  feature: string
  shap_value: number
  raw_value: number
}

export interface Prediction {
  match_id: number
  minute: number
  home_goals: number
  away_goals: number
  event_type: string
  event_team: string
  prob_home_win: number
  prob_draw: number
  prob_away_win: number
  shap_features: ShapFeature[]
  inference_ms?: number
}

export interface Player {
  id: number
  name: string
  team: string
  position: string
  salary: number
  expected_points: number
  recent_rating: number
  goals_per_match: number
  assists_per_match: number
}

export interface LineupResponse {
  status: string
  selected_players: Player[]
  total_salary: number
  total_expected_points: number
  formation: string
}

// ── API functions ────────────────────────────────────────────────────────────
export const api = {
  getMatches: () => apiFetch<Match[]>('/api/v1/matches'),
  getMatch:   (id: number) => apiFetch<Match>(`/api/v1/matches/${id}`),
  getPrediction: (id: number) => apiFetch<Prediction>(`/api/v1/matches/${id}/prediction`),
  getPlayers: () => apiFetch<Player[]>('/api/v1/players'),
  optimizeLineup: (body: { budget: number; formation: string; players: Player[] }) =>
    apiFetch<LineupResponse>('/api/v1/lineup/optimize', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}

// ── WebSocket URL builder ────────────────────────────────────────────────────
export function wsUrl(matchId: number): string {
  const wsBase = import.meta.env.VITE_WS_URL
    ?? (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host
  return `${wsBase}/ws/match/${matchId}`
}
