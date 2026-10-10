import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type Props = {
  heatmap: number[][] 
  timeIndex: number
  totalSteps: number
}

function colorFor(value: number, min: number, max: number): string {
  const t = max > min ? (value - min) / (max - min) : 0.5
  const hue = 240 - t * 200
  return `hsl(${hue} 70% 45%)`
}

export function CsiHeatmap({ heatmap, timeIndex, totalSteps }: Props) {
  const flat = heatmap.flat()
  const min = flat.length ? Math.min(...flat) : 0
  const max = flat.length ? Math.max(...flat) : 1
  const rows = heatmap.length
  const cols = heatmap[0]?.length ?? 52

  return (
    <Card className="border-emerald-900/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          CSI heatmap (rolling)
          <Badge variant="real">REAL DATA</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {rows === 0 ? (
          <p className="text-sm text-zinc-500">Press play to stream amplitude rows from exported MAT.</p>
        ) : (
          <div className="overflow-x-auto">
            <svg
              width={Math.max(cols * 4, 200)}
              height={Math.max(rows * 3, 80)}
              className="rounded border border-zinc-800"
            >
              {heatmap.map((row, ri) =>
                row.map((v, ci) => (
                  <rect
                    key={`${ri}-${ci}`}
                    x={ci * 4}
                    y={ri * 3}
                    width={4}
                    height={3}
                    fill={colorFor(v, min, max)}
                  />
                )),
              )}
            </svg>
          </div>
        )}
        <p className="mt-2 text-xs text-zinc-500">
          Index {timeIndex} / {totalSteps - 1} · nominal replay rate — matrix index, not verified
          capture clock
        </p>
      </CardContent>
    </Card>
  )
}
