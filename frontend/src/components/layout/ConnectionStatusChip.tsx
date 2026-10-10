import { Badge } from '@/components/ui/badge'
import type { ConnectionStatus } from '@/hooks/useConnectionStatus'

type Props = {
  status: ConnectionStatus
}

export function ConnectionStatusChip({ status }: Props) {
  const wsOk = status.transportMode === 'websocket' && status.wsConnected
  const wsLabel =
    status.transportMode === 'websocket'
      ? wsOk
        ? 'WS connected'
        : 'WS disconnected'
      : 'Local replay'

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <Badge variant={wsOk || status.transportMode === 'local' ? 'real' : 'simulated'}>
        {wsLabel}
      </Badge>
      <Badge variant={status.apiReachable ? 'real' : 'neutral'}>
        API {status.apiReachable ? 'OK' : 'unreachable'}
      </Badge>
    </div>
  )
}
