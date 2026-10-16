import { apiBaseUrl } from '@/services/apiClient'

export type SourceStatus = {
  mode: 'dataset_replay' | 'live_unavailable'
  reason: string
  dataset_id?: string | null
  live_implemented: boolean
}

export async function fetchSourceStatus(): Promise<SourceStatus> {
  const res = await fetch(`${apiBaseUrl()}/source/status`)
  if (!res.ok) {
    throw new Error(`source status failed: ${res.status}`)
  }
  return (await res.json()) as SourceStatus
}
