import { useEffect, useMemo, useState } from 'react'

import { LabelInferenceCaveat } from '@/components/layout/LabelInferenceCaveat'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const DEEP_DEFAULT_CONFIG_FAMILIES = new Set(['cnn1d', 'gru', 'tcn'])

type PerClassStats = Record<
  string,
  { precision?: number; recall?: number; f1?: number; support?: number }
>

type GeneralizationModel = {
  model_id: string
  family: string
  split_strategy: string
  macro_f1?: number
  generalization_gap?: number | null
  in_domain_macro_f1?: number
  confused_pairs?: { true_label: string; predicted_label: string; count: number }[]
  per_class?: PerClassStats
  assignment_sha256?: string
}

type GeneralizationPayload = {
  generated_at?: string
  git_sha?: string
  status?: string
  integrity_note?: string
  provenance?: { source?: string; note?: string }
  baseline_run_ids?: Record<string, string>
  models: GeneralizationModel[]
}

type ParticipantRow = {
  user_id: number
  session_counts: Record<string, number>
  scenario_ids: number[]
}

type ParticipantsPayload = {
  status: string
  reason?: string
  overview?: { status: string; participants: ParticipantRow[] }
  model_metrics?: {
    status: string
    models: {
      family: string
      split_strategy: string
      participants: { user_id: number; macro_f1?: number; test_session_count: number }[]
    }[]
  }
  methodology?: string
}

type PersonalizationParticipant = {
  user_id: number
  status: string
  calibration_session_count?: number
  evaluation_session_count?: number
  general?: { macro_f1: number; accuracy: number }
  personalized?: { macro_f1: number; accuracy: number }
  macro_f1_delta?: number
  adaptation_method?: string
}

type PersonalizationExperiment = {
  family: string
  run_id: string
  split_strategy: string
  aggregate?: {
    mean_macro_f1_general?: number | null
    mean_macro_f1_personalized?: number | null
    mean_macro_f1_delta?: number | null
    participants_evaluated?: number
  }
  participants: PersonalizationParticipant[]
}

type PersonalizationPayload = {
  status: string
  protocol?: string
  limitations?: string
  cross_user_personalization?: string
  in_domain_personalization?: string
  experiments?: PersonalizationExperiment[]
}

const STRATEGIES = ['in_domain', 'cross_user', 'cross_environment'] as const

