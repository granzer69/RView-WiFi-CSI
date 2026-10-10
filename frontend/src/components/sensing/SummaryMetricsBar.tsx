import type { ReactNode } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { Prediction } from '@/types/prediction'
import type { SessionMeta } from '@/types/session'

type Props = {
  meta: SessionMeta | null
  groundTruth: Prediction | null
  modelPrediction: Prediction | null
}

function MetricCell({
  label,
  value,
  sub,
  warn,
}: {
  label: string
  value: string
  sub?: ReactNode
  warn?: boolean
}) {
  return (
    <Card className={`surface-card border-zinc-800/80 ${warn ? 'border-amber-700/50' : ''}`}>
      <CardContent className="p-3">
        <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">{label}</p>
        <p className={`text-lg font-semibold capitalize ${warn ? 'text-amber-100' : 'text-zinc-50'}`}>
          {value}
        </p>
        {sub && <p className="text-xs text-zinc-500">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export function SummaryMetricsBar({ meta, groundTruth, modelPrediction }: Props) {
  const gtLabel = meta?.normalized_label ?? groundTruth?.activity ?? '—'
  const predLabel = modelPrediction?.activity ?? '—'
  const conf =
    modelPrediction != null ? `${(modelPrediction.confidence * 100).toFixed(1)}%` : '—'
  const latency =
    modelPrediction?.latency_ms != null ? `${modelPrediction.latency_ms.toFixed(1)} ms` : '—'
  const lowConf = modelPrediction != null && modelPrediction.confidence < 0.45

  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCell
        label="Predicted activity"
        value={String(predLabel)}
        sub={modelPrediction ? <Badge variant="model" className="mt-1">MODEL</Badge> : undefined}
      />
      <MetricCell label="Ground truth" value={String(gtLabel)} sub="Dataset label" />
      <MetricCell label="Confidence" value={conf} warn={lowConf} sub={lowConf ? 'Below 0.45 threshold' : undefined} />
      <MetricCell label="Inference latency" value={latency} />
    </div>
  )
}
