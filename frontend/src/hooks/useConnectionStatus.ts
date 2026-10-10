import { useEffect, useState } from 'react'

import { fetchHealth } from '@/services/apiClient'
import { replayTransport } from '@/services/replayClient'
import { wsReplayClient } from '@/services/wsReplayClient'

export type ConnectionStatus = {
  transportMode: 'websocket' | 'local'
  wsConnected: boolean
  apiReachable: boolean
  apiError: string | null
}

export function useConnectionStatus(): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>({
    transportMode: replayTransport.getTransportMode(),
    wsConnected: wsReplayClient.isConnected(),
    apiReachable: false,
    apiError: null,
  })

  useEffect(() => {
    const poll = () => {
      void fetchHealth()
        .then(() =>
          setStatus((s) => ({
            ...s,
            transportMode: replayTransport.getTransportMode(),
            wsConnected: wsReplayClient.isConnected(),
            apiReachable: true,
            apiError: null,
          })),
        )
        .catch((err: Error) =>
          setStatus((s) => ({
            ...s,
            transportMode: replayTransport.getTransportMode(),
            wsConnected: wsReplayClient.isConnected(),
            apiReachable: false,
            apiError: err.message,
          })),
        )
    }
    poll()
    const id = window.setInterval(poll, 8000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    const tick = () => {
      setStatus((s) => ({
        ...s,
        transportMode: replayTransport.getTransportMode(),
        wsConnected: wsReplayClient.isConnected(),
      }))
    }
    const id = window.setInterval(tick, 1500)
    return () => window.clearInterval(id)
  }, [])

  return status
}
