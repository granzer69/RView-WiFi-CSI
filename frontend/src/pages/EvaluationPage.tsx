import { useEffect, useMemo, useState } from 'react'

import { StudioPageChrome } from '@/components/layout/StudioPageChrome'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MODEL_FAMILIES } from '@/lib/modelFamilies'

type PerClassMetrics = Record<string, number>

type EvalModel = {
  model_id: string
  family: string
  split_strategy: string
  macro_f1?: number
  weighted_f1?: number
  accuracy?: number
  per_class_f1?: PerClassMetrics
  per_class_precision?: PerClassMetrics
  per_class_recall?: PerClassMetrics
  confusion_matrix?: { labels: string[]; matrix: number[][] }
  latency_ms?: number
  model_size_bytes?: number
  integrity_note?: string
}

type EvalSummary = {
  integrity_note: string
  models: EvalModel[]
}

const FAMILIES = MODEL_FAMILIES
const STRATEGIES = ['in_domain', 'cross_user', 'cross_environment'] as const

function formatBytes(n?: number) {
  if (n == null) return 'unavailable'
  if (n < 1024) return `${n} B`
  return `${(n / 1024).toFixed(1)} KiB`
}

function formatLatency(n?: number) {
  return n != null ? `${n.toFixed(2)} ms` : 'unavailable'
}

function ConfusionHeatmap({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const max = Math.max(...matrix.flat(), 1)
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-1 text-zinc-500">pred ↓ / true →</th>
            {labels.map((l) => (
              <th key={l} className="p-1 font-normal capitalize text-zinc-400">
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <td className="p-1 capitalize text-zinc-400">{labels[i]}</td>
              {row.map((cell, j) => {
                const intensity = cell / max
                return (
                  <td
                    key={`${i}-${j}`}
                    className="p-1 text-center text-zinc-100"
                    style={{
                      backgroundColor: `color-mix(in oklch, var(--color-signal-cyan) ${(0.15 + intensity * 0.75) * 100}%, transparent)`,
                    }}
                  >
                    {cell}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ModelMetricsPanel({ model, title }: { model: EvalModel | null; title: string }) {
  if (!model) {
    return (
      <Card className="surface-card border-zinc-800">
        <CardHeader><CardTitle className="text-sm">{title}</CardTitle></CardHeader>
        <CardContent className="text-sm text-zinc-500">No metrics for this selection.</CardContent>
      </Card>
    )
  }

  const labels = model.per_class_f1
    ? Object.keys(model.per_class_f1)
    : model.confusion_matrix?.labels ?? []

  return (
    <Card className="surface-card border-zinc-800">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-sm">
          {title}
          <Badge variant="model">{model.family}</Badge>
          <Badge variant="neutral">{model.split_strategy.replace(/_/g, ' ')}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <p className="text-[10px] uppercase text-zinc-500">Macro F1</p>
            <p className="text-xl font-semibold">{model.macro_f1?.toFixed(3) ?? '—'}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-zinc-500">Accuracy</p>
            <p className="text-xl font-semibold">{model.accuracy?.toFixed(3) ?? '—'}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-zinc-500">Latency (test)</p>
            <p className="text-sm font-medium">{formatLatency(model.latency_ms)}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-zinc-500">Model size</p>
            <p className="text-sm font-medium">{formatBytes(model.model_size_bytes)}</p>
          </div>
        </div>

        {labels.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium uppercase text-zinc-500">Per-class metrics</p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-zinc-500">
                    <th className="p-1 text-left">Class</th>
                    <th className="p-1 text-right">Precision</th>
                    <th className="p-1 text-right">Recall</th>
                    <th className="p-1 text-right">F1</th>
                  </tr>
                </thead>
                <tbody>
                  {labels.map((label) => (
                    <tr key={label} className="border-t border-zinc-800/80">
                      <td className="p-1 capitalize text-zinc-300">{label}</td>
                      <td className="p-1 text-right text-zinc-400">
                        {model.per_class_precision?.[label]?.toFixed(3) ?? 'unavailable'}
                      </td>
                      <td className="p-1 text-right text-zinc-400">
                        {model.per_class_recall?.[label]?.toFixed(3) ?? 'unavailable'}
                      </td>
                      <td className="p-1 text-right text-zinc-200">
                        {model.per_class_f1?.[label]?.toFixed(3) ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {model.confusion_matrix && (
          <div>
            <p className="mb-2 text-xs font-medium uppercase text-zinc-500">Confusion matrix</p>
            <ConfusionHeatmap
              labels={model.confusion_matrix.labels}
              matrix={model.confusion_matrix.matrix}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

type SlotState = { family: string; strategy: string }

function SelectionControls({
  label,
  value,
  families,
  onChange,
}: {
  label: string
  value: SlotState
  families: string[]
  onChange: (next: SlotState) => void
}) {
  return (
    <div className="space-y-2 rounded-lg border border-zinc-800 surface-card p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{label}</p>
      <div className="flex flex-wrap gap-1">
        {families.map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => onChange({ ...value, family: f })}
            className={`rounded-full px-2.5 py-1 text-xs ${
              value.family === f ? 'bg-cyan-900 text-cyan-100' : 'bg-zinc-800 text-zinc-300'
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-1">
        {STRATEGIES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onChange({ ...value, strategy: s })}
            className={`rounded-full px-2.5 py-1 text-xs ${
              value.strategy === s ? 'bg-teal-900 text-teal-100' : 'bg-zinc-800 text-zinc-300'
            }`}
          >
            {s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
    </div>
  )
}

export function EvaluationPage() {
  const [summary, setSummary] = useState<EvalSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [slotA, setSlotA] = useState<SlotState>({ family: 'rf', strategy: 'in_domain' })
  const [slotB, setSlotB] = useState<SlotState>({ family: 'logreg', strategy: 'cross_user' })

  useEffect(() => {
    fetch('/evaluation/summary.json')
      .then(async (res) => {
        if (!res.ok) throw new Error('Run scripts/export_evaluation_summary.py first')
        return (await res.json()) as EvalSummary
      })
      .then(setSummary)
      .catch((err: Error) => setError(err.message))
  }, [])

  const families = useMemo(() => {
    const fromData = new Set(summary?.models.map((m) => m.family) ?? [])
    return FAMILIES.filter((f) => fromData.has(f) || fromData.size === 0)
  }, [summary])

  const resolve = (slot: SlotState) =>
    summary?.models.find((m) => m.family === slot.family && m.split_strategy === slot.strategy) ?? null

  const modelA = resolve(slotA)
  const modelB = resolve(slotB)

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <StudioPageChrome
        title="Evaluation laboratory"
        subtitle="Offline metrics from exported summary.json only — no live or fabricated scores. Compare holdout split strategies side by side."
      />

      {error && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </div>
      )}

      {!summary && !error && (
        <div className="space-y-2">
          <div className="skeleton-pulse h-8 w-48" />
          <div className="skeleton-pulse h-32 w-full" />
        </div>
      )}

      {summary && (
        <>
          <div className="rounded-md border border-cyan-900/40 bg-cyan-950/20 px-3 py-2 text-xs text-cyan-100/90">
            {summary.integrity_note}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <SelectionControls label="Compare A" value={slotA} families={families} onChange={setSlotA} />
            <SelectionControls label="Compare B" value={slotB} families={families} onChange={setSlotB} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <ModelMetricsPanel model={modelA} title="Selection A" />
            <ModelMetricsPanel model={modelB} title="Selection B" />
          </div>
        </>
      )}
    </div>
  )
}
