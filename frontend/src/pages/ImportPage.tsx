import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ImportResult } from '../lib/api'

/** Import REAL community data — the only way data enters this site.
 *  No seed, no mock: the website starts empty and stays empty until a
 *  creator imports real evidence from YouTube, GitHub or Discord. */
export function ImportPage() {
  const [ytUrl, setYtUrl] = useState('')
  const [ghRepo, setGhRepo] = useState('')
  const [dcRaw, setDcRaw] = useState('')
  const [imp, setImp] = useState<ImportResult | null>(null)
  const [busy, setBusy] = useState<'github' | 'youtube' | 'discord' | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const doImport = async (kind: 'github' | 'youtube' | 'discord') => {
    setBusy(kind); setImp(null); setErr(null)
    try {
      let r: ImportResult
      if (kind === 'github') r = await api.importGithub(ghRepo.trim())
      else if (kind === 'youtube') r = await api.importYoutube(ytUrl.trim())
      else r = await api.importDiscord(dcRaw)
      setImp(r)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(null) }
  }

  return (
    <div>
      <div className="page-title">Import real community data</div>
      <p className="page-desc">
        This site starts empty. Paste a public source and REMNANT fetches REAL evidence —
        verbatim comments, issues, or messages with full provenance (source, author,
        URL, timestamp). Everything runs through the discovery engine. Never mocked,
        never relabeled.
      </p>

      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16 }}>
        <div className="card" style={{ flex: 1, minWidth: 260 }}>
          <div className="card-title"><h3>YouTube</h3><span className="meta">real comments, no API key</span></div>
          <input className="input" placeholder="https://www.youtube.com/watch?v=ENrzD9HAZK4"
            value={ytUrl} onChange={(ev) => setYtUrl(ev.target.value)} />
          <button className="btn" style={{ marginTop: 10, width: '100%' }}
            disabled={busy !== null || !ytUrl.trim()} onClick={() => doImport('youtube')}>
            {busy === 'youtube' ? 'Fetching real comments…' : 'Import YouTube comments'}
          </button>
          <p className="small muted" style={{ marginTop: 8 }}>
            fetches up to 60 real comments via yt-dlp. Works on this deployment.
          </p>
        </div>

        <div className="card" style={{ flex: 1, minWidth: 260 }}>
          <div className="card-title"><h3>GitHub</h3><span className="meta">real issues + comments, no key</span></div>
          <input className="input" placeholder="foundry-rs/foundry" value={ghRepo}
            onChange={(ev) => setGhRepo(ev.target.value)} />
          <button className="btn" style={{ marginTop: 10, width: '100%' }}
            disabled={busy !== null || !ghRepo.trim()} onClick={() => doImport('github')}>
            {busy === 'github' ? 'Fetching real issues…' : 'Import GitHub issues'}
          </button>
          <p className="small muted" style={{ marginTop: 8 }}>
            pulls real open issues + replies through the GitHub API.
          </p>
        </div>

        <div className="card" style={{ flex: 1, minWidth: 260 }}>
          <div className="card-title"><h3>Discord</h3><span className="meta">paste your export</span></div>
          <textarea className="input" rows={2}
            placeholder={'jade: any chance of a mobile app?\nraz: please make an app'}
            value={dcRaw} onChange={(ev) => setDcRaw(ev.target.value)} />
          <button className="btn" style={{ marginTop: 10, width: '100%' }}
            disabled={busy !== null || !dcRaw.trim()} onClick={() => doImport('discord')}>
            {busy === 'discord' ? 'Importing…' : 'Import Discord messages'}
          </button>
          <p className="small muted" style={{ marginTop: 8 }}>
            accepts pasted lines, a JSON array, or CSV.
          </p>
        </div>
      </div>

      {err && <div className="ev ev-conflict" style={{ marginBottom: 12 }}>Error: {err}</div>}

      {imp && (
        <div className="card">
          <div className="ev ev-support">
            Imported <b className="num">{imp.items}</b> real {imp.source} item{imp.items === 1 ? '' : 's'}
            {imp.video && <> from '<b>{imp.video.slice(0, 45)}</b>'</>}
            {imp.repo && <> from <b>{imp.repo}</b></>}
            {imp.note && <span className="muted"> — {imp.note}</span>}
          </div>
          <div className="meta" style={{ marginTop: 10 }}>Discovery log — what REMNANT decided</div>
          {imp.log.slice(0, 8).map((e, i) => (
            <div className="ev ev-neutral" key={i} style={{ fontSize: 12.5 }}>
              <b className="mono">{e.action}</b>
              {e.issue ? ` #${e.issue}` : ''}
              {e.comment ? ` "${e.comment.slice(0, 45)}"` : ''}
              {e.message ? ` "${e.message.slice(0, 45)}"` : ''}
              {' '}→ <b>{e.remnant}</b>
              {e.verdict !== 'new_candidate' ? ` (${e.verdict})` : ' (new candidate)'}
            </div>
          ))}
          <p className="small muted" style={{ marginTop: 10 }}>
            Imported evidence is REAL and labeled — see it in <Link to="/remnants" style={{ color: 'var(--ink)' }}>Remnants</Link>.
          </p>
        </div>
      )}
    </div>
  )
}