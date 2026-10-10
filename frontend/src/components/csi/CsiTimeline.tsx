import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type Props = {
  timeIndex: number
  totalSteps: number
  label: string
}

export function CsiTimeline({ timeIndex, totalSteps, label }: Props) {
  const progress = totalSteps > 1 ? timeIndex / (totalSteps - 1) : 0
  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="relative h-8 rounded bg-zinc-800">
          <div
            className="absolute inset-y-0 left-0 rounded bg-emerald-700/50"
            style={{ width: `${progress * 100}%` }}
          />
          <div
            className="absolute top-0 h-full w-0.5 bg-emerald-300"
            style={{ left: `${progress * 100}%` }}
          />
        </div>
        <p className="text-xs text-zinc-500">
          Ground-truth band: <span className="capitalize text-zinc-300">{label}</span> (full trial)
        </p>
      </CardContent>
    </Card>
  )
}
