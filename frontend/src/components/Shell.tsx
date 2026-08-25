import { NavLink, Outlet } from 'react-router-dom'
import { Footer } from './Footer'

const SECTIONS: { title: string; links: { to: string; label: string; icon: string }[] }[] = [
  {
    title: 'Overview',
    links: [
      { to: '/dashboard', label: 'Dashboard', icon: '⌂' },
      { to: '/remnants', label: 'Remnants', icon: '∷' },
      { to: '/mind', label: 'The Mind', icon: '◌' },
    ],
  },
  {
    title: 'Evidence',
    links: [
      { to: '/system', label: 'System & audit', icon: '≡' },
      { to: '/lab', label: 'Safety lab', icon: '◈' },
    ],
  },
]

/** Dashboard shell: sidebar + content + shared footer. */
export function Shell() {
  return (
    <div className="app-shell">
      <div className="app-body">
        <aside className="sidebar">
          <NavLink to="/" className="brand" style={{ padding: '4px 12px 14px' }}>
            REMNANT<span className="brand-hl">.</span>
          </NavLink>
          {SECTIONS.map((sec) => (
            <div key={sec.title}>
              <div className="side-sec">{sec.title}</div>
              {sec.links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.to === '/dashboard'}
                  className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}
                >
                  <span className="side-icon">{l.icon}</span>
                  {l.label}
                </NavLink>
              ))}
            </div>
          ))}
        </aside>
        <div className="content">
          <Outlet />
        </div>
      </div>
      <Footer />
    </div>
  )
}