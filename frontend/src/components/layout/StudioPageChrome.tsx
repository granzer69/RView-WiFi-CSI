import type { ReactNode } from 'react'

import { LabelInferenceCaveat } from '@/components/layout/LabelInferenceCaveat'
import { cn } from '@/lib/utils'

type Props = {
  title: string
  subtitle?: string
  eyebrow?: string
  children?: ReactNode
  showLabelCaveat?: boolean
  className?: string
}

export function StudioPageChrome({
  title,
  subtitle,
  eyebrow = 'Scientific workstation',
  children,
  showLabelCaveat = false,
  className,
}: Props) {
  return (
    <header className={cn('studio-page-header space-y-4 border-b border-border-subtle/80 pb-5', className)}>
      <div className="space-y-1">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-signal/80">{eyebrow}</p>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">{title}</h1>
        {subtitle ? <p className="max-w-3xl text-sm leading-relaxed text-zinc-400">{subtitle}</p> : null}
      </div>
      {showLabelCaveat ? <LabelInferenceCaveat compact /> : null}
      {children}
    </header>
  )
}
