export type ReplaySourceKind = 'dataset_replay' | 'esp32_stream'

export type SessionMeta = {
  session_id: string
  environment_id: string
  scenario_id: number
  scenario_name?: string
  participant_id: number
  trial_id: number
  activity_code: number
  normalized_label: string
  dataset_label: string
  label_verified_by_folder: boolean
  data_tier: 'real'
  dataset_id?: string
  dataset_version?: string
}

export type SessionManifestEntry = Pick<
  SessionMeta,
  | 'session_id'
  | 'scenario_id'
  | 'participant_id'
  | 'activity_code'
  | 'normalized_label'
  | 'dataset_label'
  | 'label_verified_by_folder'
> & {
  scenario_name: string
  environment_id: string
}

export type ReplayManifest = {
  dataset_id: string
  source: ReplaySourceKind
  nominal_replay_hz: number
  timing_note: string
  session_count: number
  sessions: SessionManifestEntry[]
  default_session_id: string
}

export type TransportState = 'idle' | 'playing' | 'paused' | 'stopped' | 'complete'

export type ReplaySpeed = 0.25 | 0.5 | 1 | 2 | 4

export const REPLAY_SPEEDS: ReplaySpeed[] = [0.25, 0.5, 1, 2, 4]

export const DEFAULT_NOMINAL_REPLAY_HZ = 95

export type ReplayEvent =
  | { type: 'session_started'; session_id: string; source: ReplaySourceKind }
  | {
      type: 'csi_frame'
      time_index: number
      subcarriers: number[]
      meta: SessionMeta
    }
  | { type: 'prediction'; payload: import('./prediction').Prediction }
  | { type: 'session_ended'; reason: 'stop' | 'complete' }
  | { type: 'error'; message: string }
