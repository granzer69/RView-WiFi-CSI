import { useEffect, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

type EvalModel = {
  model_id: string
  family: string
  split_strategy: string
  macro_f1?: number
  weighted_f1?: number
  accuracy?: number
  per_class_f1?: Record<string, number>
  confusion_matrix?: { labels: string[]; matrix: number[][] }
  latency_ms?: number
  model_size_bytes?: number
  integrity_note?: string
}

type EvalSummary = {
  integrity_note: string
  models: EvalModel[]
}

const STRATEGIES = ['in_domain', 'cross_user', 'cross_environment'] as const

function formatBytes(n?: number) {
  if (n == null) return '—'
  if (n < 1024) return `${n} B`
  return `${(n / 1024).toFixed(1)} KiB`
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
                      backgroundColor: `rgba(56, 189, 248, ${0.15 + intensity * 0.75})`,
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

export function EvaluationPage() {
  const [summary, setSummary] = useState<EvalSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [family, setFamily] = useState('rf')

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
    const set = new Set(summary?.models.map((m) => m.family) ?? [])
    return Array.from(set).sort()
  }, [summary])

  useEffect(() => {
    if (families.length && !families.includes(family)) {
      setFamily(families[0])
    }
  }, [families, family])

  const byStrategy = (strategy: string) =>
    summary?.models.filter((m) => m.family === family && m.split_strategy === strategy) ?? []

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4 md:p-6">
      <header className="border-b border-zinc-800 pb-4">
        <h1 className="text-xl font-semibold">V2 evaluation dashboard</h1>
        <p className="text-sm text-zinc-400">
          Offline metrics from trained artifacts · ESP-Fi holdout splits
        </p>
      </header>

      {error && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </div>
      )}

      {summary && (
        <>
          <p className="text-xs text-zinc-500">{summary.integrity_note}</p>
          <div className="flex flex-wrap gap-2">
            {families.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFamily(f)}
                className={`rounded-full px-3 py-1 text-xs ${
                  f === family ? 'bg-sky-900 text-sky-100' : 'bg-zinc-800 text-zinc-300'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <Tabs defaultValue="in_domain">
            <TabsList>
              {STRATEGIES.map((s) => (
                <TabsTrigger key={s} value={s}>{s.replace('_', ' ')}</TabsTrigger>
              ))}
            </TabsList>
            {STRATEGIES.map((strategy) => {
              const rows = byStrategy(strategy)
              const model = rows[0]
              return (
                <TabsContent key={strategy} value={strategy} className="space-y-4">
                  {!model ? (
                    <p className="text-sm text-zinc-500">No metrics for this family/strategy.</p>
                  ) : (
                    <>
                      <div className="grid gap-3 md:grid-cols-4">
                        <Card>
                          <CardHeader><CardTitle className="text-sm">Macro F1</CardTitle></CardHeader>
                          <CardContent className="text-2xl font-semibold">
                            {model.macro_f1?.toFixed(3) ?? '—'}
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader><CardTitle className="text-sm">Accuracy</CardTitle></CardHeader>
                          <CardContent className="text-2xl font-semibold">
                            {model.accuracy?.toFixed(3) ?? '—'}
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader><CardTitle className="text-sm">Latency (test)</CardTitle></CardHeader>
                          <CardContent className="text-2xl font-semibold">
                            {model.latency_ms != null ? `${model.latency_ms.toFixed(2)} ms` : '—'}
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader><CardTitle className="text-sm">Model size</CardTitle></CardHeader>
                          <CardContent className="text-2xl font-semibold">
                            {formatBytes(model.model_size_bytes)}
                          </CardContent>
                        </Card>
                      </div>

                      {model.per_class_f1 && (
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-sm">Per-class F1</CardTitle>
                          </CardHeader>
                          <CardContent className="flex flex-wrap gap-2">
                            {Object.entries(model.per_class_f1).map(([label, f1]) => (
                              <Badge key={label} variant="neutral" className="capitalize">
                                {label}: {f1?.toFixed(3)}
                              </Badge>
                            ))}
                          </CardContent>
                        </Card>
                      )}

                      {model.confusion_matrix && (
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-sm">Confusion matrix (test)</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ConfusionHeatmap
                              labels={model.confusion_matrix.labels}
                              matrix={model.confusion_matrix.matrix}
                            />
                          </CardContent>
                        </Card>
                      )}
                    </>
                  )}
                </TabsContent>
              )
            })}
          </Tabs>
        </>
      )}
    </div>
  )
}
