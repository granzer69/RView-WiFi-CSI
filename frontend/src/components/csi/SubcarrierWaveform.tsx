import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SUBCARRIERS } from '@/types/csi'

type Props = {
  subcarriers?: number[] | null
  timeIndex?: number
  /** Explorer mode: amplitude vs sample index for one subcarrier */
  values?: number[]
  subcarrierIndex?: number
}

export function SubcarrierWaveform({
  subcarriers = null,
  timeIndex = 0,
  values: timeSeries,
  subcarrierIndex,
}: Props) {
  const values = timeSeries ?? subcarriers ?? []
  const n = values.length || SUBCARRIERS
  const min = values.length ? Math.min(...values) : 0
  const max = values.length ? Math.max(...values) : 1
  const width = 520
  const height = 120
  const pad = 8

  const points =
    values.length > 0
      ? values
          .map((v, i) => {
            const x = pad + (i / Math.max(n - 1, 1)) * (width - pad * 2)
            const t = max > min ? (v - min) / (max - min) : 0.5
            const y = height - pad - t * (height - pad * 2)
            return `${x},${y}`
          })
          .join(' ')
      : ''

  return (
    <Card className="border-signal surface-card">
      <CardHeader className="pb-2">
        <CardTitle className="flex flex-wrap items-center gap-2 text-sm">
          {timeSeries ? 'Subcarrier time series' : 'Subcarrier waveform'}
          <Badge variant="real">REAL DATA</Badge>
          {timeSeries ? (
            <span className="text-xs font-normal text-zinc-500">
              subcarrier {subcarrierIndex ?? 0} · raw amplitude
            </span>
          ) : (
            <span className="text-xs font-normal text-zinc-500">frame t={timeIndex}</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!values.length ? (
          <div className="space-y-2">
            <div className="skeleton-pulse h-[120px] w-full" />
            <p className="text-xs text-zinc-500">No frame yet — connect replay and press play.</p>
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full rounded border border-zinc-800 bg-zinc-900/50"
            role="img"
            aria-label={
              timeSeries
                ? `Amplitude across ${values.length} samples`
                : `Amplitude across ${values.length} subcarriers`
            }
          >
            <polyline
              fill="none"
              stroke="oklch(0.72 0.12 195)"
              strokeWidth="1.5"
              points={points}
            />
            {values.map((v, i) => {
              const x = pad + (i / Math.max(n - 1, 1)) * (width - pad * 2)
              const t = max > min ? (v - min) / (max - min) : 0.5
              const y = height - pad - t * (height - pad * 2)
              return <circle key={i} cx={x} cy={y} r={1.2} fill="oklch(0.62 0.1 175)" />
            })}
          </svg>
        )}
      </CardContent>
    </Card>
  )
}
