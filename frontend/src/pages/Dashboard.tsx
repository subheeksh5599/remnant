import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api, fmtDate, isRemnantList, currentRelevance, h1Strength, isSynthetic,
  type MindState, type Remnant, type ObservatoryAction,
} from '../lib/api'

function Badge({ kind, children }: { kind: string; children: React.ReactNode }) {
  return <span className={`badge ${kind}`}>{children}</span>
}

export function Dashboard() {
  const [remnants, setRemnants] = useState<Remnant[]>([])
  const [mind, setMind] = useState<MindState | null>(null)
  const [health, setHealth] = useState<{ ok: boolean; mind: boolean; remnants: number; env?: { mind_configured: boolean; storage_mode?: string } } | null>(null)
  const [actions, setActions] = useState<ObservatoryAction[]>([])
  const [surfacedCount, setSurfacedCount] = useState(0)
  const [err, setErr] = useState<string | null>(null)

  const load = () => {
    // observatory run is best-effort (503 when the loop isn't running) — never blank the dashboard
    const obs = api.observatoryRun().then((o) => o.surfaced.length).catch(() => 0)
    Promise.all([api.remnants(), api.mind(), api.health(), api.observatoryActions(), obs])
      .then(([rs, m, h, a, count]) => {
        if (!isRemnantList(rs)) throw new Error('invalid response shape')
        setRemnants(rs); setMind(m); setHealth(h); setActions(a.actions); setSurfacedCount(count)
      })
      .catch(() => {
        // serverless cold-start: retry once after a beat before showing an error
        setTimeout(() => {
          const obs2 = api.observatoryRun().then((o) => o.surfaced.length).catch(() => 0)
          Promise.all([api.remnants(), api.mind(), api.health(), api.observatoryActions(), obs2])
            .then(([rs, m, h, a, count]) => {
              if (!isRemnantList(rs)) throw new Error('invalid response shape')
              setRemnants(rs); setMind(m); setHealth(h); setActions(a.actions); setSurfacedCount(count)
            })
            .catch((e2: Error) => setErr(e2.message))
        }, 1200)
      })
  }
  useEffect(load, [])

  const lastAutonomous = actions.length ? actions[actions.length - 1] : null
  const persistOk = health?.ok ?? false
  const storageMode = health?.env?.storage_mode ?? null
  const mindLive = mind?.ok ?? false

  return (
    <div>
      <div className="page-title">Dashboard</div>
      <p className="page-desc">
        The persistent Minds agent and the community-memory archive, live.
      </p>

      {err && <div className="empty" style={{ marginBottom: 20 }}>Could not reach the backend: {err}</div>}

      {/* Mind Status */}
      <div className="card-title" style={{ marginTop: 12 }}>
        <h3>Mind status</h3>
        <Badge kind={mindLive ? 'badge-ok' : 'badge-err'}>{mindLive ? 'Online' : 'Offline'}</Badge>
      </div>
      <div className="grid-3" style={{ marginBottom: 8 }}>
        <div className="card">
          <div className="kv">
            <dt>Mind</dt><dd>{mind?.name ?? (mind?.available ? '—' : 'not configured')}</dd>
            <dt>Connection</dt><dd>{mindLive ? 'Connected' : 'Unavailable'}</dd>
            <dt>Persistence</dt><dd><span className={`badge ${storageMode === 'memory' ? 'badge-warn' : persistOk ? 'badge-ok' : 'badge-err'}`}>{storageMode === 'memory' ? 'memory (serverless)' : persistOk ? 'Store healthy' : 'Store error'}</span></dd>
          </div>
        </div>
        <div className="card">
          <div className="kv">
            <dt>Cognition balance</dt><dd className="num">{mind?.cognition_balance?.toFixed(1) ?? '—'}</dd>
            <dt>Mind enabled</dt><dd>{mind?.enabled ? 'Yes' : '—'}</dd>
            <dt>Error</dt><dd>{mind?.error ?? 'none'}</dd>
          </div>
        </div>
        <div className="card">
          <div className="kv">
            <dt>Last autonomous activity</dt>
            <dd>
              {lastAutonomous
                ? <span>{lastAutonomous.action} · {fmtDate(lastAutonomous.at)}</span>
                : 'none recorded yet'}
            </dd>
            <dt>Surfaced candidates</dt><dd className="num">{surfacedCount}</dd>
          </div>
        </div>
      </div>

      {/* Remnant summary */}
      <div className="card-title" style={{ marginTop: 24 }}>
        <h3>Remnants</h3>
        <Link to="/remnants" style={{ fontSize: 13, color: 'var(--muted)' }}>View all →</Link>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="tbl">
          <thead>
            <tr>
              <th>ID</th><th>Underlying need</th><th>Status</th><th>First</th><th>Last</th>
              <th>Relevance</th><th>H1 evidence</th>
            </tr>
          </thead>
          <tbody>
            {remnants.slice(0, 6).map((r) => (
              <tr key={r.remnant_id}>
                <td className="num"><Link to={`/remnants/${r.remnant_id}`} style={{ color: 'var(--ink)' }}>{r.remnant_id.slice(0, 8)}</Link></td>
                <td>
                  {r.title}
                  {isSynthetic(r) && <span className="synth-tag" style={{ marginLeft: 8 }}>synthetic</span>}
                </td>
                <td><Badge kind={stateBadge(r.resolution_state)}>{r.resolution_state.replace(/_/g, ' ')}</Badge></td>
                <td className="num">{fmtDate(firstDet(r))}</td>
                <td className="num">{fmtDate(lastDet(r))}</td>
                <td><Badge kind={relBadge(currentRelevance(r))}>{currentRelevance(r)}</Badge></td>
                <td><Badge kind={evBadge(h1Strength(r))}>{h1Strength(r)}</Badge></td>
              </tr>
            ))}
            {!remnants.length && !err && (
              <tr><td colSpan={7} className="muted" style={{ padding: 24, textAlign: 'center' }}>No remnants yet — load the demo corpus in the Safety lab.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Autonomous activity */}
      <div className="card-title" style={{ marginTop: 24 }}>
        <h3>Autonomous Mind activity</h3>
        <Link to="/mind" style={{ fontSize: 13, color: 'var(--muted)' }}>The Mind →</Link>
      </div>
      <div className="card">
        {actions.length ? (
          actions.slice(-6).reverse().map((a) => (
            <div className="feed-item" key={a.action_id}>
              <div className="feed-meta">
                {a.action}<br />{fmtDate(a.at)}
              </div>
              <div className="feed-act">
                <Link to={`/remnants/${a.remnant_id}`} style={{ color: 'var(--ink)' }}>{a.remnant_id.slice(0, 8)}</Link>
                <span className="muted"> — {a.reason.slice(0, 90)}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="empty">No autonomous actions yet. Run the observatory from The Mind page.</div>
        )}
      </div>
    </div>
  )
}

export function stateBadge(s: string): string {
  return { candidate: 'badge-info', insufficient_evidence: 'badge-neutral', unresolved: 'badge-warn', dormant: 'badge-neutral', fulfilled: 'badge-ok', rejected: 'badge-err',
    partially_fulfilled: 'badge-info', revisited: 'badge-info', under_experiment: 'badge-info',
    validated: 'badge-ok', disproven: 'badge-err', uncertain: 'badge-warn' }[s] ?? 'badge-neutral'
}
function relBadge(r: string): string { return r === 'high' ? 'badge-ok' : r === 'medium' ? 'badge-warn' : 'badge-neutral' }
function evBadge(e: string): string { return e === 'high' ? 'badge-ok' : e === 'medium' ? 'badge-warn' : 'badge-neutral' }
function firstDet(r: Remnant): string | null { return r.expressions.length ? r.expressions.reduce((a, b) => a.occurred_at < b.occurred_at ? a : b).occurred_at : null }
function lastDet(r: Remnant): string | null { return r.expressions.length ? r.expressions.reduce((a, b) => a.occurred_at > b.occurred_at ? a : b).occurred_at : null }