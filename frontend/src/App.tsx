import { Route, Routes } from 'react-router-dom'

import { WorkspaceShell } from '@/components/layout/WorkspaceShell'
import { EvaluationPage } from '@/pages/EvaluationPage'
import { LiveSensingPage } from '@/pages/LiveSensingPage'

export default function App() {
  return (
    <WorkspaceShell>
      <Routes>
        <Route path="/" element={<LiveSensingPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
      </Routes>
    </WorkspaceShell>
  )
}
