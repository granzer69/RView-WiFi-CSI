import { useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchHealth } from '@/services/apiClient'
import { wsReplayClient, type ModelStatus } from '@/services/wsReplayClient'
import { replayTransport } from '@/services/replayClient'

export function ModelStatusCard() {
  const [status, setStatus] = useState<ModelStatus & { model_path?: string }>({
    model_loaded: false,
  })
  const transport = replayTransport.getTransportMode()

  useEffect(() => {
    void fetchHealth()
      .then((h) =>
        setStatus({
          model_loaded: h.model_loaded,
          active_model_id: h.active_model_id,
          load_error: h.model_load_error,
          model_path: h.model_path,
        }),
      )
      .catch(() => setStatus({ model_loaded: false, load_error: 'API unreachable' }))
    return wsReplayClient.onModelStatus((ws) => setStatus((prev) => ({ ...prev, ...ws })))
  }, [])

  const presenceHint =
    status.model_loaded
      ? 'Presence derived from model confidence (software replay; not hardware radar).'
      : 'Model not loaded — predictions unavailable until artifact loads.'

  return (
    <Card className="border-zinc-800">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          Model status
          <Badge variant={status.model_loaded ? 'real' : 'neutral'}>
            {status.model_loaded ? 'LOADED' : 'UNAVAILABLE'}
          </Badge>
          <Badge variant="neutral">{transport === 'websocket' ? 'WS STREAM' : 'LOCAL + HTTP'}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm text-zinc-400">
        <p>{status.active_model_id ?? '—'}</p>
        {status.model_version && <p className="text-xs">Version: {status.model_version}</p>}
        {status.model_path && <p className="text-xs text-zinc-500">{status.model_path}</p>}
        {status.load_error && <p className="text-xs text-red-300">{status.load_error}</p>}
        <p className="text-xs text-zinc-500">{presenceHint}</p>
      </CardContent>
    </Card>
  )
}
