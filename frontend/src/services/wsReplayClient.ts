import { apiBaseUrl } from '@/services/apiClient'
import type { ReplayEvent, ReplaySpeed, TransportState } from '@/types/session'

type WsServerMessage =
  | { type: 'session_started'; session_id: string; source: string; frame_count?: number }
  | { type: 'csi_frame'; time_index: number; subcarriers: number[]; meta: import('@/types/session').SessionMeta }
  | { type: 'prediction'; payload: import('@/types/prediction').Prediction }
  | { type: 'session_ended'; reason: 'stop' | 'complete' }
  | { type: 'error'; message: string }
  | { type: 'model_status'; model_loaded: boolean; active_model_id?: string; model_version?: string; load_error?: string }
  | { type: 'timeline'; entries: Array<{ time_index: number; activity: string; confidence: number; presence: boolean }> }
  | { type: 'pong' }

function wsUrl(): string {
  const base = apiBaseUrl()
  if (base.startsWith('http')) {
    const url = new URL(base)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    url.pathname = '/ws/stream'
    return url.toString()
  }
  const loc = window.location
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${loc.host}/ws/stream`
}

export type ModelStatus = {
  model_loaded: boolean
  active_model_id?: string
  model_version?: string
  load_error?: string
}

export class WebSocketReplayClient {
  private socket: WebSocket | null = null
  private listeners = new Set<(event: ReplayEvent) => void>()
  private statusListeners = new Set<(status: ModelStatus) => void>()
  private timelineListeners = new Set<
    (entries: Array<{ time_index: number; activity: string; confidence: number; presence: boolean }>) => void
  >()
  private state: TransportState = 'idle'
  private connected = false
  private frameCount = 0
  private timeline: Array<{ time_index: number; activity: string; confidence: number; presence: boolean }> = []

  subscribe(listener: (event: ReplayEvent) => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onModelStatus(listener: (status: ModelStatus) => void): () => void {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  onTimeline(listener: (entries: typeof this.timeline) => void): () => void {
    this.timelineListeners.add(listener)
    return () => this.timelineListeners.delete(listener)
  }

  getTimeline() {
    return this.timeline
  }

  isConnected(): boolean {
    return this.connected && this.socket?.readyState === WebSocket.OPEN
  }

  getState(): TransportState {
    return this.state
  }

  getFrameCount(): number {
    return this.frameCount
  }

  async connect(): Promise<boolean> {
    if (this.isConnected()) return true
    return new Promise((resolve) => {
      try {
        const socket = new WebSocket(wsUrl())
        this.socket = socket
        socket.onopen = () => {
          this.connected = true
          resolve(true)
        }
        socket.onerror = () => {
          this.connected = false
          resolve(false)
        }
        socket.onclose = () => {
          this.connected = false
          this.state = 'idle'
        }
        socket.onmessage = (ev) => {
          const msg = JSON.parse(ev.data as string) as WsServerMessage
          this.handleMessage(msg)
        }
      } catch {
        resolve(false)
      }
    })
  }

  private emit(event: ReplayEvent) {
    for (const listener of this.listeners) listener(event)
  }

  private handleMessage(msg: WsServerMessage) {
    switch (msg.type) {
      case 'session_started':
        this.state = 'paused'
        this.frameCount = msg.frame_count ?? this.frameCount
        this.timeline = []
        this.emit({ type: 'session_started', session_id: msg.session_id, source: 'dataset_replay' })
        break
      case 'csi_frame':
        this.emit({
          type: 'csi_frame',
          time_index: msg.time_index,
          subcarriers: msg.subcarriers,
          meta: msg.meta,
        })
        break
      case 'prediction':
        this.emit({ type: 'prediction', payload: msg.payload })
        break
      case 'session_ended':
        this.state = msg.reason === 'complete' ? 'complete' : 'stopped'
        this.emit({ type: 'session_ended', reason: msg.reason })
        break
      case 'error':
        this.emit({ type: 'error', message: msg.message })
        break
      case 'model_status':
        for (const listener of this.statusListeners) {
          listener({
            model_loaded: msg.model_loaded,
            active_model_id: msg.active_model_id,
            model_version: msg.model_version,
            load_error: msg.load_error,
          })
        }
        break
      case 'timeline':
        this.timeline = msg.entries
        for (const listener of this.timelineListeners) listener(this.timeline)
        break
      default:
        break
    }
  }

  private send(payload: Record<string, unknown>) {
    if (!this.isConnected() || !this.socket) return
    this.socket.send(JSON.stringify(payload))
  }

  openSession(sessionId: string) {
    this.send({ type: 'open_session', session_id: sessionId })
  }

  control(action: 'play' | 'pause' | 'stop' | 'restart', speed?: ReplaySpeed) {
    if (action === 'play') this.state = 'playing'
    if (action === 'pause') this.state = 'paused'
    this.send({ type: 'control', action, speed })
  }

  selectModel(modelId: string) {
    this.send({ type: 'select_model', model_id: modelId })
  }

  disconnect() {
    this.socket?.close()
    this.socket = null
    this.connected = false
  }
}

export const wsReplayClient = new WebSocketReplayClient()
