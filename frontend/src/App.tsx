import { Routes, Route, Navigate } from 'react-router-dom'

import DashboardPage from './pages/DashboardPage.tsx'
import AllPatientsPage from './pages/AllPatientsPage.tsx'

/**
 * App — root routing.
 *
 * Routes:
 *   /          → DashboardPage (daily at-a-glance + register patient)
 *   /patients  → AllPatientsPage (search/filter/audit table)
 *   *          → redirect to / (unknown routes fall back to dashboard)
 *
 * Patient detail modal is URL-synced via /patients?id=<uuid>
 * and handled inside AllPatientsPage (Phase 9).
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/patients" element={<AllPatientsPage />} />
      {/* Catch-all: redirect unknown routes to dashboard */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
