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

export function useWebSocketReplay(): boolean {
  const flag = import.meta.env.VITE_USE_WS_REPLAY as string | undefined
  if (flag === 'false' || flag === '0') return false
  return true
}

export type ApiModelInfo = {
  model_id: string
  model_type: string
  family: string
  split_strategy: string
  run_id: string
  artifact_dir: string
  label_names: string[]
  metrics?: Record<string, unknown>
  load_error?: string
}

export async function fetchHealth(): Promise<{
  model_loaded: boolean
  model_path?: string
  active_model_id?: string
  model_load_error?: string
}> {
  const res = await fetch(`${apiBaseUrl()}/health`)
  if (!res.ok) throw new Error(`API health failed (${res.status})`)
  return (await res.json()) as {
    model_loaded: boolean
    model_path?: string
    active_model_id?: string
    model_load_error?: string
  }
}

export async function fetchModels(): Promise<{ active_model_id: string | null; models: ApiModelInfo[] }> {
  const res = await fetch(`${apiBaseUrl()}/models`)
  if (!res.ok) throw new Error(`models failed (${res.status})`)
  return (await res.json()) as { active_model_id: string | null; models: ApiModelInfo[] }
}

export async function selectActiveModel(modelId: string): Promise<void> {
  const res = await fetch(`${apiBaseUrl()}/models/active`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`select model failed (${res.status}): ${detail}`)
  }
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
