import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Prediction } from '@/types/prediction'

type Props = {
  scenarioId: number
  scenarioName?: string
  prediction: Prediction | null
}

const ROOM_LABELS: Record<number, string> = {
  1: 'Corridor (illustrative)',
  2: 'Office (illustrative)',
  3: 'Boardroom (illustrative)',
  4: 'Laboratory (illustrative)',
}

export function SimulatedFloorPlan({ scenarioId, scenarioName, prediction }: Props) {
  const spatial = prediction?.spatial
  const x = spatial?.x ?? 0.5
  const y = spatial?.y ?? 0.5
  const px = 40 + x * 220
  const py = 30 + y * 140

  return (
    <Card className="border-dashed border-amber-600/50">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Spatial
          <Badge variant="simulated">SIMULATED POSITION</Badge>
          <Badge variant="neutral">DATASET REPLAY</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-amber-100/90">
          Simulated position for demonstration only. ESP-Fi does not include location labels.
        </p>
        <p className="text-sm text-zinc-400">
          Environment: {scenarioName ?? ROOM_LABELS[scenarioId] ?? `scenario ${scenarioId}`}
        </p>
        <svg viewBox="0 0 300 200" className="w-full max-w-md rounded-md bg-zinc-950/80">
          <rect
            x="30"
            y="20"
            width="240"
            height="160"
            fill="none"
            stroke="oklch(0.75 0.15 75)"
            strokeDasharray="6 4"
            strokeWidth="2"
            rx="4"
          />
          <text x="36" y="36" fill="oklch(0.75 0.12 75)" fontSize="10">
            SIMULATED POSITION
          </text>
          <circle cx={px} cy={py} r="10" fill="oklch(0.65 0.18 250)" opacity="0.9" />
          <circle cx={px} cy={py} r="14" fill="none" stroke="oklch(0.65 0.18 250)" strokeWidth="1" />
        </svg>
        {spatial && (
          <p className="text-xs text-zinc-500">
            Normalized x={spatial.x.toFixed(2)}, y={spatial.y.toFixed(2)} · spatial.simulated=
            {String(spatial.simulated)}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
