import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  api, fmtDate, isRemnant, firstDetected, lastDetected, currentRelevance, isSynthetic,
  HYPOTHESIS_LABELS, STATE_LABELS, RESOLUTION_COLORS, shortId,
  type Remnant, type Experiment, type ProvenancePayload,
} from '../lib/api'

export function RemnantDetail() {
  const { rid = '' } = useParams()
  const [r, setR] = useState<Remnant | null>(null)
  const [belief, setBelief] = useState<string>('')
  const [prov, setProv] = useState<ProvenancePayload | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [exprText, setExprText] = useState('')
  const [exprSrc, setExprSrc] = useState('youtube_comment')
  const [obsVal, setObsVal] = useState('')
  const [decision, setDecision] = useState('no_response')
  const [expThreshold, setExpThreshold] = useState('')
  const [expWindow, setExpWindow] = useState('')
  const [expPopulation, setExpPopulation] = useState('')
  const [expMetric, setExpMetric] = useState('')

  const load = (id: string) => {
    api.remnant(id).then((x) => {
      if (!isRemnant(x)) throw new Error('invalid response shape')
      setR(x)
      return api.belief(id)
    }).then((b) => setBelief(b.belief))
      .catch((e: Error) => setErr(e.message))
    api.provenance(id).then(setProv).catch(() => setProv(null))
  }
  useEffect(() => { load(rid) }, [rid])

  const full = r ?? null
  if (err && !full) return <div className="empty">Could not load remnant: {err}</div>
  if (!full) return <div className="empty">Loading…</div>

  const hist = full.expressions.filter((e) => new Date(e.occurred_at).getFullYear() <= 2023)
  const cur = full.expressions.filter((e) => new Date(e.occurred_at).getFullYear() >= 2024)
  const rel = currentRelevance(full)

  const addExpr = async () => {
    if (!exprText.trim()) return
    setBusy(true)
    try {
      await api.addExpression(full.remnant_id, exprText.trim(), exprSrc, `ui-${Date.now()}`)
      setExprText(''); await load(full.remnant_id)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }
  const planExp = async () => {
    setBusy(true)
    try {
      const overrides: Record<string, string | number> = {}
      if (expMetric.trim()) overrides.metric = expMetric.trim()
      if (expThreshold.trim() && !Number.isNaN(Number(expThreshold))) overrides.threshold = Number(expThreshold)
      if (expPopulation.trim()) overrides.target_population = expPopulation.trim()
      if (expWindow.trim()) overrides.measurement_window = expWindow.trim()
      await api.planExperiment(full.remnant_id, overrides)
      await load(full.remnant_id)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }
  const recordOut = async (e: Experiment) => {
    const v = Number(obsVal)
    if (!obsVal || Number.isNaN(v)) return
    setBusy(true)
    try { await api.recordOutcome(full.remnant_id, e.experiment_id, v); setObsVal(''); await load(full.remnant_id) }
    catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }
  const addDec = async () => {
    setBusy(true)
    try { await api.addDecision(full.remnant_id, decision, 'recorded from the UI'); await load(full.remnant_id) }
    catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  return (
    <div style={{ maxWidth: 1080 }}>
      <div className="page-title" style={{ fontSize: '1.3rem' }}>
        <Link to="/remnants" style={{ color: 'var(--muted)', fontSize: 13 }}>Remnants / </Link>
        {full.title}
      </div>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 24, flexWrap: 'wrap' }}>
        <span className={`badge ${RESOLUTION_COLORS[full.resolution_state] ?? 'badge-neutral'}`}>{STATE_LABELS[full.resolution_state] ?? full.resolution_state}</span>
        <span className={`badge ${rel === 'high' ? 'badge-ok' : rel === 'medium' ? 'badge-warn' : 'badge-neutral'}`}>relevance {rel}</span>
        <span className="badge badge-info">{full.remnant_id.slice(0, 10)}</span>
        {isSynthetic(full) && <span className="synth-tag">synthetic demonstration</span>}
      </div>

      {err && <div className="empty" style={{ marginBottom: 16, padding: 14 }}>{err}</div>}

      {/* Underlying need + resolution */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title"><h3>Underlying need</h3></div>
          <p style={{ fontSize: 14, color: 'var(--ink-2)' }}>{full.underlying_need_hypothesis}</p>
          <div className="kv" style={{ marginTop: 16 }}>
            <dt>First detected</dt><dd className="num">{fmtDate(firstDetected(full))}</dd>
            <dt>Last detected</dt><dd className="num">{fmtDate(lastDetected(full))}</dd>
            <dt>Expressions</dt><dd className="num">{full.expressions.length} total · {hist.length} historical · {cur.length} current</dd>
          </div>
        </div>
        <div className="card">
          <div className="card-title"><h3>Persistence state</h3></div>
          <div className="kv">
            <dt>Resolution state</dt><dd>{STATE_LABELS[full.resolution_state]}</dd>
            <dt>State transitions</dt><dd className="num">{full.state_transitions.length}</dd>
            <dt>Updated</dt><dd className="num">{fmtDate(full.updated_at)}</dd>
            <dt>History entries</dt><dd className="num">{full.history.length}</dd>
          </div>
        </div>
      </div>

      {/* Timeline + evidence */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Timeline</h3></div>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="timeline">
          {[...full.expressions].sort((a, b) => a.occurred_at.localeCompare(b.occurred_at)).map((e) => (
            <div className="tl-row" key={e.expression_id}>
              <div className="tl-date">{fmtDate(e.occurred_at)}</div>
              <div className="tl-body">
                <span className="small muted mono">{e.source.kind}</span><br />
                {e.text}
              </div>
            </div>
          ))}
          {!full.expressions.length && <div className="empty">No expressions recorded yet.</div>}
        </div>
      </div>

      {/* Historical + current expressions */}
      <div className="grid-2" style={{ marginBottom: 8 }}>
        <div className="card">
          <div className="card-title"><h3>Historical expressions</h3><span className="meta">{hist.length}</span></div>
          {hist.length ? hist.map((e) => (
            <div className="ev ev-neutral" key={e.expression_id} style={{ marginBottom: 6 }}>
              <span className="mono small muted">{fmtDate(e.occurred_at)} [{e.source.kind}]</span><br />{e.text}
            </div>
          )) : <div className="empty" style={{ padding: 16 }}>None on record.</div>}
        </div>
        <div className="card">
          <div className="card-title"><h3>Current expressions</h3><span className="meta">{cur.length}</span></div>
          {cur.length ? cur.map((e) => (
            <div className="ev ev-neutral" key={e.expression_id} style={{ marginBottom: 6 }}>
              <span className="mono small muted">{fmtDate(e.occurred_at)} [{e.source.kind}]</span><br />{e.text}
            </div>
          )) : <div className="empty" style={{ padding: 16 }}>None on record.</div>}
        </div>
      </div>

      {/* Competing hypotheses H1-H4 */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Competing hypotheses</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        {full.assessments.map((a) => {
          const lbl = HYPOTHESIS_LABELS[a.hypothesis] ?? { label: a.hypothesis, short: a.hypothesis }
          const pct = a.evidence_strength === 'high' ? 75 : a.evidence_strength === 'medium' ? 45 : 12
          return (
            <div className="hypo" key={a.hypothesis}>
              <div>
                <div className="hypo-label">{a.hypothesis} · {lbl.short}</div>
                <div className="hypo-strength"><span className={`badge ${a.evidence_strength === 'high' ? 'badge-ok' : a.evidence_strength === 'medium' ? 'badge-warn' : 'badge-neutral'}`}>{a.evidence_strength} evidence</span></div>
              </div>
              <div>
                <div className="bar"><div className="bar-fill" style={{ width: `${pct}%` }} /></div>
                <div className="grid-2" style={{ marginTop: 10, gap: 10 }}>
                  <div>
                    <div className="meta" style={{ marginBottom: 4 }}>Supporting</div>
                    {a.supporting_evidence.length ? a.supporting_evidence.map((s, i) => <div className="ev ev-support" key={i} style={{ marginBottom: 4 }}>{s}</div>) : <div className="ev ev-missing">none</div>}
                  </div>
                  <div>
                    <div className="meta" style={{ marginBottom: 4 }}>Conflicting</div>
                    {a.contradicting_evidence.length ? a.contradicting_evidence.map((s, i) => <div className="ev ev-conflict" key={i} style={{ marginBottom: 4 }}>{s}</div>) : <div className="ev ev-missing">none on record</div>}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Discovery evidence (P0.2: how this remnant was discovered, not encoded) */}
      {full.discovered_links && full.discovered_links.length > 0 && (
        <>
          <div className="card-title" style={{ marginTop: 24 }}><h3>Discovery evidence</h3></div>
          <div className="card" style={{ marginBottom: 8 }}>
            <p className="small muted" style={{ marginBottom: 12 }}>
              How REMNANT itself linked each expression into this remnant — the transparent matcher
              evidence (concept glossary + token overlap), with its limits. Nothing here is pre-encoded
              by the corpus.
            </p>
            {full.discovered_links.map((l, i) => (
              <div className="ev ev-neutral" key={i} style={{ marginBottom: 8 }}>
                <div style={{ marginBottom: 4 }}>
                  <span className={`badge ${l.relationship === 'same_need' ? 'badge-ok' : l.relationship === 'candidate' ? 'badge-info' : 'badge-warn'}`}>{l.relationship.replace(/_/g, ' ')}</span>
                  <span className="muted small" style={{ marginLeft: 8 }}>confidence {l.confidence}</span>
                  {l.shared_concepts?.length > 0 && <span className="muted small" style={{ marginLeft: 8 }}>concepts: {l.shared_concepts.join(', ')}</span>}
                </div>
                <div className="small muted" style={{ marginBottom: 4 }}>vs "{l.against_text}"</div>
                {l.supporting?.map((s, j) => <div className="ev ev-support" key={j} style={{ marginBottom: 2, fontSize: 12 }}>{s}</div>)}
                {l.conflicting?.map((c, j) => <div className="ev ev-conflict" key={j} style={{ marginBottom: 2, fontSize: 12 }}>{c}</div>)}
                {l.uncertainty?.map((u, j) => <div className="ev ev-missing" key={j} style={{ marginBottom: 2, fontSize: 12 }}>{u}</div>)}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Experiments */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Experiments</h3></div>
      {full.experiments.map((e) => (
        <div className="card" key={e.experiment_id} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
            <span className="mono small muted">Experiment {shortId(e.experiment_id)}</span>
            <span className={`badge ${e.status === 'completed' ? 'badge-ok' : 'badge-warn'}`}>{e.status}{e.status === 'completed' ? ' · immutable' : ''}</span>
          </div>
          <div className="kv" style={{ marginBottom: 10 }}>
            <dt>Question</dt><dd>{e.test.slice(0, 160)}</dd>
            <dt>Hypothesis tested</dt><dd>{e.hypothesis}</dd>
            <dt>Metric</dt><dd>{e.metric}</dd>
            <dt>Pre-registered threshold</dt><dd className="num">{e.threshold_value} ({e.threshold_operator}) — locked before observation</dd>
            <dt>Prediction</dt><dd>{e.prediction}</dd>
            <dt>Success condition</dt><dd>{e.success_threshold}</dd>
            <dt>Failure condition</dt><dd>{e.failure_condition}</dd>
          </div>
          {e.status === 'completed' ? (
            <div className="evidence">
              <div className="ev ev-support">Observed value: <b className="num">{e.observed_value}</b> · Verdict: {e.outcome}</div>
              <div className="ev ev-neutral">Outcome recorded once — duplicates rejected with 409. Immutable after recording.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div>
                <label className="label">Observed value (ratio 0-1)</label>
                <input className="input" style={{ width: 140 }} placeholder="e.g. 0.067"
                  value={obsVal} onChange={(ev) => setObsVal(ev.target.value)} />
              </div>
              <button className="btn" disabled={busy} onClick={() => recordOut(e)}>Record observation</button>
            </div>
          )}
        </div>
      ))}
      {!full.experiments.length && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title"><h3>Plan an experiment</h3><span className="meta">defaults are autonomous; overrides are yours</span></div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label className="label">Metric (optional)</label>
              <input className="input" placeholder="e.g. comment-to-view ratio at 72h"
                value={expMetric} onChange={(ev) => setExpMetric(ev.target.value)} />
            </div>
            <div style={{ width: 110 }}>
              <label className="label">Threshold (0-1)</label>
              <input className="input" placeholder="0.04" value={expThreshold}
                onChange={(ev) => setExpThreshold(ev.target.value)} />
            </div>
            <div style={{ width: 150 }}>
              <label className="label">Window</label>
              <input className="input" placeholder="48h" value={expWindow}
                onChange={(ev) => setExpWindow(ev.target.value)} />
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label className="label">Target population</label>
              <input className="input" placeholder="beginner segment"
                value={expPopulation} onChange={(ev) => setExpPopulation(ev.target.value)} />
            </div>
            <div style={{ alignSelf: 'flex-end' }}>
              <button className="btn" disabled={busy} onClick={planExp}>Plan experiment</button>
            </div>
          </div>
          <p className="small muted" style={{ marginTop: 10 }}>
            Leave all fields empty for the autonomous default (90s explainer, comment-to-view ratio,
            threshold 0.04, 48h). Any field you fill is recorded as creator-defined on the experiment.
          </p>
        </div>
      )}

      {/* Belief reconstruction */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Belief reconstruction</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <p className="mono small" style={{ whiteSpace: 'pre-line', color: 'var(--ink-2)', fontSize: 12.5 }}>{belief}</p>
      </div>

      {/* Provenance */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Provenance</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <p className="small muted" style={{ marginBottom: 12 }}>
          Every expression carries source, timestamp, and original text. Interpretation and
          derived conclusions are recorded, never retrofitted.
        </p>
        {prov ? (
          <table className="tbl">
            <thead>
              <tr>
                <th>Source</th><th>Timestamp</th><th>Original expression</th><th>Interpretation</th><th>Derived conclusion</th>
              </tr>
            </thead>
            <tbody>
              {prov.expressions.map((e) => (
                <tr key={e.expression_id}>
                  <td className="num">{e.source.kind} {e.source.source_id ? `· ${e.source.source_id.slice(0, 10)}` : ''}</td>
                  <td className="num">{fmtDate(e.occurred_at)}</td>
                  <td className="small">{e.text.slice(0, 80)}</td>
                  <td className="small muted">recorded as evidence toward the underlying need</td>
                  <td className="small muted">contributes to H1–H4 evidence accounting</td>
                </tr>
              ))}
              {!prov.expressions.length && (
                <tr><td colSpan={5} className="muted" style={{ padding: 16, textAlign: 'center' }}>No expressions recorded.</td></tr>
              )}
            </tbody>
          </table>
        ) : (
          <div className="empty" style={{ padding: 16 }}>Provenance unavailable.</div>
        )}
        {prov && prov.state_transitions.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div className="meta" style={{ marginBottom: 6 }}>State-transition history (evidence chain)</div>
            <div className="timeline">
              {prov.state_transitions.map((t, i) => (
                <div className="tl-row" key={i}>
                  <div className="tl-date">{fmtDate(t.at)}</div>
                  <div className="tl-body"><span className="num">{t.from}</span> → <b>{t.to}</b> <span className="muted">— {t.reason}</span></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Creator decisions */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Creator decisions</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        {full.creator_decisions.length ? (
          <table className="tbl">
            <thead><tr><th>Decision</th><th>Date</th><th>Reason</th></tr></thead>
            <tbody>
              {full.creator_decisions.map((d, i) => (
                <tr key={i}><td><span className="badge badge-info">{d.decision.replace(/_/g, ' ')}</span></td><td className="num">{fmtDate(d.decided_at)}</td><td>{d.reason ?? '—'}</td></tr>
              ))}
            </tbody>
          </table>
        ) : <div className="empty" style={{ padding: 14 }}>No creator decision recorded.</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          {['adopted', 'rejected', 'deferred', 'no_response'].map((d) => (
            <button key={d} className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }}
              onClick={() => { setDecision(d); addDec() }} disabled={busy}>
              {d.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Ingest */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Ingest an expression</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input className="input" style={{ flex: 2, minWidth: 240 }} placeholder="e.g. I don't know where to begin with ZK"
            value={exprText} onChange={(ev) => setExprText(ev.target.value)} />
          <select className="input" style={{ width: 160 }} value={exprSrc} onChange={(ev) => setExprSrc(ev.target.value)}>
            {['youtube_comment', 'discord', 'twitter', 'github_discussion'].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button className="btn" disabled={busy || !exprText.trim()} onClick={addExpr}>Ingest</button>
        </div>
      </div>
    </div>
  )
}