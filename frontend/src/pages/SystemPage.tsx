import { useEffect, useState } from 'react'
import { api, type AuditEvent } from '../lib/api'

export function SystemPage() {
  const [health, setHealth] = useState<{ ok: boolean; mind: boolean; remnants: number; env: { mind_configured: boolean; storage_mode?: string } } | null>(null)
  const [ready, setReady] = useState<{ ok: boolean; remnants: number } | null>(null)
  const [live, setLive] = useState<{ ok: boolean } | null>(null)
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.health(), api.readyz(), api.livez(), api.audit(150)])
      .then(([h, r, l, a]) => { setHealth(h); setReady(r); setLive(l); setAudit(a.events) })
      .catch((e: Error) => setErr(e.message))
  }, [])

  return (
    <div>
      <div className="page-title">System</div>
      <p className="page-desc">
        Health, audit trail, and the honest states the product can be in. Every mutation is
        logged with a request id; every failure is explicit, never silent.
      </p>

      {err && <div className="empty" style={{ marginBottom: 16 }}>{err}</div>}

      {/* System health */}
      <div className="card-title"><h3>System health</h3></div>
      <div className="grid-4" style={{ marginBottom: 8 }}>
        <div className="card">
          <div className="kv">
            <dt>Mind connection</dt><dd><span className={`badge ${health?.mind ? 'badge-ok' : 'badge-err'}`}>{health?.mind ? 'connected' : 'offline'}</span></dd>
            <dt>Backend readiness</dt><dd><span className={`badge ${ready?.ok ? 'badge-ok' : 'badge-err'}`}>{ready?.ok ? 'ready' : 'not ready'}</span></dd>
          </div>
        </div>
        <div className="card">
          <div className="kv">
            <dt>Liveness</dt><dd><span className={`badge ${live?.ok ? 'badge-ok' : 'badge-err'}`}>{live?.ok ? 'alive' : 'down'}</span></dd>
            <dt>Persistence</dt><dd><span className={`badge ${health?.env?.storage_mode === 'memory' ? 'badge-warn' : 'badge-ok'}`}>{health?.env?.storage_mode === 'memory' ? 'memory (serverless)' : 'store healthy'}</span></dd>
          </div>
        </div>
        <div className="card">
          <div className="kv">
            <dt>Observatory</dt><dd><span className="badge badge-info">background loop</span></dd>
            <dt>Minds env</dt><dd><span className={`badge ${health?.env?.mind_configured ? 'badge-ok' : 'badge-neutral'}`}>{health?.env?.mind_configured ? 'configured' : 'not configured'}</span></dd>
          </div>
        </div>
        <div className="card">
          <div className="kv">
            <dt>Last operation</dt><dd className="num">{audit.length ? audit[audit.length - 1].event : '—'}</dd>
            <dt>Error state</dt><dd>{err ? <span className="badge badge-err">error</span> : <span className="badge badge-ok">none</span>}</dd>
          </div>
        </div>
      </div>

      {/* Error / uncertainty states */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Error &amp; uncertainty states</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {[
            ['Insufficient evidence', 'badge-warn'],
            ['No reliable match', 'badge-warn'],
            ['Conflicting evidence', 'badge-info'],
            ['Mind unavailable', 'badge-err'],
            ['Experiment inconclusive', 'badge-warn'],
            ['Unauthorized action', 'badge-err'],
            ['Persistence failure', 'badge-err'],
          ].map(([l, b]) => <span key={l} className={`badge ${b}`}>{l}</span>)}
        </div>
        <p className="small muted" style={{ marginTop: 12 }}>
          These are first-class states, not bugs. The Mind reports "I don't know" and picks a probe;
          auth failures return 401 with a request id; Mind failures report unavailable instead of
          fabricating behavior.
        </p>
      </div>

      {/* Evidence states */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Evidence states</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <span className="badge badge-ok">real</span>
          <span className="badge badge-warn">synthetic demonstration</span>
          <span className="badge badge-info">inferred</span>
          <span className="badge badge-ok">confirmed</span>
          <span className="badge badge-neutral">uncertain</span>
        </div>
        <p className="small muted" style={{ marginTop: 12 }}>
          Synthetic data is labeled everywhere it appears and never mixed with real data without
          the label. Evidence strength is qualitative (low/medium/high), never a fake percentage.
        </p>
      </div>

      {/* Audit trail */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Audit trail</h3></div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="tbl">
          <thead>
            <tr><th>Event</th><th>Request id</th><th>Details</th></tr>
          </thead>
          <tbody>
            {[...audit].reverse().slice(0, 40).map((e, i) => (
              <tr key={i}>
                <td className="num" style={{ whiteSpace: 'nowrap' }}>{e.event}</td>
                <td className="num muted">{typeof e.request_id === 'string' ? e.request_id.slice(0, 12) : '—'}</td>
                <td className="small muted" style={{ maxWidth: 420 }}>
                  {Object.entries(e).filter(([k]) => !['event', 'request_id'].includes(k)).map(([k, v]) => `${k}=${typeof v === 'string' ? v.slice(0, 60) : String(v).slice(0, 40)}`).join(' · ')}
                </td>
              </tr>
            ))}
            {!audit.length && <tr><td colSpan={3} className="muted" style={{ padding: 20, textAlign: 'center' }}>No audit events yet.</td></tr>}
          </tbody>
        </table>
      </div>

      <p className="small muted" style={{ marginTop: 12 }}>
        Full JSON logs, health/readyz/livez endpoints, and the OpenAPI schema at /api/v1/docs.
      </p>
    </div>
  )
}