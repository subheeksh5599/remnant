// REMNANT — typed API client. Mirrors the backend domain model.

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
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  health: () => j<{ ok: boolean; mind: boolean; remnants: number }>('/api/health'),
  remnants: () => j<Remnant[]>('/api/remnants'),
  createRemnant: (title: string, need: string) =>
    j<Remnant>('/api/remnants', {
      method: 'POST',
      body: JSON.stringify({ title, underlying_need_hypothesis: need }),
    }),
  remnant: (rid: string) => j<Remnant>(`/api/remnants/${rid}`),
  addExpression: (rid: string, text: string, sourceKind: string, sid: string, occurredAt?: string) =>
    j<Remnant>(`/api/remnants/${rid}/expressions`, {
      method: 'POST',
      body: JSON.stringify({
        text,
        source_kind: sourceKind,
        source_id: sid,
        occurred_at: occurredAt,
      }),
    }),
  addDecision: (rid: string, decision: string, reason?: string) =>
    j<Remnant>(`/api/remnants/${rid}/decisions`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason }),
    }),
  planExperiment: (rid: string) =>
    j<Experiment>(`/api/remnants/${rid}/experiments`, { method: 'POST' }),
  recordOutcome: (rid: string, eid: string, observedValue: number) =>
    j<Remnant>(`/api/remnants/${rid}/experiments/${eid}/outcome`, {
      method: 'POST',
      body: JSON.stringify({ observed_value: observedValue }),
    }),
  belief: (rid: string) =>
    j<{ remnant_id: string; belief: string }>(`/api/remnants/${rid}/belief`),
  mind: () => j<{ ok: boolean; name?: string; cognition_balance?: number; available: boolean }>('/api/mind'),
}