import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { useSourceStatus } from '@/hooks/useSourceStatus'
import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-cyan-950/70 text-cyan-50 shadow-sm ring-1 ring-cyan-700/40'
      : 'text-zinc-400 hover:bg-zinc-900/80 hover:text-zinc-100',
  )

export function WorkspaceShell({ children }: Props) {
  const { status: sourceStatus } = useSourceStatus()
  const sourceLabel =
    sourceStatus?.mode === 'dataset_replay' ? 'DATASET REPLAY' : 'LIVE UNAVAILABLE'

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-20 border-b border-border-subtle/90 bg-zinc-950/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-signal bg-gradient-to-br from-cyan-950/80 to-zinc-900 text-sm font-bold text-signal shadow-inner"
              aria-hidden
            >
              R
            </div>
            <div>
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-signal/75">
                R-View WiFi CSI
              </p>
              <h1 className="font-display text-base font-semibold tracking-tight text-zinc-50 md:text-lg">
                Sensing Studio
              </h1>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-1.5" aria-label="Primary navigation">
            <Badge variant={sourceStatus?.mode === 'dataset_replay' ? 'real' : 'neutral'}>
              {sourceLabel}
            </Badge>
            <NavLink to="/" className={navLinkClass} end>
              Sensing
            </NavLink>
            <NavLink to="/activity" className={navLinkClass}>
              Activity
            </NavLink>
            <NavLink to="/models" className={navLinkClass}>
              Models
            </NavLink>
            <NavLink to="/evaluation" className={navLinkClass}>
              Evaluation
            </NavLink>
            <NavLink to="/research" className={navLinkClass}>
              Research Lab
            </NavLink>
            <NavLink to="/explorer" className={navLinkClass}>
              CSI Explorer
            </NavLink>
            <NavLink to="/experiments" className={navLinkClass}>
              Experiments
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="workstation-grid min-h-[calc(100vh-8rem)]">{children}</main>
      <footer className="border-t border-border-subtle/80 bg-zinc-950/95 py-3">
        <div className="mx-auto max-w-7xl px-4 text-xs text-zinc-500">
          <Link to="/" className="hover:text-zinc-400">Sensing</Link>
          <span className="mx-2">·</span>
          <Link to="/activity" className="hover:text-zinc-400">Activity</Link>
          <span className="mx-2">·</span>
          <Link to="/models" className="hover:text-zinc-400">Models</Link>
          <span className="mx-2">·</span>
          <Link to="/evaluation" className="hover:text-zinc-400">Evaluation laboratory</Link>
          <span className="mx-2">·</span>
          <Link to="/research" className="hover:text-zinc-400">Research lab</Link>
          <span className="mx-2">·</span>
          <Link to="/explorer" className="hover:text-zinc-400">CSI explorer</Link>
          <span className="mx-2">·</span>
          <Link to="/experiments" className="hover:text-zinc-400">Experiment workbench</Link>
        </div>
      </footer>
    </div>
  )
}
