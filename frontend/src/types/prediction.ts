export type NormalizedActivity =
  | 'running'
  | 'walking'
  | 'jumping'
  | 'squatting'
  | 'arm_wave'
  | 'turning'
  | 'falling'

export type PredictionSource = 'model' | 'dataset_replay'

export type SimulatedSpatial = {
  x: number
  y: number
  simulated: true
}

export type Prediction = {
  activity: NormalizedActivity | string
  confidence: number
  timestamp: string
  session_id: string
  environment_id: string
  latency_ms: number
  source: PredictionSource
  presence?: boolean
  probabilities?: Record<string, number>
  model_version?: string
  spatial?: SimulatedSpatial
}
