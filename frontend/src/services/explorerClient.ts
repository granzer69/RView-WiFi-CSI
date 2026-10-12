import { apiBaseUrl } from '@/services/apiClient'

export type ExplorerTrial = {
  session_id: string
  scenario_id: number
  scenario_name: string
  participant_id: number
  activity_code: number
  dataset_label: string
  normalized_label: string
  trial_id: number
  label_verified_by_folder: boolean
  label_status: 'verified' | 'inferred'
}

export type ExplorerCatalog = {
  dataset_id: string
  trial_count: number
  shape: { time_steps: number; subcarriers: number }
  orientation_note: string
  label_caveat: string
  trials: ExplorerTrial[]
}

export async function fetchExplorerCatalog(): Promise<ExplorerCatalog> {
  const res = await fetch(`${apiBaseUrl()}/explorer/catalog`)
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`explorer catalog failed (${res.status}): ${detail}`)
  }
  return (await res.json()) as ExplorerCatalog
}

export async function fetchTrialAmplitude(sessionId: string): Promise<number[][]> {
  const res = await fetch(`${apiBaseUrl()}/explorer/trials/${sessionId}/amplitude`)
  if (!res.ok) throw new Error(`amplitude failed (${res.status})`)
  const body = (await res.json()) as { amplitude: number[][] }
  return body.amplitude
}

export async function fetchSubcarrierTrace(
  sessionId: string,
  subcarrierIndex: number,
): Promise<{ values: number[]; ground_truth_label: string }> {
  const res = await fetch(
    `${apiBaseUrl()}/explorer/trials/${sessionId}/subcarrier/${subcarrierIndex}`,
  )
  if (!res.ok) throw new Error(`subcarrier trace failed (${res.status})`)
  return (await res.json()) as { values: number[]; ground_truth_label: string }
}

export async function fetchTrialDetail(sessionId: string) {
  const res = await fetch(`${apiBaseUrl()}/explorer/trials/${sessionId}`)
  if (!res.ok) throw new Error(`trial detail failed (${res.status})`)
  return await res.json()
}

export async function fetchTrialPrediction(sessionId: string, modelId?: string) {
  const q = modelId ? `?model_id=${encodeURIComponent(modelId)}` : ''
  const res = await fetch(`${apiBaseUrl()}/explorer/trials/${sessionId}/prediction${q}`)
  if (!res.ok) throw new Error(`trial prediction failed (${res.status})`)
  return await res.json()
}

export async function fetchCompare(sessionA: string, sessionB: string) {
  const res = await fetch(
    `${apiBaseUrl()}/explorer/compare?session_a=${encodeURIComponent(sessionA)}&session_b=${encodeURIComponent(sessionB)}`,
  )
  if (!res.ok) throw new Error(`compare failed (${res.status})`)
  return await res.json()
}
