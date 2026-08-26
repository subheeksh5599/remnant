// REMNANT — typed API client. Mirrors the backend domain model exactly.
// In dev, Vite proxies /api -> backend (:8000). In production, the backend is
// served on the same origin (reverse proxy) or API_BASE is set explicitly.
const API_BASE = (import.meta.env?.VITE_API_BASE as string | undefined) ?? ''

export type EvidenceStrength = 'low' | 'medium' | 'high'
export type ResolutionState =
  | 'candidate' | 'insufficient_evidence' | 'unresolved' | 'dormant' | 'fulfilled' | 'rejected'
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
  author?: string | null
  audience_segment?: string | null
  ingested_at?: string
  url?: string | null
  creator_response?: string | null
}

export interface CreatorDecision {
  decision: 'adopted' | 'rejected' | 'deferred' | 'no_response'
  reason?: string | null
  decided_at: string
}

export interface HypothesisAssessment {
  hypothesis: 'H1' | 'H2' | 'H3' | 'H4'
  supporting_evidence: string[]
  contradicting_evidence: string[]
  evidence_strength: EvidenceStrength
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
  status: 'planned' | 'completed'
  observed_value?: number | null
  crossed_threshold?: boolean | null
  outcome?: string | null
  created_at: string
  decided_at?: string | null
  target_population?: string | null
  measurement_window?: string | null
  defined_by_creator?: boolean
}

export interface StateTransition {
  from: string
  to: string
  at: string
  reason: string
}

export interface Remnant {
  schema_version: number
  remnant_id: string
  title: string
  underlying_need_hypothesis: string
  resolution_state: ResolutionState
  created_at: string
  updated_at: string
  expressions: AudienceExpression[]
  creator_decisions: CreatorDecision[]
  assessments: HypothesisAssessment[]
  experiments: Experiment[]
  history: string[]
  state_transitions: StateTransition[]
  discovered_links?: DiscoveryLink[]
}

export interface DiscoveryLink {
  expression_id?: string
  text?: string
  against_expression_id: string
  against_text: string
  relationship: 'same_need' | 'candidate' | 'insufficient_evidence' | 'different_need'
  confidence: string
  supporting: string[]
  conflicting: string[]
  uncertainty: string[]
  shared_concepts: string[]
}

export interface DiscoveryEntry {
  action: 'linked' | 'created'
  remnant: string
  expression: string
  verdict: string
  evidence: string
}

export interface MindState {
  ok: boolean
  mind_id?: string
  name?: string
  enabled?: boolean
  cognition_balance?: number
  available: boolean
  connected?: boolean
  error?: string
}

export interface MindsStatus {
  connected: boolean
  kind: 'user' | 'env' | 'none'
  ok: boolean
  mind_id?: string | null
  mind_name?: string | null
  error?: string | null
}

export interface ObservationCandidate {
  remnant_id: string
  title: string
  recent_expressions: number
  historical_expressions: number
  current_expressions: number
  state: string
  candidate: string
  recommended_action: string
  approval_required: boolean
}

export interface ObservatoryAction {
  action_id: string
  at: string
  remnant_id: string
  action: string
  reason: string
}

export interface AdversarialResult {
  expression_a: string
  expression_b: string
  relationship: 'same_need' | 'candidate' | 'different_need' | 'insufficient_evidence'
  confidence: 'high' | 'medium' | 'candidate' | 'low'
  supporting: string[]
  conflicting: string[]
  uncertainty: string[]
  reasoning: string[]
  shared_concepts: string[]
}

export interface AskAnswers {
  what_do_you_currently_believe: string
  why: string
  what_evidence_supports_this: string
  what_contradicts_it: string
  what_should_we_test_next: string
  what_changed_since_the_last_experiment: string
  resolution_state: string
}

export interface AuditEvent {
  event: string
  [k: string]: unknown
}