function GapTable({ models }: { models: GeneralizationModel[] }) {
  const families = useMemo(
    () => [...new Set(models.map((m) => m.family))].sort(),
    [models],
  )
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs">
        <thead>
          <tr className="text-zinc-500">
            <th className="p-2 text-left">Family</th>
            {STRATEGIES.map((s) => (
              <th key={s} className="p-2 text-right capitalize">{s.replace(/_/g, ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {families.map((family) => (
            <tr key={family} className="border-t border-zinc-800">
              <td className="p-2 font-medium text-zinc-200">{family}</td>
              {STRATEGIES.map((strategy) => {
                const row = models.find(
                  (m) => m.family === family && m.split_strategy === strategy,
                )
                const gap = row?.generalization_gap
                const f1 = row?.macro_f1
                return (
                  <td key={strategy} className="p-2 text-right text-zinc-300">
                    {f1 != null ? f1.toFixed(3) : '—'}
                    {gap != null && strategy !== 'in_domain' && (
                      <span className="ml-1 text-zinc-500">(Δ {gap.toFixed(3)})</span>
                    )}
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

export function ResearchLabPage() {
  const [generalization, setGeneralization] = useState<GeneralizationPayload | null>(null)
  const [participants, setParticipants] = useState<ParticipantsPayload | null>(null)
  const [personalization, setPersonalization] = useState<PersonalizationPayload | null>(null)
  const [profilingFamily, setProfilingFamily] = useState<string>('logreg')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/research/generalization.json').then(async (res) => {
        if (!res.ok) throw new Error('Run scripts/export_research_lab.py')
        return (await res.json()) as GeneralizationPayload
      }),
      fetch('/research/participants.json').then(async (res) => {
        if (!res.ok) return null
        return (await res.json()) as ParticipantsPayload
      }),
      fetch('/research/personalization.json').then(async (res) => {
        if (!res.ok) return null
        return (await res.json()) as PersonalizationPayload
      }),
    ])
      .then(([gen, part, pers]) => {
        setGeneralization(gen)
        setParticipants(part)
        setPersonalization(pers)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  const sampleGaps = useMemo(() => {
    if (!generalization?.models?.length) return []
    return generalization.models
      .filter((m) => m.split_strategy !== 'in_domain' && m.generalization_gap != null)
      .slice(0, 4)
  }, [generalization])

  const profilingFamilies = useMemo(() => {
    const fromExport = participants?.model_metrics?.models?.map((m) => m.family) ?? []
    const unique = [...new Set(fromExport)].sort()
    return unique.length > 0 ? unique : ['logreg', 'rf', 'cnn1d', 'gru', 'mlp', 'gbdt', 'tcn']
  }, [participants])

  const profilingModel = useMemo(() => {
    const models = participants?.model_metrics?.models ?? []
    return (
      models.find((m) => m.family === profilingFamily) ??
      models.find((m) => m.family === profilingFamilies[0]) ??
      null
    )
  }, [participants, profilingFamily, profilingFamilies])

  useEffect(() => {
    if (profilingFamilies.length && !profilingFamilies.includes(profilingFamily)) {
      setProfilingFamily(profilingFamilies[0])
    }
  }, [profilingFamilies, profilingFamily])

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <header className="border-b border-zinc-800 pb-4">
        <h1 className="text-xl font-semibold text-zinc-50">Research Lab</h1>
        <p className="text-sm text-zinc-400">
          Generalization gaps, participant test metrics, and experiment provenance
        </p>
      </header>

      {error && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          {error}
        </div>
      )}

      {!generalization && !error && (
        <div className="space-y-2">
          <div className="skeleton-pulse h-8 w-48" />
          <div className="skeleton-pulse h-40 w-full" />
        </div>
      )}

      {generalization && (
        <>
          <LabelInferenceCaveat compact className="mb-2" />
        <Tabs defaultValue="generalization" className="w-full">
          <TabsList className="grid w-full grid-cols-2 gap-1 md:grid-cols-4">
            <TabsTrigger value="generalization">Generalization</TabsTrigger>
            <TabsTrigger value="profiling">User Profiling</TabsTrigger>
            <TabsTrigger value="personalization">Personalization</TabsTrigger>
            <TabsTrigger value="experiments">Experiment Details</TabsTrigger>
          </TabsList>

          <TabsContent value="generalization" className="mt-4 space-y-4">
            {generalization.integrity_note && (
              <div className="rounded-md border border-cyan-900/40 bg-cyan-950/20 px-3 py-2 text-xs text-cyan-100/90">
                {generalization.integrity_note}
              </div>
            )}
            <Card className="surface-card border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm flex flex-wrap items-center gap-2">
                  Macro-F1 and generalization gap (Δ vs in-domain)
                  <Badge variant="neutral" className="text-[10px] font-normal">
                    cnn1d / gru / tcn: default-config baseline (not hyperparameter-tuned)
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <GapTable models={generalization.models} />
              </CardContent>
            </Card>
            {sampleGaps.length > 0 && (
              <Card className="surface-card border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm">Top confused pairs (selected models)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs text-zinc-400">
                  {sampleGaps.map((model) => (
                    <div key={model.model_id}>
                      <p className="mb-1 font-medium text-zinc-200">
                        {model.family} · {model.split_strategy.replace(/_/g, ' ')}
                        {DEEP_DEFAULT_CONFIG_FAMILIES.has(model.family) && (
                          <Badge variant="neutral" className="ml-2 text-[10px]">
                            default-config baseline
                          </Badge>
                        )}
                      </p>
                      <ul className="list-disc pl-4">
                        {(model.confused_pairs ?? []).slice(0, 3).map((pair) => (
                          <li key={`${pair.true_label}-${pair.predicted_label}`}>
                            {pair.true_label} → {pair.predicted_label}: {pair.count}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="profiling" className="mt-4 space-y-4">
            {participants?.status === 'blocked' && (
              <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
                {participants.reason ?? 'Participant export blocked — ESP-Fi data missing.'}
              </div>
            )}
            {participants?.overview?.participants && (
              <Card className="surface-card border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm">Participants (session counts)</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="text-zinc-500">
                        <th className="p-2 text-left">User</th>
                        <th className="p-2 text-right">Train</th>
                        <th className="p-2 text-right">Val</th>
                        <th className="p-2 text-right">Test</th>
                      </tr>
                    </thead>
                    <tbody>
                      {participants.overview.participants.map((p) => (
                        <tr key={p.user_id} className="border-t border-zinc-800">
                          <td className="p-2 text-zinc-200">{p.user_id}</td>
                          <td className="p-2 text-right">{p.session_counts.train}</td>
                          <td className="p-2 text-right">{p.session_counts.val}</td>
                          <td className="p-2 text-right">{p.session_counts.test}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
            {profilingModel && (
              <Card className="surface-card border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm flex flex-wrap items-center gap-2">
                    Per-participant test macro-F1
                    <div className="flex flex-wrap gap-1">
                      {profilingFamilies.map((family) => (
                        <button
                          key={family}
                          type="button"
                          onClick={() => setProfilingFamily(family)}
                          className={`rounded-full px-2 py-0.5 text-[10px] ${
                            profilingFamily === family
                              ? 'bg-cyan-900 text-cyan-100'
                              : 'bg-zinc-800 text-zinc-400'
                          }`}
                        >
                          {family}
                        </button>
                      ))}
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-2 sm:grid-cols-4">
                  {profilingModel.participants.map((p) => (
                    <div key={p.user_id} className="rounded border border-zinc-800 p-2">
                      <p className="text-[10px] uppercase text-zinc-500">User {p.user_id}</p>
                      <p className="text-lg font-semibold">{p.macro_f1?.toFixed(3) ?? '—'}</p>
                      <p className="text-[10px] text-zinc-500">{p.test_session_count} test sessions</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="personalization" className="mt-4 space-y-4">
            <div
              role="alert"
              className="rounded-lg border border-rose-900/60 bg-rose-950/30 px-4 py-3 text-sm text-rose-100/95"
            >
              <p className="font-semibold text-rose-50">Not unseen-user personalization</p>
              <p className="mt-1 text-rose-100/90">
                The global baseline models were trained on the full in-domain train split, including each
                participant&apos;s sessions used later for calibration. Reported gains are in-domain A/B
                comparisons — not leave-one-user-out or deployment to users absent from training.
              </p>
            </div>
            <Card className="surface-card border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  In-domain personalization A/B
                  <Badge variant="neutral">{personalization?.status ?? 'unknown'}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-zinc-400">
                <p>{personalization?.protocol}</p>
                <p>{personalization?.limitations}</p>
                <p>
                  cross_user: {personalization?.cross_user_personalization} · in_domain:{' '}
                  {personalization?.in_domain_personalization}
                </p>
              </CardContent>
            </Card>
            {personalization?.experiments?.map((exp) => (
              <Card key={exp.family} className="surface-card border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    {exp.family}
                    <Badge variant="model">{exp.split_strategy}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {exp.aggregate && (
                    <p className="text-xs text-zinc-400">
                      Mean macro-F1 general {exp.aggregate.mean_macro_f1_general?.toFixed(3) ?? '—'} →
                      personalized {exp.aggregate.mean_macro_f1_personalized?.toFixed(3) ?? '—'} (Δ{' '}
                      {exp.aggregate.mean_macro_f1_delta?.toFixed(3) ?? '—'}) ·{' '}
                      {exp.aggregate.participants_evaluated} participants
                    </p>
                  )}
                  <div className="grid gap-2 sm:grid-cols-4">
                    {exp.participants
                      .filter((p) => p.status === 'ok')
                      .map((p) => (
                        <div key={p.user_id} className="rounded border border-zinc-800 p-2 text-xs">
                          <p className="text-[10px] uppercase text-zinc-500">Participant {p.user_id}</p>
                          <p className="text-zinc-300">
                            G {p.general?.macro_f1?.toFixed(3)} / P {p.personalized?.macro_f1?.toFixed(3)}
                          </p>
                          <p className="text-signal-cyan">Δ {p.macro_f1_delta?.toFixed(3)}</p>
                          <p className="text-[10px] text-zinc-600">
                            cal {p.calibration_session_count} · eval {p.evaluation_session_count}
                          </p>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="experiments" className="mt-4 space-y-4">
            <Card className="surface-card border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm">Provenance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-zinc-400">
                <p>Generated: {generalization.generated_at ?? '—'}</p>
                <p>Git SHA: {generalization.git_sha ?? '—'}</p>
                <p>{generalization.provenance?.source}</p>
                <p>{generalization.provenance?.note}</p>
                {generalization.baseline_run_ids && (
                  <ul className="list-disc pl-4">
                    {Object.entries(generalization.baseline_run_ids).map(([family, runId]) => (
                      <li key={family}>{family}: {runId}</li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        </>
      )}
    </div>
  )
}
