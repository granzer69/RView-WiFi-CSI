import type { TrialReplayPayload } from '@/types/csi'
import type { Prediction } from '@/types/prediction'
import type {
  ReplayEvent,
  ReplayManifest,
  ReplaySpeed,
  SessionMeta,
  TransportState,
} from '@/types/session'
import { DEFAULT_NOMINAL_REPLAY_HZ } from '@/types/session'

export type LocalReplayListener = (event: ReplayEvent) => void

function spatialAt(progress: number, label: string): Prediction['spatial'] {
  const t = progress
  let x = 0.5
  let y = 0.5
  switch (label) {
    case 'walking':
    case 'running':
      x = 0.2 + 0.6 * Math.abs(Math.sin(t * Math.PI * 2))
      y = 0.5
      break
    case 'falling':
      x = 0.5
      y = 0.5 - 0.35 * Math.min(1, t * 4)
      break
    case 'jumping':
      y = 0.5 - 0.25 * Math.abs(Math.sin(t * Math.PI * 4))
      x = 0.5
      break
    default:
      x = 0.5 + 0.15 * Math.sin(t * Math.PI)
      y = 0.5 + 0.1 * Math.cos(t * Math.PI)
  }
  return { x, y, simulated: true }
}

/** Stub model output for UI wiring only — not trained inference (V2). */
export function buildStubPrediction(
  meta: SessionMeta,
  timeIndex: number,
  frameCount: number,
): Prediction {
  const progress = frameCount > 1 ? timeIndex / (frameCount - 1) : 0
  const activities = [
    'running',
    'walking',
    'jumping',
    'squatting',
    'arm_wave',
    'turning',
    'falling',
  ] as const
  const stubIdx = (timeIndex + meta.activity_code) % activities.length
  const stubActivity = activities[stubIdx]
  return {
    activity: stubActivity,
    confidence: 0.55 + 0.1 * Math.sin(timeIndex / 20),
    timestamp: new Date().toISOString(),
    session_id: meta.session_id,
    environment_id: meta.environment_id,
    latency_ms: 8,
    source: 'model',
    presence: true,
    model_version: 'stub_v1_no_training',
    probabilities: { [stubActivity]: 0.6 },
    spatial: spatialAt(progress, meta.normalized_label),
  }
}

export function buildGroundTruthEcho(meta: SessionMeta, timeIndex: number, frameCount: number): Prediction {
  const progress = frameCount > 1 ? timeIndex / (frameCount - 1) : 0
  return {
    activity: meta.normalized_label,
    confidence: 1,
    timestamp: new Date().toISOString(),
    session_id: meta.session_id,
    environment_id: meta.environment_id,
    latency_ms: 0,
    source: 'dataset_replay',
    spatial: spatialAt(progress, meta.normalized_label),
  }
}

export class LocalReplayTransport {
  private listeners = new Set<LocalReplayListener>()
  private manifest: ReplayManifest | null = null
  private trial: TrialReplayPayload | null = null
  private timeIndex = 0
  private timer: ReturnType<typeof setInterval> | null = null
  private speed: ReplaySpeed = 1
  private state: TransportState = 'idle'

  subscribe(listener: LocalReplayListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(event: ReplayEvent) {
    for (const listener of this.listeners) {
      listener(event)
    }
  }

  async loadManifest(): Promise<ReplayManifest> {
    const res = await fetch('/replay/manifest.json')
    if (!res.ok) throw new Error('ESP-Fi replay manifest not found')
    this.manifest = (await res.json()) as ReplayManifest
    return this.manifest
  }

  getManifest(): ReplayManifest | null {
    return this.manifest
  }

  getState(): TransportState {
    return this.state
  }

  getTimeIndex(): number {
    return this.timeIndex
  }

  getTrial(): TrialReplayPayload | null {
    return this.trial
  }

  async openSession(sessionId: string): Promise<void> {
    this.stopTimer()
    this.timeIndex = 0
    const res = await fetch(`/replay/trials/${sessionId}.json`)
    if (!res.ok) {
      this.trial = null
      this.state = 'idle'
      this.emit({
        type: 'error',
        message:
          `Trial amplitude not exported for ${sessionId}. Run scripts/export_replay_manifest.py --export-trials ${sessionId}`,
      })
      return
    }
    this.trial = (await res.json()) as TrialReplayPayload
    this.state = 'paused'
    this.emit({ type: 'session_started', session_id: sessionId, source: 'dataset_replay' })
    this.emitFrame()
  }

  setSpeed(speed: ReplaySpeed) {
    this.speed = speed
    if (this.state === 'playing') {
      this.startTimer()
    }
  }

  control(action: 'play' | 'pause' | 'stop' | 'restart') {
    if (!this.trial && action !== 'stop') return
    switch (action) {
      case 'play':
        if (!this.trial) return
        if (this.timeIndex >= this.trial.time_steps) {
          this.timeIndex = 0
        }
        this.state = 'playing'
        this.startTimer()
        break
      case 'pause':
        this.state = 'paused'
        this.stopTimer()
        break
      case 'stop':
        this.stopTimer()
        this.state = 'stopped'
        this.emit({ type: 'session_ended', reason: 'stop' })
        break
      case 'restart':
        this.stopTimer()
        this.timeIndex = 0
        this.state = 'paused'
        this.emitFrame()
        break
    }
  }

  private nominalHz(): number {
    return this.manifest?.nominal_replay_hz ?? DEFAULT_NOMINAL_REPLAY_HZ
  }

  private startTimer() {
    this.stopTimer()
    const intervalMs = 1000 / (this.nominalHz() * this.speed)
    this.timer = setInterval(() => this.tick(), intervalMs)
  }

  private stopTimer() {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  }

  private tick() {
    if (!this.trial) return
    if (this.timeIndex >= this.trial.time_steps) {
      this.stopTimer()
      this.state = 'complete'
      this.emit({ type: 'session_ended', reason: 'complete' })
      return
    }
    this.timeIndex += 1
    this.emitFrame()
  }

  private emitFrame() {
    if (!this.trial) return
    const row = this.trial.amplitude[this.timeIndex]
    if (!row) return
    const meta = this.trial.meta
    this.emit({
      type: 'csi_frame',
      time_index: this.timeIndex,
      subcarriers: row,
      meta,
    })
    this.emit({
      type: 'prediction',
      payload: buildStubPrediction(meta, this.timeIndex, this.trial.time_steps),
    })
  }
}

export const replayTransport = new LocalReplayTransport()
