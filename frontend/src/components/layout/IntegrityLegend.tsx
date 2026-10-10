import { Badge } from '@/components/ui/badge'

export function IntegrityLegend() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
      <span className="font-medium text-zinc-300">Integrity:</span>
      <Badge variant="real">REAL DATA</Badge>
      <span>ESP-Fi amplitude &amp; filename labels</span>
      <Badge variant="simulated">SIMULATED POSITION</Badge>
      <span>Dataset replay — not localization</span>
      <Badge variant="model">MODEL PREDICTION</Badge>
      <span>Stub until V2 training</span>
    </div>
  )
}
