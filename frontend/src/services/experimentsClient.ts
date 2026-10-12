import { apiBaseUrl } from '@/services/apiClient'

export type ExperimentSchema = {
  families: string[]
  split_strategies: string[]
  hyperparameters: Record<string, Record<string, unknown>>
  preprocess: Record<string, unknown>
  defaults: Record<string, unknown>
}

export type ExperimentRun = {
  run_id: string
  family: string
  status: string
  created_at?: string
  artifacts_dir?: string
  error?: string
  manifest_summary?: Record<string, number>
}

export async function fetchExperimentSchema(): Promise<ExperimentSchema> {
  const res = await fetch(`${apiBaseUrl()}/experiments/schema`)
  if (!res.ok) throw new Error(`schema failed (${res.status})`)
  return (await res.json()) as ExperimentSchema
}

export async function fetchExperimentRuns(): Promise<ExperimentRun[]> {
  const res = await fetch(`${apiBaseUrl()}/experiments/runs`)
  if (!res.ok) throw new Error(`runs list failed (${res.status})`)
  const body = (await res.json()) as { runs: ExperimentRun[] }
  return body.runs
}

export async function previewExperimentRun(payload: Record<string, unknown>) {
  const res = await fetch(`${apiBaseUrl()}/experiments/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, preview_only: true }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`preview failed (${res.status}): ${detail}`)
  }
  return await res.json()
}

export async function startExperimentRun(payload: Record<string, unknown>) {
  const res = await fetch(`${apiBaseUrl()}/experiments/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, preview_only: false }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`start run failed (${res.status}): ${detail}`)
  }
  return await res.json()
}

export async function fetchRunMetrics(runId: string, strategy = 'in_domain') {
  const res = await fetch(
    `${apiBaseUrl()}/experiments/runs/${runId}/metrics?strategy=${encodeURIComponent(strategy)}`,
  )
  if (!res.ok) throw new Error(`metrics failed (${res.status})`)
  return await res.json()
}
