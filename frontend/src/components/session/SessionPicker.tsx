import { Badge } from '@/components/ui/badge'
import type { SessionManifestEntry } from '@/types/session'

type Props = {
  sessions: SessionManifestEntry[]
  selectedId: string
  onSelect: (id: string) => void
}

export function SessionPicker({ sessions, selectedId, onSelect }: Props) {
  const exported = new Set(['1-1-2-1', '1-1-1-1'])

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-medium text-zinc-400" htmlFor="session-select">
        Session
      </label>
      <select
        id="session-select"
        className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2 text-sm"
        value={selectedId}
        onChange={(e) => onSelect(e.target.value)}
      >
        {sessions.map((s) => (
          <option key={s.session_id} value={s.session_id}>
            {s.session_id} — {s.normalized_label} ({s.scenario_name})
            {!exported.has(s.session_id) ? ' [manifest only]' : ''}
          </option>
        ))}
      </select>
      <p className="text-xs text-zinc-500">
        Full CSI replay requires exported trial JSON. Default demos: 1-1-2-1, 1-1-1-1.
      </p>
    </div>
  )
}

export function SourceChip() {
  return (
    <Badge variant="neutral" className="text-sm">
      Dataset Replay
    </Badge>
  )
}
