import { Route, Routes } from 'react-router-dom'

import { WorkspaceShell } from '@/components/layout/WorkspaceShell'
import { EvaluationPage } from '@/pages/EvaluationPage'
import { ExperimentsPage } from '@/pages/ExperimentsPage'
import { ExplorerPage } from '@/pages/ExplorerPage'
import { LiveSensingPage } from '@/pages/LiveSensingPage'
import { ResearchLabPage } from '@/pages/ResearchLabPage'

export default function App() {
  return (
    <WorkspaceShell>
      <Routes>
        <Route path="/" element={<LiveSensingPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
        <Route path="/research" element={<ResearchLabPage />} />
        <Route path="/explorer" element={<ExplorerPage />} />
        <Route path="/experiments" element={<ExperimentsPage />} />
      </Routes>
    </WorkspaceShell>
  )
}
