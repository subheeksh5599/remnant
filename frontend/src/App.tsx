import { useEffect, useState } from 'react'
import { api, type Remnant, type Experiment } from './lib/api'

// ---------- helpers ----------------------------------------------------------

function utcDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toISOString().slice(0, 10)
}

function stateLabel(s: string): string {
  return s.replace(/_/g, ' ')
}

function Timeline({ remnant }: { remnant: Remnant }) {
  const years: Record<number, number> = {}
  for (const e of remnant.expressions) {
    const y = new Date(e.occurred_at).getFullYear()
    years[y] = (years[y] ?? 0) + 1
  }
  if (remnant.expressions.length === 0) return <div className="empty">no historical expressions yet</div>
  const min = Math.min(...Object.keys(years).map(Number))
  const max = Math.max(...Object.keys(years).map(Number))
  const rows: React.ReactNode[] = []
  for (let y = min; y <= max; y++) {
    rows.push(
      <span key={y} className="tl-year">
        {y}{' '}
        {years[y] ? (
          <span className="tl-dot">{'●'.repeat(Math.min(years[y], 6))}</span>
        ) : (
          <span className="tl-empty">○</span>
        )}
      </span>,
    )
  }
  return <div className="timeline">{rows}</div>
}

function Provenance({ remnant }: { remnant: Remnant }) {
  const chain: { lbl: string; text: string }[] = []
  chain.push({ lbl: 'first source', text: remnant.expressions[0]?.text ?? '—' })
  chain.push({ lbl: 'candidate need', text: remnant.underlying_need_hypothesis })
  chain.push({
    lbl: 'resolution state',
    text: stateLabel(remnant.resolution_state),
  })
  if (remnant.experiments.length > 0) {
    const last = remnant.experiments[remnant.experiments.length - 1]
    chain.push({ lbl: 'experiment', text: last.test })
    chain.push({ lbl: 'outcome', text: last.observed_value !== null && last.observed_value !== undefined ? `${last.observed_value} → ${last.outcome ?? 'pending'}` : 'pending' })
  }
  return (
    <div className="provenance">
      {chain.map((n, i) => (
        <div key={i}>
          <div className="prov-node">
            <div className="lbl">{n.lbl}</div>
            {n.text}
          </div>
          {i < chain.length - 1 && <div className="prov-arrow">↓</div>}
        </div>
      ))}
    </div>
  )
}

// ---------- screens ----------------------------------------------------------

function RemnantCard({ r, onClick }: { r: Remnant; onClick: () => void }) {
  const h1 = r.assessments.find((a) => a.hypothesis === 'H1')
  const n = r.expressions.length
  return (
    <div className="card" onClick={onClick}>
      <h3>REMNANT #{r.remnant_id.slice(0, 6).toUpperCase()}</h3>
      <div className="meta">
        <span>{r.title}</span>
        <span className={`pill ${h1?.evidence_strength ?? 'low'}`}>{h1?.evidence_strength ?? 'low'} evidence</span>
      </div>
      <div className="meta" style={{ marginTop: 6 }}>
        <span>{n} expressions</span>
        <span>first {utcDate(r.expressions[0]?.occurred_at ?? '')}</span>
        <span className={`state`} style={{ color: 'var(--warn)' }}>{stateLabel(r.resolution_state)}</span>
      </div>
      <div className="need">“{r.underlying_need_hypothesis}”</div>
    </div>
  )
}

function RemnantsScreen({ remnants, onOpen }: { remnants: Remnant[]; onOpen: (r: Remnant) => void }) {
  const [title, setTitle] = useState('')
  const [need, setNeed] = useState('')
  const [busy, setBusy] = useState(false)

  const create = async () => {
    if (!title.trim() || !need.trim()) return
    setBusy(true)
    try {
      await api.createRemnant(title.trim(), need.trim())
      setTitle('')
      setNeed('')
    } finally {
      setBusy(false)
    }
    window.location.reload()
  }

  return (
    <>
      <div className="page-title">REMNANTS</div>
      <div className="page-desc">
        A REMNANT is a time-aware hypothesis about an unresolved audience need — not a note,
        not a saved comment. It preserves the underlying need candidate, its historical
        expressions, competing explanations, evidence, experiments, and outcomes.
      </div>

      <div className="section">
        <h4>Register an unresolved audience need</h4>
        <div className="form">
          <input className="input" placeholder="Title (e.g. Beginner-friendly ZK education)" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea className="textarea" placeholder="Underlying need hypothesis (what the audience actually wants)" value={need} onChange={(e) => setNeed(e.target.value)} />
          <button className="btn primary" disabled={busy} onClick={create}>
            {busy ? 'registering…' : 'register remnant'}
          </button>
        </div>
      </div>

      <div className="section">
        <h4>Stored remnants ({remnants.length})</h4>
        {remnants.length === 0 ? (
          <div className="empty">No remnants yet. Register the first unresolved audience need.</div>
        ) : (
          <div className="grid">
            {remnants.map((r) => (
              <RemnantCard key={r.remnant_id} r={r} onClick={() => onOpen(r)} />
            ))}
          </div>
        )}
      </div>
    </>
  )
}

