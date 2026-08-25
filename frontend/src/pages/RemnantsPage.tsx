import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api, fmtDate, isRemnantList, firstDetected, lastDetected, currentRelevance,
  h1Strength, isSynthetic, RESOLUTION_COLORS, STATE_LABELS,
  type Remnant,
} from '../lib/api'

export function RemnantsPage() {
  const [remnants, setRemnants] = useState<Remnant[]>([])
  const [loaded, setLoaded] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    const grab = () => api.remnants().then((rs) => {
      if (!isRemnantList(rs)) throw new Error('invalid response shape')
      setRemnants(rs); setLoaded(true)
    }).catch(() => {
      // serverless cold-start: retry once before showing the error
      setTimeout(() => api.remnants().then((rs) => {
        if (!isRemnantList(rs)) throw new Error('invalid response shape')
        setRemnants(rs); setLoaded(true)
      }).catch((e2: Error) => { setErr(e2.message); setLoaded(true) }), 1200)
    })
    grab()
  }, [])

  const states = ['all', ...Array.from(new Set(remnants.map((r) => r.resolution_state)))]
  const shown = filter === 'all' ? remnants : remnants.filter((r) => r.resolution_state === filter)

  return (
    <div>
      <div className="page-title">Remnants</div>
      <p className="page-desc">
        Time-aware hypotheses about unresolved audience needs. A remnant is not a saved
        comment — it is a need with a history, evidence, and an experiment record.
      </p>

      <div className="btn-row" style={{ marginBottom: 20 }}>
        {states.map((s) => (
          <button key={s} className={s === filter ? 'btn' : 'btn btn-ghost'} style={{ padding: '7px 14px', fontSize: 12.5 }}
            onClick={() => setFilter(s)}>
            {s === 'all' ? `All (${remnants.length})` : `${STATE_LABELS[s] ?? s} (${remnants.filter((r) => r.resolution_state === s).length})`}
          </button>
        ))}
      </div>

      {err ? <div className="empty">Could not reach the backend: {err}</div>
        : !loaded ? <div className="empty">Loading…</div>
        : !shown.length ? <div className="empty">No remnants in this state.</div>
        : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Remnant ID</th>
                  <th>Underlying need</th>
                  <th>Status</th>
                  <th>First detected</th>
                  <th>Last detected</th>
                  <th>Current relevance</th>
                  <th>Evidence strength</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => {
                  const first = firstDetected(r)
                  const last = lastDetected(r)
                  const rel = currentRelevance(r)
                  const ev = h1Strength(r)
                  return (
                    <tr key={r.remnant_id}>
                      <td className="num">
                        <Link to={`/remnants/${r.remnant_id}`} style={{ color: 'var(--ink)' }}>{r.remnant_id.slice(0, 8)}</Link>
                      </td>
                      <td style={{ maxWidth: 320 }}>
                        {r.title}
                        {isSynthetic(r) && <span className="synth-tag" style={{ marginLeft: 8 }}>synthetic</span>}
                        <div className="small muted" style={{ marginTop: 2 }}>{r.underlying_need_hypothesis.slice(0, 90)}</div>
                      </td>
                      <td><span className={`badge ${RESOLUTION_COLORS[r.resolution_state] ?? 'badge-neutral'}`}>{STATE_LABELS[r.resolution_state] ?? r.resolution_state}</span></td>
                      <td className="num">{fmtDate(first)}</td>
                      <td className="num">{fmtDate(last)}</td>
                      <td><span className={`badge ${rel === 'high' ? 'badge-ok' : rel === 'medium' ? 'badge-warn' : 'badge-neutral'}`}>{rel}</span></td>
                      <td><span className={`badge ${ev === 'high' ? 'badge-ok' : ev === 'medium' ? 'badge-warn' : 'badge-neutral'}`}>{ev}</span></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
    </div>
  )
}