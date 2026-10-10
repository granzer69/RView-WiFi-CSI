import { Link, Route, Routes } from 'react-router-dom'

import { EvaluationPage } from '@/pages/EvaluationPage'
import { LiveSensingPage } from '@/pages/LiveSensingPage'

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <nav className="flex gap-4 border-b border-zinc-800 px-4 py-2 text-sm">
        <Link className="text-sky-400 hover:underline" to="/">Live replay</Link>
        <Link className="text-sky-400 hover:underline" to="/evaluation">Evaluation</Link>
      </nav>
      <Routes>
        <Route path="/" element={<LiveSensingPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
      </Routes>
    </div>
  )
}
