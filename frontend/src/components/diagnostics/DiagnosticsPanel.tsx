import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ModelStatusCard } from '@/components/model/ModelStatusCard'
import type { ConnectionStatus } from '@/hooks/useConnectionStatus'
import type { ReplayManifest } from '@/types/session'

type TimelineEntry = {
  time_index: number
  activity: string
  confidence: number
  presence: boolean
}

type Props = {
  manifest: ReplayManifest | null
  transportMode: 'websocket' | 'local'
  timeline: TimelineEntry[]
  connection: ConnectionStatus
}

export function DiagnosticsPanel({ manifest, transportMode, timeline, connection }: Props) {
  return (
    <div className="space-y-4">
      <ModelStatusCard />

      <Card className="surface-card border-zinc-800">
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2 text-base">
            Transport &amp; API
            <Badge variant="real">REAL DATA</Badge>
            {transportMode === 'websocket' ? (
              <Badge variant="model">MODEL / WS</Badge>
            ) : (
              <Badge variant="neutral">LOCAL + HTTP</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-400">
          <ul className="list-disc space-y-1 pl-5">
            <li>
              WebSocket:{' '}
              <span className={connection.wsConnected ? 'text-emerald-300' : 'text-amber-200'}>
                {transportMode === 'websocket'
                  ? connection.wsConnected
                    ? 'connected (/ws/stream)'
                    : 'not connected'
                  : 'not used (local mode)'}
              </span>
            </li>
            <li>
              REST API:{' '}
              <span className={connection.apiReachable ? 'text-emerald-300' : 'text-amber-200'}>
                {connection.apiReachable ? 'reachable (GET /api/health)' : connection.apiError ?? 'unreachable'}
              </span>
            </li>
            <li>Dataset: {manifest?.dataset_id ?? 'esp-fi-har'} · {manifest?.session_count ?? '—'} sessions</li>
            <li>Nominal replay: {manifest?.nominal_replay_hz ?? 95} Hz (config)</li>
          </ul>
        </CardContent>
      </Card>

      {timeline.length > 0 && (
        <Card className="surface-card border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm">Session timeline (stream)</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-zinc-400">
              {timeline.map((entry) => (
                <li key={entry.time_index}>
                  t={entry.time_index} · {entry.activity} · {(entry.confidence * 100).toFixed(0)}%
                  {entry.presence ? '' : ' · no presence'}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card className="border-dashed border-amber-600/40 bg-amber-950/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            Spatial overlay
            <Badge variant="simulated">SIMULATED</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-zinc-500">
          Floor plan positions are illustrative — not ESP-Fi localization.
        </CardContent>
      </Card>
    </div>
  )
}
