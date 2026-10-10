import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  buildGroundTruthEcho,
  replayTransport,
} from '@/services/replayClient'
import { wsReplayClient } from '@/services/wsReplayClient'
import type { CsiStreamFrame } from '@/types/csi'
import type { Prediction } from '@/types/prediction'
import type {
  ReplayManifest,
  ReplaySpeed,
  SessionManifestEntry,
  TransportState,
} from '@/types/session'

const HEATMAP_HISTORY = 120
const PREDICTION_HISTORY = 40

export function useReplaySession() {
  const [manifest, setManifest] = useState<ReplayManifest | null>(null)
  const [selectedId, setSelectedId] = useState<string>('')
  const [transportState, setTransportState] = useState<TransportState>('idle')
  const [speed, setSpeed] = useState<ReplaySpeed>(1)
  const [timeIndex, setTimeIndex] = useState(0)
  const [frame, setFrame] = useState<CsiStreamFrame | null>(null)
  const [heatmap, setHeatmap] = useState<number[][]>([])
  const [error, setError] = useState<string | null>(null)
  const [modelPrediction, setModelPrediction] = useState<Prediction | null>(null)
  const [predictionHistory, setPredictionHistory] = useState<
    Array<Prediction & { time_index: number; ground_truth?: string }>
  >([])
  const [timeline, setTimeline] = useState<
    Array<{ time_index: number; activity: string; confidence: number; presence: boolean }>
  >([])
  const [transportMode, setTransportMode] = useState<'websocket' | 'local'>('local')

  useEffect(() => {
    replayTransport
      .loadManifest()
      .then(async (m) => {
        setManifest(m)
        setSelectedId(m.default_session_id)
        setTransportMode(replayTransport.getTransportMode())
        await replayTransport.openSession(m.default_session_id)
        setTransportState(replayTransport.getState())
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    return replayTransport.subscribe((event) => {
      if (event.type === 'csi_frame') {
        setFrame(event)
        setTimeIndex(event.time_index)
        setHeatmap((prev) => {
          const next = [...prev, event.subcarriers]
          return next.length > HEATMAP_HISTORY ? next.slice(-HEATMAP_HISTORY) : next
        })
        setTransportState(replayTransport.getState())
      } else if (event.type === 'prediction') {
        setModelPrediction(event.payload)
        setPredictionHistory((prev) => {
          const trial = replayTransport.getTrial()
          const gtLabel = trial?.meta?.normalized_label
          const entry = {
            ...event.payload,
            time_index: replayTransport.getTimeIndex(),
            ground_truth: gtLabel,
          }
          const next = [...prev, entry]
          return next.length > PREDICTION_HISTORY ? next.slice(-PREDICTION_HISTORY) : next
        })
        setTransportState(replayTransport.getState())
      } else if (event.type === 'session_started') {
        setError(null)
        setHeatmap([])
        setTimeline([])
        setPredictionHistory([])
        setTransportState(replayTransport.getState())
      } else if (event.type === 'session_ended') {
        setTransportState(replayTransport.getState())
      } else if (event.type === 'error') {
        setError(event.message)
        setTransportState('idle')
      }
    })
  }, [])

  useEffect(() => {
    return wsReplayClient.onTimeline((entries) => setTimeline(entries))
  }, [])

  const groundTruth = useMemo(() => {
    if (!frame) return null
    const trial = replayTransport.getTrial()
    const count = trial?.time_steps ?? wsReplayClient.getFrameCount() ?? 950
    return buildGroundTruthEcho(frame.meta, timeIndex, count)
  }, [frame, timeIndex])

  const openSession = useCallback(async (sessionId: string) => {
    setSelectedId(sessionId)
    await replayTransport.openSession(sessionId)
    setTransportState(replayTransport.getState())
    setTimeIndex(replayTransport.getTimeIndex())
  }, [])

  const play = useCallback(() => {
    replayTransport.control('play')
    setTransportState(replayTransport.getState())
  }, [])

  const pause = useCallback(() => {
    replayTransport.control('pause')
    setTransportState(replayTransport.getState())
  }, [])

  const stop = useCallback(() => {
    replayTransport.control('stop')
    setTransportState(replayTransport.getState())
  }, [])

  const restart = useCallback(() => {
    replayTransport.control('restart')
    setTransportState(replayTransport.getState())
    setTimeIndex(0)
    setHeatmap([])
    setPredictionHistory([])
  }, [])

  const changeSpeed = useCallback((s: ReplaySpeed) => {
    setSpeed(s)
    replayTransport.setSpeed(s)
  }, [])

  const sessions: SessionManifestEntry[] = manifest?.sessions ?? []

  return {
    manifest,
    sessions,
    selectedId,
    transportState,
    speed,
    timeIndex,
    frame,
    heatmap,
    groundTruth,
    modelPrediction,
    predictionHistory,
    error,
    timeline,
    transportMode,
    openSession,
    play,
    pause,
    stop,
    restart,
    changeSpeed,
  }
}
