import { useEffect, useMemo, useState } from 'react'

import { StudioPageChrome } from '@/components/layout/StudioPageChrome'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DEEP_DEFAULT_CONFIG_FAMILIES } from '@/lib/deepModelBadges'
import { MODEL_FAMILIES } from '@/lib/modelFamilies'

type EvalModel = {
  model_id: string
  family: string
  split_strategy: string
  macro_f1?: number
  accuracy?: number
  per_class_f1?: Record<string, number>
  confusion_matrix?: { labels: string[]; matrix: number[][] }
  latency_ms?: number
}

type EvalSummary = { integrity_note: string; models: EvalModel[] }

type GenModel = {
  model_id: string
  family: string
  split_strategy: string
  macro_f1?: number
  generalization_gap?: number | null
  in_domain_macro_f1?: number
}

type GenPayload = {
  generated_at?: string
  git_sha?: string
  provenance?: { source?: string; note?: string }
  models: GenModel[]
}

const STRATEGIES = ['in_domain', 'cross_user', 'cross_environment'] as const

function fmt(n?: number | null) {
  return n != null && Number.isFinite(n) ? n.toFixed(3) : 'unavailable'
}

export function ModelsPage() {
  const [evalSummary, setEvalSummary] = useState<EvalSummary | null>(null)
  const [generalization, setGeneralization] = useState<GenPayload | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/evaluation/summary.json').then(async (res) => {
        if (!res.ok) throw new Error('evaluation summary missing')
        return (await res.json()) as EvalSummary
      }),
      fetch('/research/generalization.json').then(async (res) => {
        if (!res.ok) return null
        return (await res.json()) as GenPayload
      }),
    ])
      .then(([ev, gen]) => {
        setEvalSummary(ev)
        setGeneralization(gen)
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  const matrix = useMemo(() => {
    const evalByKey = new Map<string, EvalModel>()
    for (const m of evalSummary?.models ?? []) {
      evalByKey.set(`${m.family}:${m.split_strategy}`, m)
    }
    const genByKey = new Map<string, GenModel>()
    for (const m of generalization?.models ?? []) {
      genByKey.set(`${m.family}:${m.split_strategy}`, m)
    }
    return MODEL_FAMILIES.map((family) =>
      STRATEGIES.map((strategy) => {
        const key = `${family}:${strategy}`
        return {
          family,
          strategy,
          eval: evalByKey.get(key) ?? null,
          gen: genByKey.get(key) ?? null,
        }
      }),
    )
  }, [evalSummary, generalization])

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <StudioPageChrome
        showLabelCaveat
        title="Model catalog"
        subtitle="Seven families × three split strategies from frozen artifact exports. Missing metrics show as unavailable — never zero."
      />

      {error && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </div>
      )}

      {evalSummary?.integrity_note && (
        <p className="text-xs text-zinc-500">{evalSummary.integrity_note}</p>
      )}

      {generalization && (
        <p className="text-xs text-zinc-500">
          Provenance: {generalization.provenance?.source} · git {generalization.git_sha ?? '—'} ·{' '}
          {generalization.generated_at ?? '—'}
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-zinc-500">
              <th className="p-2 text-left">Family</th>
              {STRATEGIES.map((s) => (
                <th key={s} className="p-2 text-left capitalize">{s.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => (
              <tr key={row[0].family} className="border-t border-zinc-800">
                <td className="p-2 font-medium text-zinc-200">
                  {row[0].family}
                  {DEEP_DEFAULT_CONFIG_FAMILIES.has(row[0].family) && (
                    <Badge variant="neutral" className="ml-2 text-[10px]">
                      default-config baseline
                    </Badge>
                  )}
                </td>
                {row.map((cell) => (
                  <td key={cell.strategy} className="p-2 align-top text-zinc-400">
                    <div>macro-F1: {fmt(cell.eval?.macro_f1 ?? cell.gen?.macro_f1)}</div>
                    <div>accuracy: {fmt(cell.eval?.accuracy)}</div>
                    <div>
                      gap Δ:{' '}
                      {cell.gen?.generalization_gap != null
                        ? fmt(cell.gen.generalization_gap)
                        : 'unavailable'}
                    </div>
                    <div className="text-[10px] text-zinc-600">
                      latency:{' '}
                      {cell.eval?.latency_ms != null
                        ? `${cell.eval.latency_ms.toFixed(2)} ms`
                        : 'unavailable'}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Card className="surface-card border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm">Deep-model caveat</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-zinc-400">
          cnn1d, gru, tcn (and extended mlp/gbdt when present) use repository default training
          configs — not hyperparameter search. Treat metrics as reproducible baselines, not tuned
          production models.
        </CardContent>
      </Card>
    </div>
  )
}
