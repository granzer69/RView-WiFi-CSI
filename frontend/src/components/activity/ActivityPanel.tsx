import { useMemo } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Prediction } from '@/types/prediction'
import type { SessionMeta } from '@/types/session'

const LOW_CONFIDENCE = 0.45

type TimelineEntry = {
  time_index: number
  activity: string
  confidence: number
  presence: boolean
}

type HistoryEntry = Prediction & { time_index: number; ground_truth?: string }

type Props = {
  meta: SessionMeta | null
  groundTruth: Prediction | null
  modelPrediction: Prediction | null
  predictionHistory: HistoryEntry[]
  timeline: TimelineEntry[]
}

export function ActivityPanel({
  meta,
  groundTruth,
  modelPrediction,
  predictionHistory,
  timeline,
}: Props) {
  const distribution = useMemo(() => {
    const counts = new Map<string, number>()
    for (const e of timeline) {
      counts.set(e.activity, (counts.get(e.activity) ?? 0) + 1)
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])
  }, [timeline])

  const accuracy = useMemo(() => {
    const scored = predictionHistory.filter((p) => p.ground_truth)
    if (!scored.length) return null
    const correct = scored.filter(
      (p) => p.ground_truth && p.activity === p.ground_truth,
    ).length
    return { correct, total: scored.length }
  }, [predictionHistory])

  const lowConf = modelPrediction != null && modelPrediction.confidence < LOW_CONFIDENCE

  return (
    <div className="space-y-4">
      {lowConf && (
        <div className="rounded-md border border-amber-700/60 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          Low model confidence ({(modelPrediction!.confidence * 100).toFixed(1)}%) — below{' '}
          {LOW_CONFIDENCE} threshold.
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <Card className="border-emerald-800/60 surface-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              Ground truth
              <Badge variant="real">REAL DATA</Badge>
              <Badge variant="neutral">GROUND TRUTH</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {meta ? (
              <>
                <p className="text-2xl font-semibold capitalize">{meta.normalized_label}</p>
                <p className="text-zinc-400">
                  Code {meta.activity_code} · dataset label {meta.dataset_label}
                </p>
                <p className="text-xs text-zinc-500">
                  {meta.label_verified_by_folder
                    ? 'Verified by scenario-3 class folder'
                    : 'Inferred from filename code (scenarios 1, 2, 4 unverified)'}
                </p>
                {!meta.label_verified_by_folder && (
                  <p className="text-xs text-amber-200/90">
                    Warning: ground-truth label inferred from metadata — treat activity analysis with care.
                  </p>
                )}
              </>
            ) : (
              <p className="text-zinc-500">Select a session and press play.</p>
            )}
            {groundTruth && (
              <p className="text-xs text-zinc-500">
                Echo tier: dataset_replay · confidence {groundTruth.confidence.toFixed(2)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-sky-800/60 surface-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              Model output
              <Badge variant="model">MODEL PREDICTION</Badge>
              {modelPrediction?.model_version?.startsWith('stub') ? (
                <Badge variant="neutral">STUB</Badge>
              ) : (
                <Badge variant="real">V3 API</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {modelPrediction ? (
              <>
                <p className="text-2xl font-semibold capitalize">{modelPrediction.activity}</p>
                <p className="text-zinc-400">
                  Confidence {(modelPrediction.confidence * 100).toFixed(1)}% · latency{' '}
                  {modelPrediction.latency_ms} ms
                </p>
                {modelPrediction.model_version?.startsWith('stub') ? (
                  <p className="text-xs text-amber-200/90">
                    API unreachable — showing synthetic stub. Start the V3 API on port 45231.
                  </p>
                ) : (
                  <p className="text-xs text-emerald-200/90">
                    Live inference via WebSocket stream (preferred) or POST /predict fallback.
                  </p>
                )}
                {modelPrediction.presence === false && (
                  <p className="text-xs text-zinc-500">Presence: low confidence / empty scene (derived).</p>
                )}
                <p className="text-xs text-zinc-500">Version: {modelPrediction.model_version}</p>
              </>
            ) : (
              <p className="text-zinc-500">Play replay to emit model predictions.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {accuracy && (
        <Card className="surface-card border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm">Session match vs ground truth</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-400">
            {accuracy.correct} / {accuracy.total} predictions match trial label (
            {((accuracy.correct / accuracy.total) * 100).toFixed(0)}%)
          </CardContent>
        </Card>
      )}

      {distribution.length > 0 && (
        <Card className="surface-card border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm">Activity distribution (timeline)</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {distribution.map(([activity, count]) => (
              <Badge key={activity} variant="neutral" className="capitalize">
                {activity}: {count}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="surface-card border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm">Prediction history</CardTitle>
        </CardHeader>
        <CardContent>
          {predictionHistory.length === 0 ? (
            <p className="text-sm text-zinc-500">No predictions yet.</p>
          ) : (
            <ul className="max-h-56 space-y-1 overflow-y-auto text-xs">
              {[...predictionHistory].reverse().map((p, i) => {
                const match = p.ground_truth && p.activity === p.ground_truth
                const mismatch = p.ground_truth && p.activity !== p.ground_truth
                return (
                  <li
                    key={`${p.time_index}-${i}`}
                    className={`flex flex-wrap items-center gap-2 rounded px-2 py-1 ${
                      mismatch ? 'bg-red-950/30' : match ? 'bg-emerald-950/20' : 'bg-zinc-900/40'
                    }`}
                  >
                    <span className="text-zinc-500">t={p.time_index}</span>
                    <span className="capitalize text-zinc-200">{p.activity}</span>
                    <span className="text-zinc-500">{(p.confidence * 100).toFixed(0)}%</span>
                    {p.ground_truth && (
                      <span className={match ? 'text-emerald-400' : 'text-red-300'}>
                        {match ? '✓' : `✗ vs ${p.ground_truth}`}
                      </span>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
