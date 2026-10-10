import type { Prediction } from '@/types/prediction'

const DEFAULT_API_BASE = '/api'

export function apiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_URL as string | undefined
  return (fromEnv?.trim() || DEFAULT_API_BASE).replace(/\/$/, '')
}

export function useApiPredictions(): boolean {
  const flag = import.meta.env.VITE_USE_API_PREDICTIONS as string | undefined
  if (flag === 'false' || flag === '0') return false
  return true
}

export async function fetchHealth(): Promise<{ model_loaded: boolean; model_path?: string }> {
  const res = await fetch(`${apiBaseUrl()}/health`)
  if (!res.ok) throw new Error(`API health failed (${res.status})`)
  return (await res.json()) as { model_loaded: boolean; model_path?: string }
}

export async function fetchModelPrediction(
  amplitudePrefix: number[][],
  meta: {
    session_id: string
    environment_id: string
    time_index: number
    frame_count: number
  },
): Promise<Prediction> {
  const res = await fetch(`${apiBaseUrl()}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amplitude: amplitudePrefix,
      session_id: meta.session_id,
      environment_id: meta.environment_id,
      time_index: meta.time_index,
      frame_count: meta.frame_count,
    }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`predict failed (${res.status}): ${detail}`)
  }
  const payload = (await res.json()) as Prediction
  return { ...payload, source: 'model' }
}
