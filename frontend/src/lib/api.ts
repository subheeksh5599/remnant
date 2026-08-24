// REMNANT — typed API client. Mirrors the backend domain model.

// In dev, Vite proxies /api -> backend (:8000). In production, the backend is
// served on the same origin (reverse proxy) or API_BASE is set explicitly.
const API_BASE = (import.meta.env?.VITE_API_BASE as string | undefined) ?? ''

export type EvidenceStrength = 'low' | 'medium' | 'high'
export type ResolutionState =
  | 'unresolved' | 'dormant' | 'fulfilled' | 'rejected'
  | 'partially_fulfilled' | 'revisited' | 'under_experiment'
  | 'validated' | 'disproven' | 'uncertain'

export interface Source {
  kind: string
  source_id: string
  url?: string | null
}

export interface AudienceExpression {
  expression_id: string
  text: string
  source: Source
  occurred_at: string
  audience_segment?: string | null
  creator_response?: string | null
}

export interface HypothesisAssessment {
  hypothesis: 'H1' | 'H2' | 'H3' | 'H4'
  supporting_evidence: string[]
  contradicting_evidence: string[]
  evidence_strength: EvidenceStrength
  summary: string
}

export interface Experiment {
  experiment_id: string
  remnant_id: string
  hypothesis: string
  test: string
  metric: string
  threshold_value: number
  threshold_operator: 'gte' | 'lte'
  prediction: string
  success_threshold: string
  failure_condition: string
  status: 'planned' | 'running' | 'completed'
  observed_value?: number | null
  crossed_threshold?: boolean | null
  outcome?: string | null
}

export interface CreatorDecision {
  decision: 'adopted' | 'rejected' | 'deferred' | 'no_response'
  reason?: string | null
  decided_at?: string | null
}

export interface Remnant {
  remnant_id: string
  title: string
  underlying_need_hypothesis: string
  created_at: string
  expressions: AudienceExpression[]
  creator_decisions: CreatorDecision[]
  assessments: HypothesisAssessment[]
  experiments: Experiment[]
  resolution_state: ResolutionState
  current_relevance: 'low' | 'medium' | 'high' | 'uncertain'
  history: string[]
  mind_notes: string[]
}

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    // Parse the consistent error schema when available.
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.error?.message ?? `${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

// --- runtime response validation (trust nothing from the wire) ------------------

export function isRemnant(x: unknown): x is Remnant {
  if (typeof x !== 'object' || x === null) return false
  const r = x as Record<string, unknown>
  return (
    typeof r.remnant_id === 'string' &&
    typeof r.title === 'string' &&
    Array.isArray(r.expressions) &&
    Array.isArray(r.assessments) &&
    Array.isArray(r.experiments)
  )
}

export function isRemnantList(x: unknown): x is Remnant[] {
  return Array.isArray(x) && x.every(isRemnant)
}

export const api = {
  health: () => j<{ ok: boolean; mind: boolean; remnants: number }>('/api/v1/health'),
  remnants: () => j<Remnant[]>('/api/v1/remnants'),
  createRemnant: (title: string, need: string) =>
    j<Remnant>('/api/v1/remnants', {
      method: 'POST',
      body: JSON.stringify({ title, underlying_need_hypothesis: need }),
    }),
  remnant: (rid: string) => j<Remnant>(`/api/v1/remnants/${rid}`),
  provenance: (rid: string) =>
    j<{ remnant_id: string; expressions: unknown[]; creator_decisions: unknown[]; state_transitions: unknown[]; experiments: unknown[] }>(
      `/api/v1/remnants/${rid}/provenance`,
    ),
  addExpression: (rid: string, text: string, sourceKind: string, sid: string, occurredAt?: string) =>
    j<Remnant>(`/api/v1/remnants/${rid}/expressions`, {
      method: 'POST',
      body: JSON.stringify({
        text,
        source_kind: sourceKind,
        source_id: sid,
        occurred_at: occurredAt,
      }),
    }),
  addDecision: (rid: string, decision: string, reason?: string) =>
    j<Remnant>(`/api/v1/remnants/${rid}/decisions`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason }),
    }),
  planExperiment: (rid: string) =>
    j<Experiment>(`/api/v1/remnants/${rid}/experiments`, { method: 'POST' }),
  recordOutcome: (rid: string, eid: string, observedValue: number) =>
    j<Remnant>(`/api/v1/remnants/${rid}/experiments/${eid}/outcome`, {
      method: 'POST',
      body: JSON.stringify({ observed_value: observedValue }),
    }),
  belief: (rid: string) =>
    j<{ remnant_id: string; belief: string }>(`/api/v1/remnants/${rid}/belief`),
  observatoryRun: () =>
    j<{ surfaced: Record<string, unknown>[]; action_log: Record<string, unknown>[] }>('/api/v1/observatory/run', {
      method: 'POST',
    }),
  mind: () => j<{ ok: boolean; name?: string; cognition_balance?: number; available: boolean }>('/api/v1/mind'),
}