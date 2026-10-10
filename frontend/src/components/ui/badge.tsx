import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        real: 'border-[var(--color-real-border)] text-emerald-200 bg-emerald-950/40',
        simulated: 'border-dashed border-amber-500/80 text-amber-100 bg-amber-950/30',
        model: 'border-[var(--color-model-blue)] text-sky-200 bg-sky-950/40',
        neutral: 'border-zinc-600 text-zinc-300 bg-zinc-900',
      },
    },
    defaultVariants: { variant: 'neutral' },
  },
)

export function Badge({
  className,
  variant,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
