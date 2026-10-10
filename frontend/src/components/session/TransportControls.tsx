import { Pause, Play, RotateCcw, Square } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { ReplaySpeed, TransportState } from '@/types/session'
import { REPLAY_SPEEDS } from '@/types/session'

type Props = {
  state: TransportState
  speed: ReplaySpeed
  disabled?: boolean
  onPlay: () => void
  onPause: () => void
  onStop: () => void
  onRestart: () => void
  onSpeed: (s: ReplaySpeed) => void
}

export function TransportControls({
  state,
  speed,
  disabled,
  onPlay,
  onPause,
  onStop,
  onRestart,
  onSpeed,
}: Props) {
  const playing = state === 'playing'
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          disabled={disabled}
          onClick={onRestart}
          title="Restart"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
        <Button
          type="button"
          variant="default"
          size="icon"
          disabled={disabled}
          onClick={playing ? onPause : onPlay}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="icon"
          disabled={disabled}
          onClick={onStop}
          title="Stop"
        >
          <Square className="h-4 w-4" />
        </Button>
      </div>
      <div>
        <p className="mb-1 text-xs text-zinc-500">Speed</p>
        <div className="flex flex-wrap gap-1">
          {REPLAY_SPEEDS.map((s) => (
            <Button
              key={s}
              type="button"
              size="sm"
              variant={speed === s ? 'default' : 'outline'}
              disabled={disabled}
              onClick={() => onSpeed(s)}
            >
              {s}×
            </Button>
          ))}
        </div>
      </div>
      <p className="text-xs text-zinc-500 capitalize">State: {state}</p>
    </div>
  )
}
