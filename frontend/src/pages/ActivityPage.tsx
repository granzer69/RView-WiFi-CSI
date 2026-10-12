import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { StudioPageChrome } from '@/components/layout/StudioPageChrome'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  evaluateActivitySample,
  fetchActivityTrials,
  type ActivitySampleResult,
  type ActivityTrial,
} from '@/services/activityClient'
import { fetchModels } from '@/services/apiClient'

type EvalState = ActivitySampleResult | { status: 'not-evaluated' }

export function ActivityPage() {
  const [trials, setTrials] = useState<ActivityTrial[]>([])
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [sampleIndex, setSampleIndex] = useState(949)
  const [modelId, setModelId] = useState<string | undefined>()
  const [evalResult, setEvalResult] = useState<EvalState>({ status: 'not-evaluated' })
  const [loading, setLoading] = useState(false)
  const [participantFilter, setParticipantFilter] = useState<number | 'all'>('all')
  const [labelFilter, setLabelFilter] = useState<string | 'all'>('all')

  useEffect(() => {
    fetchActivityTrials()
      .then((payload) => {
        setTrials(payload.trials)
        if (payload.trials.length) setSelectedId(payload.trials[0].session_id)
      })
      .catch((e: Error) => setError(e.message))
    fetchModels()
      .then((m) => setModelId(m.active_model_id ?? undefined))
      .catch(() => undefined)
  }, [])

  const filtered = useMemo(() => {
    return trials.filter((t) => {
      if (participantFilter !== 'all' && t.participant_id !== participantFilter) return false
      if (labelFilter !== 'all' && t.normalized_label !== labelFilter) return false
      return true
    })
  }, [trials, participantFilter, labelFilter])

  const participants = useMemo(
    () => [...new Set(trials.map((t) => t.participant_id))].sort((a, b) => a - b),
    [trials],
  )
  const labels = useMemo(
    () => [...new Set(trials.map((t) => t.normalized_label))].sort(),
    [trials],
  )

  const runEval = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    setError(null)
    try {
      const result = await evaluateActivitySample(selectedId, sampleIndex, modelId)
      setEvalResult(result)
    } catch (e) {
      setEvalResult({
        session_id: selectedId,
        sample_index: sampleIndex,
        sample_count: 950,
        ground_truth_label: '',
        model_id: modelId ?? '',
        status: 'error',
        error: (e as Error).message,
      })
    } finally {
      setLoading(false)
    }
  }, [selectedId, sampleIndex, modelId])

  const exportSummaries = () => {
    const rows = filtered.map((t) => ({
      session_id: t.session_id,
      participant_id: t.participant_id,
      scenario_id: t.scenario_id,
      ground_truth: t.normalized_label,
    }))
    const blob = new Blob([JSON.stringify({ trials: rows }, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'activity-trial-summaries.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const statusBadge = (status: string) => {
    if (status === 'evaluated-correct') return <Badge variant="real">correct</Badge>
    if (status === 'evaluated-incorrect') return <Badge variant="simulated">incorrect</Badge>
    if (status === 'error') return <Badge variant="simulated">error</Badge>
    return <Badge variant="neutral">not evaluated</Badge>
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <StudioPageChrome
        showLabelCaveat
        title="Activity workbench"
        subtitle="Trial-level ground truth vs model prediction at a chosen sample index. Inference runs only when you request it."
      />

      {error && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <label className="text-xs text-zinc-500">
          Participant
          <select
            className="ml-2 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
            value={participantFilter}
            onChange={(e) =>
              setParticipantFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))
            }
          >
            <option value="all">all</option>
            {participants.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>
        <label className="text-xs text-zinc-500">
          Label
          <select
            className="ml-2 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
            value={labelFilter}
            onChange={(e) => setLabelFilter(e.target.value)}
          >
            <option value="all">all</option>
            {labels.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </label>
        <Button type="button" variant="outline" size="sm" onClick={exportSummaries}>
          Export trial list (JSON)
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <Card className="surface-card border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm">Trials ({filtered.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[420px] overflow-y-auto">
            <ul className="space-y-1 text-xs">
              {filtered.map((t) => (
                <li key={t.session_id}>
                  <button
                    type="button"
                    className={`w-full rounded px-2 py-1 text-left ${
                      selectedId === t.session_id ? 'bg-cyan-950 text-cyan-100' : 'hover:bg-zinc-900'
                    }`}
                    onClick={() => {
                      setSelectedId(t.session_id)
                      setEvalResult({ status: 'not-evaluated' })
                    }}
                  >
                    <span className="font-mono">{t.session_id}</span>
                    <span className="ml-2 capitalize text-zinc-500">{t.normalized_label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="surface-card border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm">Sample-index evaluation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap items-end gap-3">
                <label className="text-xs text-zinc-500">
                  Sample index (0–949)
                  <input
                    type="number"
                    min={0}
                    max={949}
                    className="ml-2 w-24 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-sm"
                    value={sampleIndex}
                    onChange={(e) => setSampleIndex(Number(e.target.value))}
                  />
                </label>
                <Button type="button" size="sm" disabled={loading || !selectedId} onClick={() => void runEval()}>
                  {loading ? 'Running…' : 'Run inference at index'}
                </Button>
              </div>
              <input
                type="range"
                min={0}
                max={949}
                value={sampleIndex}
                className="w-full"
                onChange={(e) => setSampleIndex(Number(e.target.value))}
                aria-label="Sample index timeline"
              />
              <p className="text-xs text-zinc-500">
                Timeline axis is sample index within the trial, not seconds or occupancy.
              </p>
            </CardContent>
          </Card>

          <Card className="surface-card border-zinc-800">
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center gap-2 text-sm">
                Result {statusBadge(evalResult.status)}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {evalResult.status === 'not-evaluated' && (
                <p className="text-zinc-500">Select a trial and run inference to compare GT vs prediction.</p>
              )}
              {evalResult.status !== 'not-evaluated' && (
                <>
                  <p>
                    Ground truth:{' '}
                    <span className="capitalize font-medium text-zinc-100">
                      {evalResult.ground_truth_label || '—'}
                    </span>
                  </p>
                  {evalResult.prediction && (
                    <p>
                      Prediction:{' '}
                      <span className="capitalize font-medium text-cyan-100">
                        {evalResult.prediction.activity}
                      </span>
                      {evalResult.prediction.confidence != null && (
                        <span className="ml-2 text-zinc-500">
                          ({(evalResult.prediction.confidence * 100).toFixed(1)}%)
                        </span>
                      )}
                    </p>
                  )}
                  {evalResult.status === 'evaluated-incorrect' && (
                    <Link
                      className="text-xs text-cyan-400 hover:underline"
                      to={`/explorer?session=${encodeURIComponent(evalResult.session_id)}`}
                    >
                      Open misclassified trial in CSI Explorer →
                    </Link>
                  )}
                  {evalResult.status === 'error' && (
                    <p className="text-rose-300">{evalResult.error}</p>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
