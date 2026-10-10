import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
    isActive
      ? 'bg-cyan-950/60 text-cyan-100 ring-1 ring-cyan-800/50'
      : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100',
  )

export function WorkspaceShell({ children }: Props) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-20 border-b border-zinc-800/90 bg-zinc-950/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-signal bg-cyan-950/40 text-sm font-bold text-signal"
              aria-hidden
            >
              R
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-cyan-600/90">
                R-View WiFi CSI
              </p>
              <h1 className="text-base font-semibold tracking-tight text-zinc-50 md:text-lg">
                R-View Sensing Studio
              </h1>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-1" aria-label="Primary">
            <NavLink to="/" className={navLinkClass} end>
              Sensing
            </NavLink>
            <NavLink to="/evaluation" className={navLinkClass}>
              Evaluation
            </NavLink>
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="border-t border-zinc-800/80 py-3">
        <div className="mx-auto max-w-7xl px-4 text-xs text-zinc-600">
          <Link to="/" className="hover:text-zinc-400">Sensing</Link>
          <span className="mx-2">·</span>
          <Link to="/evaluation" className="hover:text-zinc-400">Evaluation laboratory</Link>
        </div>
      </footer>
    </div>
  )
}
