import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AdversarialResult } from '../lib/api'

export function LabPage() {
  const [a, setA] = useState('How do I learn ZK?')
  const [b, setB] = useState('ZK badge for my profile looks broken')
  const [result, setResult] = useState<AdversarialResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [demo, setDemo] = useState<{
    loaded?: number
    synthetic?: boolean
    label?: string
    reconnected?: boolean
    remnants_survived?: number
    note?: string
    discovery?: { action: string; remnant: string; expression: string; verdict: string; evidence: string }[]
  } | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const analyze = async () => {
    setBusy(true)
    try { setResult(await api.adversarial(a.trim(), b.trim())) }
    catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const loadCorpus = async () => {
    setBusy(true)
    try {
      const r = await api.demoLoad()
      setDemo(r)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const reconnect = async () => {
    setBusy(true)
    try {
      const r = await api.demoReconnect()
      setDemo(r)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const PRESETS: { a: string; b: string; note: string }[] = [
    { a: 'Can you make a beginner ZK tutorial?', b: 'How do I start building with zero knowledge?', note: 'cross-language — same need, zero shared words (discovery)' },
    { a: 'How do I learn ZK?', b: 'ZK badge for my profile looks broken', note: 'adversarial collision — shared token but a fault report' },
    { a: 'Beginner ZK tutorial please', b: 'Please make ZK tutorials for beginners', note: 'true continuity — same need, similar phrasing' },
    { a: 'I want to learn zero knowledge proofs', b: 'Can we get merch pls', note: 'same subject concept, different NEEDS (global discovery guard)' },
    { a: 'Merch restock when?', b: 'Add dark mode to the dashboard?', note: 'unrelated needs' },
  ]

  return (
    <div>
      <div className="page-title">Safety lab</div>
      <p className="page-desc">
        Two controls judges will pull: the adversarial semantic guard, and the demo corpus
        (clearly labeled synthetic). Nothing here fakes evidence.
      </p>

      {err && <div className="empty" style={{ marginBottom: 16, padding: 14 }}>{err}</div>}

      {/* Semantic safety */}
      <div className="card-title"><h3>Semantic safety — adversarial analysis</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="label">Expression A</label>
            <textarea className="input" value={a} onChange={(ev) => setA(ev.target.value)} />
          </div>
          <div>
            <label className="label">Expression B</label>
            <textarea className="input" value={b} onChange={(ev) => setB(ev.target.value)} />
          </div>
        </div>
        <div className="btn-row" style={{ marginBottom: 16 }}>
          <button className="btn" disabled={busy || !a.trim() || !b.trim()} onClick={analyze}>Analyze relationship</button>
          {PRESETS.map((p, i) => (
            <button key={i} className="btn btn-ghost" style={{ padding: '7px 12px', fontSize: 12 }}
              title={p.note} onClick={() => { setA(p.a); setB(p.b) }}>
              {p.note.split('—')[0].trim()}
            </button>
          ))}
        </div>
        {result && (
          <div className="evidence">
            <div className="ev ev-neutral">
              Relationship: <b>{result.relationship.replace(/_/g, ' ')}</b>
              <span className="muted"> · confidence {result.confidence}</span>
              <span className={`badge ${result.relationship === 'same_need' ? 'badge-ok' : result.relationship === 'candidate' ? 'badge-info' : result.relationship === 'different_need' ? 'badge-err' : 'badge-warn'}`}
                style={{ marginLeft: 8 }}>{result.relationship.replace(/_/g, ' ')}</span>
              {result.shared_concepts?.length > 0 && (
                <span className="muted small" style={{ marginLeft: 8 }}>concepts: {result.shared_concepts.join(', ')}</span>
              )}
            </div>
            <div className="meta" style={{ marginTop: 4 }}>Supporting evidence</div>
            {result.supporting?.map((line, i) => <div className="ev ev-support" key={`s${i}`} style={{ fontSize: 12.5 }}>{line}</div>)}
            {result.conflicting?.length > 0 && (
              <>
                <div className="meta" style={{ marginTop: 8 }}>Conflicting evidence</div>
                {result.conflicting.map((line, i) => <div className="ev ev-conflict" key={`c${i}`} style={{ fontSize: 12.5 }}>{line}</div>)}
              </>
            )}
            {result.uncertainty?.length > 0 && (
              <>
                <div className="meta" style={{ marginTop: 8 }}>Uncertainty</div>
                {result.uncertainty.map((line, i) => <div className="ev ev-missing" key={`u${i}`} style={{ fontSize: 12.5 }}>{line}</div>)}
              </>
            )}
          </div>
        )}
        <p className="small muted" style={{ marginTop: 12 }}>
          The guard is deliberately conservative: shared tokens are never treated as continuity on
          their own. "ZK badge is broken" vs "how do I learn ZK" must come back different needs.
        </p>
      </div>

      {/* Demo controls */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Demo controls</h3></div>
      <div className="card">
        <div className="btn-row" style={{ marginBottom: 16 }}>
          <button className="btn" disabled={busy} onClick={loadCorpus}>Load demonstration corpus</button>
          <button className="btn btn-ghost" disabled={busy} onClick={reconnect}>Reconnect / restart persistence</button>
          <Link to="/remnants" className="btn btn-ghost">Trigger new evidence (Remnants)</Link>
          <Link to="/mind" className="btn btn-ghost">Replay belief chain (The Mind)</Link>
        </div>
        {demo && (
          <div className="evidence">
            {demo.loaded !== undefined && (
              <div className="ev ev-neutral">
                Loaded <b className="num">{demo.loaded}</b> remnants — <span className="synth-tag">{demo.label ?? 'synthetic'}</span>
                {demo.note && <span className="muted"> ({demo.note})</span>}
              </div>
            )}
            {demo.discovery && demo.discovery.length > 0 && (
              <>
                <div className="meta" style={{ marginTop: 4 }}>Discovery log — what REMNANT decided, not the corpus</div>
                {demo.discovery.slice(0, 8).map((d, i) => (
                  <div className="ev ev-neutral" key={i} style={{ fontSize: 12.5 }}>
                    <b className="mono">{d.action}</b> "{d.expression}" → <b>{d.remnant}</b> {d.verdict !== 'new_candidate' ? `(${d.verdict})` : '(new candidate)'}
                  </div>
                ))}
              </>
            )}
            {demo.remnants_survived !== undefined && (
              <div className="ev ev-support">
                Restart simulated — <b className="num">{demo.remnants_survived}</b> remnants survived. {demo.note}
              </div>
            )}
            <div className="ev ev-missing">
              Demo corpus is synthetic and labeled. Real audience data is ingested the same way,
              through the Remnants page, and is never relabeled.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}