import { useCallback, useEffect, useState } from 'react'

<<<<<<< HEAD
import { StudioPageChrome } from '@/components/layout/StudioPageChrome'
import { Badge } from '@/components/ui/badge'
import { MODEL_FAMILIES } from '@/lib/modelFamilies'
=======
import { Badge } from '@/components/ui/badge'
>>>>>>> origin/main
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  fetchExperimentRuns,
  fetchExperimentSchema,
  fetchRunMetrics,
  previewExperimentRun,
  startExperimentRun,
  type ExperimentRun,
  type ExperimentSchema,
} from '@/services/experimentsClient'

<<<<<<< HEAD
const FAMILIES = MODEL_FAMILIES
=======
const FAMILIES = ['logreg', 'rf', 'cnn1d', 'gru'] as const
>>>>>>> origin/main

export function ExperimentsPage() {
  const [schema, setSchema] = useState<ExperimentSchema | null>(null)
  const [runs, setRuns] = useState<ExperimentRun[]>([])
  const [family, setFamily] = useState<string>('logreg')
  const [seed, setSeed] = useState(42)
  const [strategies, setStrategies] = useState<string[]>([
    'in_domain',
    'cross_user',
    'cross_environment',
  ])
  const [modelParams, setModelParams] = useState<Record<string, string>>({ C: '1.0' })
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null)
  const [selectedRun, setSelectedRun] = useState<string>('')

  const refreshRuns = useCallback(() => {
    fetchExperimentRuns().then(setRuns).catch(() => setRuns([]))
  }, [])

  useEffect(() => {
    fetchExperimentSchema().then(setSchema).catch((e: Error) => setError(e.message))
    refreshRuns()
    const timer = window.setInterval(refreshRuns, 5000)
    return () => window.clearInterval(timer)
  }, [refreshRuns])

  useEffect(() => {
    if (!schema) return
    const hp = schema.hyperparameters[family]
    if (!hp) return
    const next: Record<string, string> = {}
    for (const [key, spec] of Object.entries(hp)) {
      const def = (spec as { default?: unknown }).default
      next[key] = def == null ? '' : String(def)
    }
    setModelParams(next)
  }, [family, schema])

  async function onPreview() {
    setError(null)
    try {
      const model: Record<string, unknown> = {}
      for (const [k, v] of Object.entries(modelParams)) {
        if (v === '') model[k] = null
        else if (/^\d+$/.test(v)) model[k] = Number(v)
        else if (/^\d*\.\d+$/.test(v)) model[k] = Number(v)
        else model[k] = v
      }
      const res = await previewExperimentRun({
        family,
        seed,
        strategies,
        model,
      })
      setPreview((res as { preview?: Record<string, unknown> }).preview ?? null)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function onStart() {
    setError(null)
    try {
      const model: Record<string, unknown> = {}
      for (const [k, v] of Object.entries(modelParams)) {
        if (v === '') model[k] = null
        else if (/^\d+$/.test(v)) model[k] = Number(v)
        else if (/^\d*\.\d+$/.test(v)) model[k] = Number(v)
        else model[k] = v
      }
      await startExperimentRun({ family, seed, strategies, model })
      refreshRuns()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function loadMetrics(runId: string) {
    setSelectedRun(runId)
    try {
      const m = await fetchRunMetrics(runId, 'in_domain')
      setMetrics(m)
    } catch {
      setMetrics(null)
    }
  }

  function toggleStrategy(s: string) {
    setStrategies((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
    )
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
<<<<<<< HEAD
      <StudioPageChrome
        showLabelCaveat
        title="Experiment workbench"
        subtitle="Configure ESP-Fi training via the v2 pipeline. Outputs land under artifacts/workbench/; frozen artifacts/v2_* baseline run IDs are never modified."
      />
=======
      <div>
        <h2 className="text-xl font-semibold text-zinc-50">Experiment Workbench</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Configure ESP-Fi training runs using the existing v2 pipeline. Outputs land under{' '}
          <code className="text-zinc-300">artifacts/workbench/</code> — frozen{' '}
          <code className="text-zinc-300">artifacts/v2_*</code> baselines are never modified.
        </p>
      </div>
>>>>>>> origin/main

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="py-4 text-sm text-red-200">{error}</CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Run configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <label className="block">
              <span className="text-zinc-400">Model family</span>
              <select
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2"
                value={family}
                onChange={(e) => setFamily(e.target.value)}
              >
                {FAMILIES.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-zinc-400">Seed</span>
              <input
                type="number"
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
              />
            </label>
            <div>
              <span className="text-zinc-400">Split strategies</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {(schema?.split_strategies ?? strategies).map((s) => (
                  <button
                    key={s}
                    type="button"
                    className={`rounded px-2 py-1 text-xs ring-1 ${
                      strategies.includes(s)
                        ? 'bg-cyan-950/60 text-cyan-100 ring-cyan-800'
                        : 'text-zinc-500 ring-zinc-700'
                    }`}
                    onClick={() => toggleStrategy(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <span className="text-zinc-400">Hyperparameters</span>
              {Object.entries(modelParams).map(([key, val]) => (
                <label key={key} className="flex items-center gap-2">
                  <span className="w-28 font-mono text-xs text-zinc-500">{key}</span>
                  <input
                    className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs"
                    value={val}
                    onChange={(e) =>
                      setModelParams((prev) => ({ ...prev, [key]: e.target.value }))
                    }
                  />
                </label>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={onPreview}>Preview config</Button>
              <Button type="button" onClick={onStart}>Start run</Button>
            </div>
            {preview && (
              <pre className="max-h-48 overflow-auto rounded bg-zinc-900 p-2 text-xs text-zinc-400">
                {JSON.stringify(preview, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Run registry</CardTitle>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <p className="text-sm text-zinc-500">No workbench runs yet.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {runs.map((run) => (
                  <li
                    key={run.run_id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-800 px-3 py-2"
                  >
                    <div>
                      <span className="font-mono text-zinc-200">{run.run_id}</span>
                      <span className="ml-2 text-zinc-500">{run.family}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={run.status === 'completed' ? 'real' : 'neutral'}>
                        {run.status}
                      </Badge>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => loadMetrics(run.run_id)}
                      >
                        Metrics
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {metrics && selectedRun && (
              <div className="mt-4 rounded border border-zinc-800 p-3 text-xs text-zinc-300">
                <p className="mb-2 font-mono text-zinc-400">{selectedRun} · in_domain test</p>
                <pre className="max-h-40 overflow-auto">{JSON.stringify(metrics.test, null, 2)}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
