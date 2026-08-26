import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AdversarialResult, type ImportResult } from '../lib/api'

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
  const [ghRepo, setGhRepo] = useState('')
  const [ytUrl, setYtUrl] = useState('')
  const [dcRaw, setDcRaw] = useState('')
  const [imp, setImp] = useState<ImportResult | null>(null)
  const [impBusy, setImpBusy] = useState<'github' | 'youtube' | 'discord' | null>(null)

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

  const doImport = async (kind: 'github' | 'youtube' | 'discord') => {
    setImpBusy(kind); setImp(null); setErr(null)
    try {
      let r: ImportResult
      if (kind === 'github') r = await api.importGithub(ghRepo.trim())
      else if (kind === 'youtube') r = await api.importYoutube(ytUrl.trim())
      else r = await api.importDiscord(dcRaw)
      setImp(r)
    } catch (e) { setErr((e as Error).message) } finally { setImpBusy(null) }
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

      {/* Import real community data */}
      <div className="card-title" style={{ marginTop: 24 }}><h3>Import real community data</h3></div>
      <div className="card" style={{ marginBottom: 8 }}>
        <p className="small muted" style={{ marginBottom: 12 }}>
          Fetch REAL evidence from public sources, right from this site — YouTube comments,
          GitHub issues, or pasted Discord exports. Each expression keeps full provenance
          (source, author, url, timestamps) and flows through the same discovery engine.
        </p>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <label className="label">YouTube video URL</label>
            <input className="input" placeholder="https://www.youtube.com/watch?v=..." value={ytUrl}
              onChange={(ev) => setYtUrl(ev.target.value)} />
            <button className="btn" style={{ marginTop: 8 }} disabled={impBusy !== null || !ytUrl.trim()}
              onClick={() => doImport('youtube')}>
              {impBusy === 'youtube' ? 'Fetching…' : 'Import YouTube comments'}
            </button>
            <p className="small muted" style={{ marginTop: 6 }}>fetches up to 60 real comments via yt-dlp (no API key).</p>
          </div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <label className="label">GitHub repo (owner/repo)</label>
            <input className="input" placeholder="foundry-rs/foundry" value={ghRepo}
              onChange={(ev) => setGhRepo(ev.target.value)} />
            <button className="btn" style={{ marginTop: 8 }} disabled={impBusy !== null || !ghRepo.trim()}
              onClick={() => doImport('github')}>
              {impBusy === 'github' ? 'Fetching…' : 'Import GitHub issues'}
            </button>
            <p className="small muted" style={{ marginTop: 6 }}>fetches real open issues + comments via the GitHub API (no key).</p>
          </div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <label className="label">Discord export (paste)</label>
            <textarea className="input" rows={2} placeholder={'jade: any chance of a mobile app?\nraz: please make an app'}
              value={dcRaw} onChange={(ev) => setDcRaw(ev.target.value)} />
            <button className="btn" style={{ marginTop: 8 }} disabled={impBusy !== null || !dcRaw.trim()}
              onClick={() => doImport('discord')}>
              {impBusy === 'discord' ? 'Fetching…' : 'Import Discord messages'}
            </button>
            <p className="small muted" style={{ marginTop: 6 }}>accepts pasted lines, JSON array, or CSV.</p>
          </div>
        </div>
        {imp && (
          <div className="evidence" style={{ marginTop: 14 }}>
            <div className="ev ev-support">
              Imported <b className="num">{imp.items}</b> real {imp.source} item{imp.items === 1 ? '' : 's'}
              {imp.video && <> from '<b>{imp.video.slice(0, 45)}</b>'</>}
              {imp.repo && <> from <b>{imp.repo}</b></>}
              {imp.note && <span className="muted"> — {imp.note}</span>}
            </div>
            <div className="meta" style={{ marginTop: 6 }}>Discovery log — what REMNANT decided</div>
            {imp.log.slice(0, 6).map((e, i) => (
              <div className="ev ev-neutral" key={i} style={{ fontSize: 12.5 }}>
                <b className="mono">{e.action}</b> {e.issue ? `#${e.issue}` : ''} {e.comment ? `"${e.comment.slice(0, 40)}"` : ''} {e.message ? `"${e.message.slice(0, 40)}"` : ''}
                {' '}→ <b>{e.remnant}</b> {e.verdict !== 'new_candidate' ? `(${e.verdict})` : '(new candidate)'}
              </div>
            ))}
            <p className="small muted" style={{ marginTop: 8 }}>
              Imported evidence is REAL and labeled — never relabeled as synthetic. See it in <Link to="/remnants" style={{ color: 'var(--ink)' }}>Remnants</Link>.
            </p>
          </div>
        )}
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