export interface ProvenancePayload {
  remnant_id: string
  expressions: {
    expression_id: string
    text: string
    source: Source
    occurred_at: string
  }[]
  creator_decisions: CreatorDecision[]
  state_transitions: StateTransition[]
  experiments: {
    experiment_id: string
    test: string
    metric: string
    threshold_value: number
    threshold_operator: string
    status: string
    observed_value?: number | null
    crossed_threshold?: boolean | null
    outcome?: string | null
  }[]
}

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    // Parse the consistent error schema when available.
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.error?.message ?? detail?.detail?.error?.message ?? `${res.status} ${res.statusText}`)
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
  health: () => j<{ ok: boolean; mind: boolean; remnants: number; env: { mind_configured: boolean; storage_mode?: string } }>('/api/v1/health'),
  readyz: () => j<{ ok: boolean; remnants: number }>('/api/v1/readyz'),
  livez: () => j<{ ok: boolean }>('/api/v1/livez'),
  remnants: () => j<Remnant[]>('/api/v1/remnants'),
  createRemnant: (title: string, need: string) =>
    j<Remnant>('/api/v1/remnants', {
      method: 'POST',
      body: JSON.stringify({ title, underlying_need_hypothesis: need }),
    }),
  remnant: (rid: string) => j<Remnant>(`/api/v1/remnants/${rid}`),
  provenance: (rid: string) => j<ProvenancePayload>(`/api/v1/remnants/${rid}/provenance`),
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
  planExperiment: (rid: string, overrides?: { metric?: string; threshold?: number; target_population?: string; measurement_window?: string }) =>
    j<Experiment>(`/api/v1/remnants/${rid}/experiments`, {
      method: 'POST',
      body: JSON.stringify(overrides ?? {}),
    }),
  recordOutcome: (rid: string, eid: string, observedValue: number) =>
    j<Remnant>(`/api/v1/remnants/${rid}/experiments/${eid}/outcome`, {
      method: 'POST',
      body: JSON.stringify({ observed_value: observedValue }),
    }),
  belief: (rid: string) => j<{ remnant_id: string; belief: string }>(`/api/v1/remnants/${rid}/belief`),
  ask: (rid: string) => j<{ remnant_id: string; answers: AskAnswers }>(`/api/v1/remnants/${rid}/ask`),
  adversarial: (a: string, b: string) =>
    j<AdversarialResult>('/api/v1/adversarial/analyze', {
      method: 'POST',
      body: JSON.stringify({ expression_a: a, expression_b: b }),
    }),
  observatoryRun: () =>
    j<{ surfaced: ObservationCandidate[]; action_log: ObservatoryAction[] }>('/api/v1/observatory/run', {
      method: 'POST',
    }),
  observatoryActions: () => j<{ actions: ObservatoryAction[] }>('/api/v1/observatory/actions'),
  mind: () => j<MindState>('/api/v1/mind'),
  mindsConnect: (builderApiKey: string, mindId?: string) =>
    j<{ connected: boolean; mind_id: string; mind_name?: string; note: string }>('/api/v1/minds/connect', {
      method: 'POST',
      body: JSON.stringify({ builder_api_key: builderApiKey, mind_id: mindId }),
    }),
  mindsDisconnect: () =>
    j<{ connected: boolean }>('/api/v1/minds/disconnect', { method: 'POST' }),
  mindsStatus: () => j<MindsStatus>('/api/v1/minds/status'),
  mindsRecover: (rid: string) =>
    j<{ remnant_id: string; recovered: boolean; memory_lines?: string[]; count?: number; note?: string; error?: string }>(`/api/v1/minds/recover/${rid}`),
  audit: (limit = 100) => j<{ events: AuditEvent[]; count: number }>(`/api/v1/audit?limit=${limit}`),
  demoLoad: () =>
    j<{ loaded: number; synthetic: boolean; label: string; discovery?: DiscoveryEntry[]; note?: string }>('/api/v1/demo/load', { method: 'POST' }),
  demoReconnect: () =>
    j<{ reconnected: boolean; remnants_survived: number; note: string }>('/api/v1/demo/reconnect', { method: 'POST' }),
}

// ---------- derived helpers shared by pages ----------

export function fmtDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toISOString().slice(0, 10)
}

export function shortId(id: string): string {
  return id.slice(0, 8)
}

export function isSynthetic(r: Remnant): boolean {
  return r.history.some((h) => h.toLowerCase().includes('synthetic'))
}

export function firstDetected(r: Remnant): string | null {
  if (!r.expressions.length) return null
  return r.expressions.reduce((a, b) => (a.occurred_at < b.occurred_at ? a : b)).occurred_at
}

export function lastDetected(r: Remnant): string | null {
  if (!r.expressions.length) return null
  return r.expressions.reduce((a, b) => (a.occurred_at > b.occurred_at ? a : b)).occurred_at
}

export function currentRelevance(r: Remnant): 'high' | 'medium' | 'low' {
  const last = lastDetected(r)
  if (!last) return 'low'
  const days = (Date.now() - new Date(last).getTime()) / 86400000
  if (days <= 60) return 'high'
  if (days <= 365) return 'medium'
  return 'low'
}

export function h1Strength(r: Remnant): EvidenceStrength {
  const h1 = r.assessments.find((a) => a.hypothesis === 'H1')
  return h1?.evidence_strength ?? 'low'
}

export const HYPOTHESIS_LABELS: Record<string, { label: string; short: string }> = {
  H1: { label: 'Persistent unresolved need', short: 'persistent need' },
  H2: { label: 'Independent recurrence', short: 'independent recurrence' },
  H3: { label: 'Temporary trend', short: 'temporary trend' },
  H4: { label: 'Semantic coincidence', short: 'semantic coincidence' },
}

export const STATE_LABELS: Record<string, string> = {
  candidate: 'Candidate (discovered)',
  insufficient_evidence: 'Insufficient evidence',
  unresolved: 'Unresolved',
  dormant: 'Dormant',
  fulfilled: 'Fulfilled',
  rejected: 'Rejected',
  partially_fulfilled: 'Partially fulfilled',
  revisited: 'Revisited',
  under_experiment: 'Under experiment',
  validated: 'Validated',
  disproven: 'Disproven',
  uncertain: 'Uncertain',
}

export const RESOLUTION_COLORS: Record<string, 'badge-ok' | 'badge-warn' | 'badge-err' | 'badge-info' | 'badge-neutral'> = {
  candidate: 'badge-info',
  insufficient_evidence: 'badge-neutral',
  unresolved: 'badge-warn',
  dormant: 'badge-neutral',
  fulfilled: 'badge-ok',
  rejected: 'badge-err',
  partially_fulfilled: 'badge-info',
  revisited: 'badge-info',
  under_experiment: 'badge-info',
  validated: 'badge-ok',
  disproven: 'badge-err',
  uncertain: 'badge-warn',
}