import { Link } from 'react-router-dom'
import { Footer } from '../components/Footer'
import { Reveal } from '../components/Reveal'

/** REMNANT landing page — minimal editorial style.
 *  Warm monochrome, serif display, bento grid. No gradients, no emojis. */

export function Landing() {
  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <div className="brand">
            REMNANT<span className="brand-hl">·</span>
          </div>
          <div className="nav-links">
            <a href="#problem" style={{ color: 'var(--muted)', fontSize: 13.5 }}>The problem</a>
            <a href="#how" style={{ color: 'var(--muted)', fontSize: 13.5 }}>How it works</a>
            <Link to="/dashboard" className="btn" style={{ padding: '8px 16px', fontSize: 13 }}>Open dashboard</Link>
          </div>
        </div>
      </nav>

      <section className="hero wrap">
        <Reveal>
          <span className="hero-tag">Creative Minds Jam #1 — Track 1 · Audience growth &amp; engagement</span>
          <h1 className="display">
            The Mind that remembers what communities leave behind.
          </h1>
          <p className="lede" style={{ marginTop: 20 }}>
            Audience needs disappear into the conversation. REMNANT is a persistent Minds agent
            that remembers unresolved needs across time — preserves uncertainty about why they recur,
            and runs small experiments to discover which needs are actually worth acting on now.
          </p>
          <p className="hero-sub" style={{ marginTop: 12 }}>
            Audience needs disappear from the conversation. REMNANT remembers them.
          </p>
          <div className="btn-row" style={{ marginTop: 36 }}>
            <Link to="/dashboard" className="btn">Open the dashboard</Link>
            <Link to="/lab" className="btn btn-ghost">See the semantic safety lab</Link>
          </div>
        </Reveal>
      </section>

      <section className="section wrap" id="problem" style={{ paddingTop: 40 }}>
        <Reveal>
          <span className="meta">The problem</span>
          <h2 style={{ marginTop: 12, maxWidth: '24ch' }}>
            Every creator has lost a need the audience already told them about.
          </h2>
          <p className="lede" style={{ marginTop: 16 }}>
            A question asked in 2022. Asked again in 2026, in different words. In between, the
            creator never saw it — and neither did any dashboard. The audience was telling them
            what to build; the conversation moved on and the need went dormant.
          </p>
        </Reveal>
        <div className="bento">
          <Reveal className="bento-wide" delay={0}>
            <div className="bento-card">
              <span className="meta">The mechanism</span>
              <h3 style={{ marginTop: 10 }}>One undeniable loop, demonstrated flawlessly</h3>
              <p style={{ marginTop: 8 }}>
                historical evidence → current evidence → competing hypotheses → concrete experiment →
                observable outcome → persistent belief update. Then reload the app and ask:
                “What do you currently believe about this need?” The Mind remembers the entire chain.
              </p>
            </div>
          </Reveal>
          <Reveal className="bento-narrow" delay={80}>
            <div className="bento-card">
              <span className="meta">Why that matters</span>
              <h3 style={{ marginTop: 10 }}>Not a summarizer. Not a chatbot.</h3>
              <p style={{ marginTop: 8 }}>
                The Minds agent is integral to the core value: persistent memory of unresolved needs.
                Remove the Mind, and the product stops meaning what it claims.
              </p>
            </div>
          </Reveal>
          <Reveal className="bento-third" delay={0}>
            <div className="bento-card">
              <span className="meta">Uncertainty</span>
              <h3 style={{ marginTop: 10 }}>Never fake confidence</h3>
              <p style={{ marginTop: 8 }}>
                Evidence strength is qualitative — low, medium, high. The Mind can say “I don't know”
                and choose a probe to find out.
              </p>
            </div>
          </Reveal>
          <Reveal className="bento-third" delay={80}>
            <div className="bento-card">
              <span className="meta">Continuity</span>
              <h3 style={{ marginTop: 10 }}>Picks up where it left off</h3>
              <p style={{ marginTop: 8 }}>
                Every belief-critical change is mirrored into the persistent Mind's memory. Restart
                the app; the chain is still there.
              </p>
            </div>
          </Reveal>
          <Reveal className="bento-third" delay={160}>
            <div className="bento-card">
              <span className="meta">Autonomy</span>
              <h3 style={{ marginTop: 10 }}>Acts without a click</h3>
              <p style={{ marginTop: 8 }}>
                The observatory reviews dormant remnants, surfaces possible recurrences, and recommends
                experiments — with action provenance, cooldown, and approval boundaries.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="section wrap" id="how" style={{ paddingTop: 40 }}>
        <Reveal>
          <span className="meta">How it works</span>
          <h2 style={{ marginTop: 12 }}>Six steps, all inspectable</h2>
        </Reveal>
        <div className="steps">
          {[
            ['01', 'Expressions', 'Comments, Discord, GitHub — every audience input, with source and timestamp.'],
            ['02', 'Hypotheses', 'H1-H4 held simultaneously. Persistent need, recurrence, trend, coincidence.'],
            ['03', 'Evidence', 'Supporting and contradicting evidence for each — never suppressed.'],
            ['04', 'Experiment', 'Smallest pre-registered probe. Metric and threshold set before observing.'],
            ['05', 'Outcome', 'The observed number crosses or misses the threshold. Deterministic verdict.'],
            ['06', 'Belief', 'The Mind updates its persistent belief and remembers the whole chain.'],
          ].map(([n, t, d], i) => (
            <Reveal key={n} delay={i * 60}>
              <div className="step">
                <span className="meta">{n}</span>
                <div className="step-title">{t}</div>
                <p>{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="section wrap" style={{ paddingTop: 24 }}>
        <Reveal>
          <div style={{ borderTop: '2px solid var(--ink)', paddingTop: 32 }}>
            <h2 style={{ maxWidth: '24ch' }}>Built to be probed by skeptical judges.</h2>
            <p className="lede" style={{ marginTop: 14 }}>
              Every claim in this product is backed by a persisted artifact: the threshold was set
              before the observation, the observed value is a number, synthetic data is labeled,
              and the belief chain replays after restart.
            </p>
            <div className="btn-row" style={{ marginTop: 28 }}>
              <Link to="/dashboard" className="btn">Explore the dashboard</Link>
            </div>
          </div>
        </Reveal>
      </section>

      <Footer />
    </div>
  )
}