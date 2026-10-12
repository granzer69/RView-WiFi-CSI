import { apiBaseUrl } from '@/services/apiClient'

export type ActivityTrial = {
  session_id: string
  participant_id: number
  scenario_id: number
  normalized_label: string
  label_verified_by_folder: boolean
}

export type ActivityTrialsResponse = {
  dataset_id: string
  trial_count: number
  trials: ActivityTrial[]
}

export type ActivitySampleResult = {
  session_id: string
  sample_index: number
  sample_count: number
  ground_truth_label: string
  model_id: string
  status: 'evaluated-correct' | 'evaluated-incorrect' | 'not-evaluated' | 'error'
  error?: string
  prediction?: {
    activity: string
    confidence: number
    probabilities?: Record<string, number>
  }
}

export async function fetchActivityTrials(): Promise<ActivityTrialsResponse> {
  const res = await fetch(`${apiBaseUrl()}/activity/trials`)
  if (!res.ok) throw new Error(`activity trials: ${res.status}`)
  return (await res.json()) as ActivityTrialsResponse
}

export async function evaluateActivitySample(
  sessionId: string,
  sampleIndex: number,
  modelId?: string,
): Promise<ActivitySampleResult> {
  const res = await fetch(`${apiBaseUrl()}/activity/sample`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      sample_index: sampleIndex,
      model_id: modelId,
    }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `activity sample: ${res.status}`)
  }
  return (await res.json()) as ActivitySampleResult
}
