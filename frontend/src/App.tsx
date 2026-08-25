import { Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { Landing } from './pages/Landing'
import { Dashboard } from './pages/Dashboard'
import { RemnantsPage } from './pages/RemnantsPage'
import { RemnantDetail } from './pages/RemnantDetail'
import { MindPage } from './pages/MindPage'
import { SystemPage } from './pages/SystemPage'
import { LabPage } from './pages/LabPage'

export default function App() {
  return (
    <Routes>
      {/* Landing (minimal editorial style, own nav + footer) */}
      <Route path="/" element={<Landing />} />
      {/* Dashboard shell: sidebar + content + shared footer */}
      <Route element={<Shell />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/remnants" element={<RemnantsPage />} />
        <Route path="/remnants/:rid" element={<RemnantDetail />} />
        <Route path="/mind" element={<MindPage />} />
        <Route path="/system" element={<SystemPage />} />
        <Route path="/lab" element={<LabPage />} />
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  )
}