import { Link } from 'react-router-dom'

/** Shared footer — used on the landing page and inside the dashboard. */

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div>
          <div className="footer-brand">REMNANT</div>
          <p>The Mind that remembers what communities leave behind.</p>
          <p style={{ marginTop: 8 }}>
            Built for Creative Minds Jam #1: Hong Kong — Minds by Animoca Brands.
          </p>
        </div>
        <div className="footer-col">
          <span className="meta">Product</span>
          <Link to="/">Overview</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/remnants">Remnants</Link>
          <Link to="/lab">Semantic safety</Link>
        </div>
        <div className="footer-col">
          <span className="meta">Systems</span>
          <Link to="/mind">The Mind</Link>
          <Link to="/system">System</Link>
        </div>
        <div className="footer-col">
          <span className="meta">Honesty</span>
          <p>Evidence is either real, labeled synthetic, or not claimed.</p>
          <p>No fake confidence numbers. No invented audience counts.</p>
        </div>
      </div>
    </footer>
  )
}