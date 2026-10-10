import type { SessionMeta } from './session'

export type CsiStreamFrame = {
  time_index: number
  subcarriers: number[]
  meta: SessionMeta
}

export type TrialReplayPayload = {
  session_id: string
  meta: SessionMeta
  time_steps: number
  subcarriers: number
  amplitude: number[][] 
  data_tier: 'real'
}

export const TIME_STEPS = 950
export const SUBCARRIERS = 52
