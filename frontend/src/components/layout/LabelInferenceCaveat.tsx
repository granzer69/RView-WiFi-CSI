import { cn } from '@/lib/utils'

type Props = {
  className?: string
  compact?: boolean
}

/**
 * ESP-Fi labels for scenarios 1/2/4 are inferred from the scenario-3 folder map — not independently verified.
 */
export function LabelInferenceCaveat({ className, compact }: Props) {
  return (
    <aside
      role="note"
      className={cn(
        'rounded-lg border border-amber-900/50 bg-amber-950/25 text-amber-100/90',
        compact ? 'px-3 py-2 text-xs leading-snug' : 'px-4 py-3 text-sm leading-relaxed',
        className,
      )}
    >
      <p className="font-medium text-amber-200/95">Label inference caveat</p>
      <p className={cn('text-amber-100/85', compact ? 'mt-1' : 'mt-1.5')}>
        ESP-Fi activity labels for scenarios 1, 2, and 4 follow the scenario-3 class-folder map and are{' '}
        <span className="font-semibold text-amber-100">inferred — not independently verified</span>. Treat
        explorer and research metrics as conditional on that mapping; do not treat them as ground-truth
        certification.
      </p>
    </aside>
  )
}
