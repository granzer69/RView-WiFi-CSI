import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { StudioPageChrome } from '@/components/layout/StudioPageChrome'
import { ExplorerHeatmap } from '@/components/csi/ExplorerHeatmap'
import { SubcarrierWaveform } from '@/components/csi/SubcarrierWaveform'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  fetchCompare,
  fetchExplorerCatalog,
  fetchSubcarrierTrace,
  fetchTrialAmplitude,
  fetchTrialDetail,
  fetchTrialPrediction,
  type ExplorerCatalog,
  type ExplorerTrial,
} from '@/services/explorerClient'
import { fetchModels } from '@/services/apiClient'

export function ExplorerPage() {
  const [searchParams] = useSearchParams()
  const [catalog, setCatalog] = useState<ExplorerCatalog | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [primaryId, setPrimaryId] = useState<string>('')
  const [compareId, setCompareId] = useState<string>('')
  const [compareMode, setCompareMode] = useState(false)
  const [ampA, setAmpA] = useState<number[][]>([])
  const [ampB, setAmpB] = useState<number[][]>([])
  const [subcarrier, setSubcarrier] = useState(26)
  const [trace, setTrace] = useState<number[]>([])
  const [stats, setStats] = useState<Record<string, unknown> | null>(null)
  const [prediction, setPrediction] = useState<Record<string, unknown> | null>(null)
  const [sharedScale, setSharedScale] = useState<{ min: number; max: number } | null>(null)
  const [modelId, setModelId] = useState<string | undefined>()

  useEffect(() => {
    fetchExplorerCatalog()
      .then((c) => {
        setCatalog(c)
        const fromQuery = searchParams.get('session')
        if (fromQuery && c.trials.some((t) => t.session_id === fromQuery)) {
          setPrimaryId(fromQuery)
        } else if (c.trials.length) setPrimaryId(c.trials[0].session_id)
      })
      .catch((e: Error) => setError(e.message))
    fetchModels()
      .then((m) => setModelId(m.active_model_id ?? undefined))
      .catch(() => undefined)
  }, [searchParams])

  const trials = catalog?.trials ?? []

  const filters = useMemo(() => {
    const participants = [...new Set(trials.map((t) => t.participant_id))].sort()
    const scenarios = [...new Set(trials.map((t) => t.scenario_id))].sort()
    const labels = [...new Set(trials.map((t) => t.normalized_label))].sort()
    return { participants, scenarios, labels }
  }, [trials])

  const [participantFilter, setParticipantFilter] = useState<number | 'all'>('all')
  const [scenarioFilter, setScenarioFilter] = useState<number | 'all'>('all')
  const [labelFilter, setLabelFilter] = useState<string | 'all'>('all')

  const filteredTrials = trials.filter((t) => {
    if (participantFilter !== 'all' && t.participant_id !== participantFilter) return false
    if (scenarioFilter !== 'all' && t.scenario_id !== scenarioFilter) return false
    if (labelFilter !== 'all' && t.normalized_label !== labelFilter) return false
    return true
  })

  useEffect(() => {
    if (!primaryId) return
    setError(null)
    fetchTrialAmplitude(primaryId)
      .then(setAmpA)
      .catch((e: Error) => setError(e.message))
    fetchTrialDetail(primaryId)
      .then((d) => setStats(d.statistics as Record<string, unknown>))
      .catch(() => setStats(null))
    fetchSubcarrierTrace(primaryId, subcarrier)
      .then((t) => setTrace(t.values))
      .catch(() => setTrace([]))
    if (modelId) {
      fetchTrialPrediction(primaryId, modelId)
        .then(setPrediction)
        .catch(() => setPrediction(null))
    }
  }, [primaryId, subcarrier, modelId])

  useEffect(() => {
    if (!compareMode || !compareId) {
      setAmpB([])
      setSharedScale(null)
      return
    }
    fetchTrialAmplitude(compareId)
      .then(setAmpB)
      .catch((e: Error) => setError(e.message))
    fetchCompare(primaryId, compareId)
      .then((c) => setSharedScale(c.compatible_scales))
      .catch(() => setSharedScale(null))
  }, [compareMode, compareId, primaryId])

  function trialLabel(t: ExplorerTrial) {
    const tag = t.label_status === 'verified' ? 'verified' : 'inferred'
    return `${t.session_id} · P${t.participant_id} · ${t.scenario_name} · ${t.normalized_label} (${tag})`
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6">
      <StudioPageChrome
        showLabelCaveat
        title="CSI explorer"
        subtitle="Inspect ESP-Fi amplitude matrices (950×52), subcarrier traces, and trial-level model alignment. Matrix row index is not wall-clock time unless independently verified."
      />
      {catalog?.label_caveat && (
        <p className="text-xs text-amber-200/80">{catalog.label_caveat}</p>
      )}

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="py-4 text-sm text-red-200">{error}</CardContent>
        </Card>
      )}

      {!catalog && !error && <p className="text-sm text-zinc-500">Loading catalog…</p>}

      {catalog && catalog.trial_count === 0 && (
        <Card>
          <CardContent className="py-6 text-sm text-zinc-400">
            ESP-Fi data not found on the API host. Set RVIEW_DATA_ROOT and export trials locally.
          </CardContent>
        </Card>
      )}

      {filteredTrials.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recording selector</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-4">
              <select
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm"
                value={participantFilter}
                onChange={(e) =>
                  setParticipantFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))
                }
              >
                <option value="all">All participants</option>
                {filters.participants.map((p) => (
                  <option key={p} value={p}>P{p}</option>
                ))}
              </select>
              <select
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm"
                value={scenarioFilter}
                onChange={(e) =>
                  setScenarioFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))
                }
              >
                <option value="all">All scenarios</option>
                {filters.scenarios.map((s) => (
                  <option key={s} value={s}>Scenario {s}</option>
                ))}
              </select>
              <select
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm"
                value={labelFilter}
                onChange={(e) => setLabelFilter(e.target.value)}
              >
                <option value="all">All activities</option>
                {filters.labels.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm text-zinc-300">
                <input
                  type="checkbox"
                  checked={compareMode}
                  onChange={(e) => setCompareMode(e.target.checked)}
                />
                Compare two recordings
              </label>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block text-sm">
              <span className="text-zinc-400">Primary trial</span>
              <select
                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2"
                value={primaryId}
                onChange={(e) => setPrimaryId(e.target.value)}
              >
                {filteredTrials.map((t) => (
                  <option key={t.session_id} value={t.session_id}>{trialLabel(t)}</option>
                ))}
              </select>
            </label>
            {compareMode && (
              <label className="block text-sm">
                <span className="text-zinc-400">Compare trial</span>
                <select
                  className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2"
                  value={compareId}
                  onChange={(e) => setCompareId(e.target.value)}
                >
                  <option value="">Select…</option>
                  {filteredTrials
                    .filter((t) => t.session_id !== primaryId)
                    .map((t) => (
                      <option key={t.session_id} value={t.session_id}>{trialLabel(t)}</option>
                    ))}
                </select>
              </label>
            )}
          </div>

          <div className={compareMode && ampB.length ? 'grid gap-4 lg:grid-cols-2' : ''}>
            <ExplorerHeatmap
              amplitude={ampA}
              sharedMin={sharedScale?.min}
              sharedMax={sharedScale?.max}
              title="Primary"
            />
            {compareMode && ampB.length > 0 && (
              <ExplorerHeatmap
                amplitude={ampB}
                sharedMin={sharedScale?.min}
                sharedMax={sharedScale?.max}
                title="Compare"
              />
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Subcarrier waveform (raw amplitude)</CardTitle>
              </CardHeader>
              <CardContent>
                <label className="mb-2 flex items-center gap-2 text-xs text-zinc-400">
                  Subcarrier index
                  <input
                    type="number"
                    min={0}
                    max={51}
                    value={subcarrier}
                    className="w-16 rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
                    onChange={(e) => setSubcarrier(Number(e.target.value))}
                  />
                </label>
                <SubcarrierWaveform values={trace} subcarrierIndex={subcarrier} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Signal statistics</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-zinc-300">
                {stats?.empty ? (
                  <p className="text-zinc-500">Empty or non-finite matrix.</p>
                ) : stats ? (
                  <ul className="space-y-1 font-mono text-xs">
                    <li>mean: {Number(stats.mean).toFixed(4)}</li>
                    <li>std: {Number(stats.std).toFixed(4)}</li>
                    <li>min / max: {Number(stats.min).toFixed(4)} / {Number(stats.max).toFixed(4)}</li>
                    <li>finite fraction: {Number(stats.finite_fraction).toFixed(4)}</li>
                    {stats.constant ? (
                      <li className="text-amber-300">constant signal (std = 0)</li>
                    ) : null}
                  </ul>
                ) : (
                  <p className="text-zinc-500">Statistics unavailable.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {prediction && (
            <Card className="border-signal/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  Trial-level prediction
                  <Badge variant="model">MODEL</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-zinc-300">
                <p>
                  Ground truth:{' '}
                  <span className="capitalize text-zinc-100">
                    {String(prediction.ground_truth_label)}
                  </span>
                  {prediction.label_verified_by_folder === false && (
                    <span className="ml-2 text-xs text-amber-300">(inferred label)</span>
                  )}
                </p>
                <p className="mt-2">
                  Predicted:{' '}
                  <span className="capitalize text-cyan-200">
                    {String((prediction.prediction as { activity?: string })?.activity)}
                  </span>
                  {' · '}
                  confidence{' '}
                  {Number((prediction.prediction as { confidence?: number })?.confidence).toFixed(3)}
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