function DetailScreen({ remnant, onBack }: { remnant: Remnant; onBack: () => void }) {
  const [refreshed, setRefreshed] = useState<Remnant>(remnant)
  const [ingest, setIngest] = useState('')
  const [ingestYear, setIngestYear] = useState(new Date().getFullYear())
  const [busy, setBusy] = useState(false)
  const [experiment, setExperiment] = useState<Experiment | null>(
    remnant.experiments[remnant.experiments.length - 1] ?? null,
  )
  const [outcomeValue, setOutcomeValue] = useState('')
  const [belief, setBelief] = useState<string | null>(null)

  const refresh = () => api.remnant(remnant.remnant_id).then(setRefreshed)

  const askBelief = async () => {
    const b = await api.belief(remnant.remnant_id)
    setBelief(b.belief)
  }

  const addExpr = async () => {
    if (!ingest.trim()) return
    setBusy(true)
    try {
      await api.addExpression(remnant.remnant_id, ingest.trim(), 'youtube_comment', `c${Date.now()}`, `${ingestYear}-06-01T00:00:00Z`)
      setIngest('')
      await refresh()
    } finally {
      setBusy(false)
    }
  }

  const plan = async () => {
    setBusy(true)
    try {
      const e = await api.planExperiment(remnant.remnant_id)
      setExperiment(e)
      await refresh()
    } finally {
      setBusy(false)
    }
  }

  const record = async () => {
    const v = Number(outcomeValue)
    if (!experiment || Number.isNaN(v)) return
    setBusy(true)
    try {
      await api.recordOutcome(remnant.remnant_id, experiment.experiment_id, v)
      setOutcomeValue('')
      await refresh()
    } finally {
      setBusy(false)
    }
  }

  const adopt = async (decision: 'adopted' | 'rejected') => {
    setBusy(true)
    try {
      await api.addDecision(remnant.remnant_id, decision, 'creator confirmation')
      await refresh()
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <button className="btn" onClick={onBack} style={{ marginBottom: 16 }}>← back</button>
      <div className="detail-top">
        <div className="detail-title">REMNANT #{refreshed.remnant_id.slice(0, 6).toUpperCase()}</div>
        <span className="state" style={{ color: 'var(--warn)' }}>{stateLabel(refreshed.resolution_state)}</span>
      </div>
      <div className="detail-title" style={{ fontSize: 17, fontWeight: 600 }}>{refreshed.title}</div>
      <div className="page-desc" style={{ marginTop: 6 }}>
        {refreshed.underlying_need_hypothesis}
      </div>

      <div className="section">
        <h4>Temporal memory</h4>
        <Timeline remnant={refreshed} />
      </div>

      <div className="section">
        <h4>Historical expressions ({refreshed.expressions.length})</h4>
        {refreshed.expressions.length === 0 ? (
          <div className="empty">none yet</div>
        ) : (
          refreshed.expressions.map((e) => (
            <div className="expr" key={e.expression_id}>
              <div className="q">“{e.text}”</div>
              <div className="meta">
                {utcDate(e.occurred_at)} · {e.source.kind} · {e.source.source_id}
              </div>
            </div>
          ))
        )}
        <div className="form">
          <input className="input" placeholder='Expression text (e.g. "Can you make a beginner tutorial?")' value={ingest} onChange={(e) => setIngest(e.target.value)} />
          <input className="input" type="number" placeholder="year" value={ingestYear} onChange={(e) => setIngestYear(Number(e.target.value))} style={{ width: 140 }} />
          <button className="btn" disabled={busy} onClick={addExpr}>add expression</button>
        </div>
      </div>

      <div className="section">
        <h4>Competing explanations</h4>
        {refreshed.assessments.map((a) => (
          <div className="assess" key={a.hypothesis}>
            <div className="h">
              {a.hypothesis} — <span className={`pill ${a.evidence_strength}`}>{a.evidence_strength}</span>
            </div>
            <div className="sum">{a.summary}</div>
            {a.supporting_evidence.length > 0 && (
              <ul>
                {a.supporting_evidence.map((s, i) => (
                  <li key={`s${i}`}>support: {s}</li>
                ))}
                {a.contradicting_evidence.map((c, i) => (
                  <li key={`c${i}`}>conflict: {c}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      <div className="section">
        <h4>Provenance chain</h4>
        <Provenance remnant={refreshed} />
      </div>

      <div className="section">
        <h4>Experiment (pre-registered, then observed)</h4>
        {refreshed.experiments.length > 0 ? (
          <>
            {refreshed.experiments.map((e) => (
              <div className="assess" key={e.experiment_id}>
                <div className="h">EXPERIMENT #{e.experiment_id.slice(0, 6).toUpperCase()} · {e.status}</div>
                <div className="sum">{e.test}</div>
                <div className="sum">metric: {e.metric}</div>
                <div className="sum">
                  pre-registered threshold: {e.threshold_value} ({e.threshold_operator})
                </div>
                <div className="sum">prediction: {e.prediction}</div>
                <div className="sum">success: {e.success_threshold} · fail: {e.failure_condition}</div>
                {e.observed_value !== null && e.observed_value !== undefined && (
                  <div className="sum" style={{ color: e.crossed_threshold ? 'var(--good)' : 'var(--bad)' }}>
                    observed value: {e.observed_value.toFixed(3)} → {e.outcome}
                  </div>
                )}
              </div>
            ))}
            {refreshed.experiments.some((e) => e.status !== 'completed') && (
              <div className="form" style={{ maxWidth: 480 }}>
                <input
                  className="input"
                  type="number"
                  step="0.001"
                  placeholder="observed metric value (e.g. 0.067)"
                  value={outcomeValue}
                  onChange={(e) => setOutcomeValue(e.target.value)}
                />
                <button className="btn primary" disabled={busy} onClick={record}>
                  record observed number
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="form" style={{ maxWidth: 480 }}>
            <div className="empty">No experiment yet. Plan the smallest pre-registered probe.</div>
            <button className="btn primary" disabled={busy} onClick={plan}>plan smallest pre-registered experiment</button>
          </div>
        )}
      </div>

      <div className="section">
        <h4>Ask the Mind: what do you currently believe?</h4>
        <button className="btn" disabled={busy} onClick={askBelief}>ask</button>
        {belief && <pre className="mindlog" style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>{belief}</pre>}
      </div>

      <div className="section">
        <h4>Creator decision</h4>
        <div className="form" style={{ maxWidth: 480 }}>
          <button className="btn" disabled={busy} onClick={() => adopt('adopted')}>confirm adoption</button>
          <button className="btn" disabled={busy} onClick={() => adopt('rejected')}>reject</button>
        </div>
      </div>

      <div className="section">
        <h4>Mind history</h4>
        <div className="mindlog">
          {refreshed.history.map((h, i) => (
            <div key={i}>▸ {h}</div>
          ))}
        </div>
      </div>

      <div className="honest-note">
        Continuity is inferred, never asserted as fact. Two of the four competing
        explanations (H1 persistent need vs H2 new cohort) remain plausible until an
        experiment disambiguates them. Evidence strength is qualitative, not a calibrated
        probability.
      </div>
    </>
  )
}

// ---------- app --------------------------------------------------------------

type View = { name: 'remnants' } | { name: 'detail'; remnant: Remnant }

export default function App() {
  const [remnants, setRemnants] = useState<Remnant[]>([])
  const [view, setView] = useState<View>({ name: 'remnants' })
  const [mind, setMind] = useState<{ ok: boolean; name?: string; cognition_balance?: number; available: boolean } | null>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.remnants().then((rs) => {
      setRemnants(rs)
      setLoaded(true)
    })
    api.mind().then(setMind).catch(() => setMind({ ok: false, available: false }))
  }, [])

  const open = (r: Remnant) => setView({ name: 'detail', remnant: r })

  return (
    <div className="app">
      <div className="sidebar">
        <div className="brand">
          REMNANT
          <div className="sub">the mind that remembers what communities leave behind</div>
        </div>
        <div className={`nav-item ${view.name === 'remnants' ? 'active' : ''}`} onClick={() => setView({ name: 'remnants' })}>
          remnants <span className="count">{remnants.length}</span>
        </div>
        <div className="nav-item" onClick={() => window.location.reload()}>experiments</div>
        <div className="nav-item" onClick={() => window.location.reload()}>decisions</div>
        <div className="sidebar-foot">
          <span className={`mind-dot ${mind?.ok ? 'on' : 'off'}`} />
          persistent mind {mind?.name ? `· ${mind.name}` : ''}
          {mind?.cognition_balance !== undefined && <> · {mind.cognition_balance.toFixed(0)} cognition</>}
        </div>
      </div>
      <div className="main">
        {!loaded ? (
          <div className="empty">loading…</div>
        ) : view.name === 'remnants' ? (
          <RemnantsScreen remnants={remnants} onOpen={open} />
        ) : (
          <DetailScreen remnant={view.remnant} onBack={() => setView({ name: 'remnants' })} />
        )}
      </div>
    </div>
  )
}