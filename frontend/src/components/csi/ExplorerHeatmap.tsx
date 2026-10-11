import { useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type Props = {
  amplitude: number[][] 
  sharedMin?: number
  sharedMax?: number
  title?: string
}

function colorFor(value: number, min: number, max: number): string {
  const t = max > min ? (value - min) / (max - min) : 0.5
  const hue = 240 - t * 200
  return `hsl(${hue} 70% 45%)`
}

export function ExplorerHeatmap({ amplitude, sharedMin, sharedMax, title }: Props) {
  const [hover, setHover] = useState<{ row: number; col: number; value: number } | null>(null)
  const [rowStart, setRowStart] = useState(0)
  const [rowEnd, setRowEnd] = useState<number | null>(null)

  const rows = amplitude.length
  const cols = amplitude[0]?.length ?? 52
  const effectiveEnd = rowEnd ?? rows

  const windowed = useMemo(() => {
    const end = Math.min(effectiveEnd, rows)
    const start = Math.max(0, Math.min(rowStart, end))
    return amplitude.slice(start, end)
  }, [amplitude, rowStart, effectiveEnd, rows])

  const { min, max } = useMemo(() => {
    const flat = windowed.flat()
    if (!flat.length) return { min: 0, max: 1 }
    if (sharedMin != null && sharedMax != null) {
      return { min: sharedMin, max: sharedMax }
    }
    return { min: Math.min(...flat), max: Math.max(...flat) }
  }, [windowed, sharedMin, sharedMax])

  const cellW = 4
  const cellH = 3

  return (
    <Card className="border-cyan-900/40">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          {title ?? 'CSI amplitude heatmap'}
          <Badge variant="real">RAW AMPLITUDE</Badge>
        </CardTitle>
        <p className="text-xs text-zinc-500">
          Horizontal: sample index · Vertical: subcarrier · Origin lower (matches backend imshow on
          amplitude.T)
        </p>
      </CardHeader>
      <CardContent>
        {rows === 0 ? (
          <p className="text-sm text-zinc-500">No amplitude rows loaded.</p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-zinc-400">
              <label className="flex items-center gap-2">
                Region start
                <input
                  type="number"
                  min={0}
                  max={rows - 1}
                  value={rowStart}
                  className="w-20 rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
                  onChange={(e) => setRowStart(Number(e.target.value))}
                />
              </label>
              <label className="flex items-center gap-2">
                Region end
                <input
                  type="number"
                  min={1}
                  max={rows}
                  value={effectiveEnd}
                  className="w-20 rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
                  onChange={(e) => setRowEnd(Number(e.target.value))}
                />
              </label>
            </div>
            <div className="overflow-x-auto">
              <svg
                width={Math.max(cols * cellW, 200)}
                height={Math.max(windowed[0]?.length ?? cols * cellH, 80)}
                className="rounded border border-zinc-800"
                onMouseLeave={() => setHover(null)}
              >
                {windowed.map((row, ri) =>
                  row.map((v, ci) => {
                    const sampleIndex = rowStart + ri
                    return (
                      <rect
                        key={`${sampleIndex}-${ci}`}
                        x={ri * cellW}
                        y={ci * cellH}
                        width={cellW}
                        height={cellH}
                        fill={colorFor(v, min, max)}
                        onMouseEnter={() =>
                          setHover({ row: sampleIndex, col: ci, value: v })
                        }
                      />
                    )
                  }),
                )}
              </svg>
            </div>
            {hover && (
              <p className="mt-2 text-xs text-cyan-200/90">
                sample {hover.row}, subcarrier {hover.col} → {hover.value.toFixed(4)}
              </p>
            )}
            <p className="mt-2 text-xs text-zinc-500">
              Showing samples {rowStart}–{rowStart + windowed.length - 1} of {rows - 1} max index
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
