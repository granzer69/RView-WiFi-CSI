import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  buildGroundTruthEcho,
  replayTransport,
} from '@/services/replayClient'
import type { CsiStreamFrame } from '@/types/csi'
import type { Prediction } from '@/types/prediction'
import type {
  ReplayManifest,
  ReplaySpeed,
  SessionManifestEntry,
  TransportState,
} from '@/types/session'

const HEATMAP_HISTORY = 120

export function useReplaySession() {
  const [manifest, setManifest] = useState<ReplayManifest | null>(null)
  const [selectedId, setSelectedId] = useState<string>('')
  const [transportState, setTransportState] = useState<TransportState>('idle')
  const [speed, setSpeed] = useState<ReplaySpeed>(1)
  const [timeIndex, setTimeIndex] = useState(0)
  const [frame, setFrame] = useState<CsiStreamFrame | null>(null)
  const [heatmap, setHeatmap] = useState<number[][]>([])
  const [error, setError] = useState<string | null>(null)
  const [stubPrediction, setStubPrediction] = useState<Prediction | null>(null)

  useEffect(() => {
    replayTransport
      .loadManifest()
      .then(async (m) => {
        setManifest(m)
        setSelectedId(m.default_session_id)
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
        setStubPrediction(event.payload)
        setTransportState(replayTransport.getState())
      } else if (event.type === 'session_started') {
        setError(null)
        setHeatmap([])
        setTransportState(replayTransport.getState())
      } else if (event.type === 'session_ended') {
        setTransportState(replayTransport.getState())
      } else if (event.type === 'error') {
        setError(event.message)
        setTransportState('idle')
      }
    })
  }, [])

  const groundTruth = useMemo(() => {
    if (!frame) return null
    const trial = replayTransport.getTrial()
    const count = trial?.time_steps ?? 950
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
    stubPrediction,
    error,
    openSession,
    play,
    pause,
    stop,
    restart,
    changeSpeed,
  }
}
