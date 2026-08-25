import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api, fmtDate, shortId,
  type MindState, type MindsStatus, type ObservatoryAction, type ObservationCandidate, type AskAnswers,
} from '../lib/api'

export function MindPage() {
  const [mind, setMind] = useState<MindState | null>(null)
  const [status, setStatus] = useState<MindsStatus | null>(null)
  const [actions, setActions] = useState<ObservatoryAction[]>([])
  const [surfaced, setSurfaced] = useState<ObservationCandidate[]>([])
  const [answers, setAnswers] = useState<AskAnswers | null>(null)
  const [askRid, setAskRid] = useState('')
  const [persist, setPersist] = useState<{ remnants_survived: number; reconnected: boolean } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [remnants, setRemnants] = useState<{ remnant_id: string; title: string }[]>([])
  const [keyField, setKeyField] = useState('')
  const [connectMsg, setConnectMsg] = useState<string | null>(null)

  const refresh = () => {
    Promise.all([api.mind(), api.observatoryActions(), api.remnants(), api.mindsStatus()])
      .then(([m, a, rs, st]) => {
        setMind(m); setActions(a.actions)
        setRemnants(rs.map((r) => ({ remnant_id: r.remnant_id, title: r.title })))
        setStatus(st)
      })
      .catch((e: Error) => setErr(e.message))
  }
  useEffect(refresh, [])

  const resolveRid = (input: string): string => {
    const t = input.trim()
    const exact = remnants.find((r) => r.remnant_id === t)
    if (exact) return exact.remnant_id
    const byPrefix = remnants.find((r) => r.remnant_id.startsWith(t))
    return byPrefix ? byPrefix.remnant_id : t
  }

  const runObs = async () => {
    setBusy(true)
    try {
      const o = await api.observatoryRun()
      setSurfaced(o.surfaced); setActions(o.action_log)
      if (o.surfaced.length && !askRid) setAskRid(o.surfaced[0].remnant_id)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const connect = async () => {
    if (!keyField.trim()) return
    setBusy(true); setConnectMsg(null)
    try {
      const r = await api.mindsConnect(keyField.trim())
      setConnectMsg(`Connected to ${r.mind_name}. ${r.note}`)
      setKeyField('')
      refresh()
    } catch (e) { setConnectMsg((e as Error).message) } finally { setBusy(false) }
  }

  const disconnect = async () => {
    setBusy(true); setConnectMsg(null)
    try { await api.mindsDisconnect(); setConnectMsg('Disconnected. The env-configured Mind (if any) is used again.'); refresh() }
    catch (e) { setConnectMsg((e as Error).message) } finally { setBusy(false) }
  }

  const reconnect = async () => {
    setBusy(true)
    try { setPersist(await api.demoReconnect()) } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const ask = async (input: string) => {
    const id = resolveRid(input)
    setBusy(true)
    try { setAnswers((await api.ask(id)).answers) } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  const QUESTIONS: { key: keyof AskAnswers; label: string }[] = [
    { key: 'what_do_you_currently_believe', label: 'What do you currently believe?' },
    { key: 'why', label: 'Why?' },
    { key: 'what_evidence_supports_this', label: 'What evidence supports this?' },
    { key: 'what_contradicts_it', label: 'What contradicts it?' },
    { key: 'what_should_we_test_next', label: 'What should we test next?' },
    { key: 'what_changed_since_the_last_experiment', label: 'What changed since the last experiment?' },
  ]

  return (
    <div>
      <div className="page-title">The Mind</div>
      <p className="page-desc">
        The persistent agent that holds the community-memory narrative. Memory mirroring is
        live-gated: with the Minds env configured, every belief-critical change is written to
        the Mind's conversation; without it, this page reports why not.
      </p>

      {/* Connect your own Mind */}
      <div className="card-title"><h3>Connect your Mind</h3></div>
      <div className="card" style={{ marginBottom: 20 }}>
        <p className="small muted" style={{ marginBottom: 12 }}>
          Any creator can use this instance with <b>their own Minds agent</b>: paste a Minds Builder
          API key, and your Mind becomes the memory steward — every expression, experiment, and belief
          update is mirrored into <b>your</b> Mind's conversation. Validated against the real Builder
          API; the key is never stored or echoed back.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input className="input" style={{ flex: 1, minWidth: 260 }} type="password"
            placeholder="Minds Builder API key (eyJ…) / MIND_ID optional"
            value={keyField} onChange={(ev) => setKeyField(ev.target.value)} />
          <button className="btn" disabled={busy || !keyField.trim()} onClick={connect}>Connect</button>
          {status?.connected && (
            <button className="btn btn-ghost" disabled={busy} onClick={disconnect}>Disconnect</button>
          )}
        </div>
        {connectMsg && <div className="ev ev-neutral" style={{ marginTop: 12 }}>{connectMsg}</div>}
        {status && (
          <div className="kv" style={{ marginTop: 12 }}>
            <dt>Memory steward</dt>
            <dd>
              {status.connected
                ? <span><span className={`badge ${status.kind === 'user' ? 'badge-info' : 'badge-ok'}`}>{status.kind === 'user' ? 'your Mind' : 'env-configured'}</span> {status.mind_name ?? ''}</span>
                : <span className="badge badge-neutral">none connected</span>}
            </dd>
            <dt>Status detail</dt><dd className="small muted">{status.error ?? 'ok'}</dd>
          </div>
        )}
      </div>

      {err && <div className="empty" style={{ marginBottom: 16, padding: 14 }}>{err}</div>}

      {/* Mind status */}
      <div className="grid-3" style={{ marginBottom: 8 }}>
        <div className="card">
          <div className="card-title"><h3>Mind</h3><span className={`badge ${mind?.ok ? 'badge-ok' : 'badge-err'}`}>{mind?.ok ? 'online' : 'offline'}</span></div>
          <div className="kv">
            <dt>Name</dt><dd>{mind?.name ?? '—'}</dd>
            <dt>Mind ID</dt><dd className="num">{mind?.mind_id ? shortId(mind.mind_id) : '—'}</dd>
            <dt>Cognition</dt><dd className="num">{mind?.cognition_balance?.toFixed(1) ?? '—'}</dd>
          </div>
          {!mind?.ok && mind?.error && <div className="ev ev-conflict" style={{ marginTop: 10 }}>{mind.error}</div>}
        </div>
        <div className="card">
          <div className="card-title"><h3>Persistence status</h3></div>
          <div className="kv">
            <dt>Store</dt><dd>durable JSON backing</dd>
            <dt>Memory mirroring</dt><dd>{status?.connected ? `on → ${status.mind_name ?? mind?.name ?? 'connected Mind'}` : mind?.available ? 'on (env configured)' : 'off — connect your Mind above'}</dd>
            <dt>Last autonomous</dt><dd>{actions.length ? `${actions[actions.length - 1].action} · ${fmtDate(actions[actions.length - 1].at)}` : 'none'}</dd>
          </div>
        </div>
        <div className="card">
          <div className="card-title"><h3>Persistence proof</h3></div>
          <p className="small muted" style={{ marginBottom: 12 }}>
            Simulate an application restart: the store reloads from disk and the belief chain
            must survive.
          </p>
          <button className="btn" disabled={busy} onClick={reconnect}>Reconnect / restart</button>
          {persist && (
            <div className="evidence" style={{ marginTop: 12 }}>
              <div className="ev ev-support">Restart simulated. <b className="num">{persist.remnants_survived}</b> remnants survived; belief chains reconstructed.</div>
            </div>
          )}
        </div>
      </div>

      {/* Autonomous activity */}
      <div className="card-title" style={{ marginTop: 24 }}>
        <h3>Autonomous Mind activity</h3>
        <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }} disabled={busy} onClick={runObs}>Run observatory</button>
      </div>
      <div className="card" style={{ marginBottom: 8 }}>
        {surfaced.length > 0 && (
          <div className="evidence" style={{ marginBottom: 14 }}>
            <div className="meta">Surfaced candidates (approval required — never auto-executed)</div>
            {surfaced.map((s) => (
              <div className="ev ev-neutral" key={s.remnant_id}>
                <Link to={`/remnants/${s.remnant_id}`} style={{ color: 'var(--ink)', textDecoration: 'underline' }}>{s.title}</Link>
                <span className="muted"> — {s.recommended_action}</span>
              </div>
            ))}
          </div>
        )}
        {actions.length ? (
          [...actions].reverse().slice(0, 20).map((a) => (
            <div className="feed-item" key={a.action_id}>
              <div className="feed-meta">
                {a.action}<br />{fmtDate(a.at)}<br /><span className="mono">{shortId(a.action_id)}</span>
              </div>
              <div className="feed-act">
                <Link to={`/remnants/${a.remnant_id}`} style={{ color: 'var(--ink)' }}>{shortId(a.remnant_id)}</Link>
                <span className="muted"> — {a.reason}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="empty">No autonomous actions yet — run the observatory.</div>
        )}
      </div>

      {/* Ask the mind */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Ask the Mind</h3></div>
      <div className="card">
        <p className="small muted" style={{ marginBottom: 12 }}>
          Answers are reconstructed from the persisted evidence chain — never invented. Enter a
          remnant id or pick one from the surfaced candidates.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          <input className="input" style={{ flex: 1, minWidth: 220 }} placeholder="remnant id (first 8 chars)"
            value={askRid} onChange={(ev) => setAskRid(ev.target.value)} />
          <button className="btn" disabled={busy || !askRid.trim()} onClick={() => ask(askRid)}>Ask</button>
          {surfaced.map((s) => (
            <button key={s.remnant_id} className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => { setAskRid(s.remnant_id); ask(s.remnant_id) }}>
              {shortId(s.remnant_id)}
            </button>
          ))}
        </div>
        {answers ? (
          <div>
            {QUESTIONS.map((q) => (
              <div className="ask" key={q.key}>
                <div className="ask-q">{q.label}</div>
                <div className="ask-a">{answers[q.key]}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty" style={{ padding: 24 }}>Ask a question to reconstruct the full belief chain.</div>
        )}
      </div>
    </div>
  )
}