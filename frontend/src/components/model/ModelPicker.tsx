import { useCallback, useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { fetchModels, selectActiveModel } from '@/services/apiClient'
import { wsReplayClient } from '@/services/wsReplayClient'

type ModelSummary = {
  model_id: string
  family: string
  split_strategy: string
}

type Props = {
  onError?: (message: string) => void
  onActiveModelChange?: (info: ModelSummary) => void
}

export function ModelPicker({ onError, onActiveModelChange }: Props) {
  const [models, setModels] = useState<
    Array<{
      model_id: string
      family: string
      split_strategy: string
      model_type: string
      load_error?: string
    }>
  >([])
  const [activeId, setActiveId] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const payload = await fetchModels()
      setModels(payload.models)
      const nextId = payload.active_model_id ?? ''
      setActiveId(nextId)
      const active = payload.models.find((m) => m.model_id === nextId)
      if (active) {
        onActiveModelChange?.({
          model_id: active.model_id,
          family: active.family,
          split_strategy: active.split_strategy,
        })
      }
    } catch (err) {
      onError?.(err instanceof Error ? err.message : 'Failed to load models')
    }
  }, [onError, onActiveModelChange])

  useEffect(() => {
    void refresh()
    return wsReplayClient.onModelStatus((status) => {
      if (status.active_model_id) setActiveId(status.active_model_id)
    })
  }, [refresh])

  const onSelect = async (modelId: string) => {
    setLoading(true)
    try {
      await selectActiveModel(modelId)
      if (wsReplayClient.isConnected()) {
        wsReplayClient.selectModel(modelId)
      }
      setActiveId(modelId)
      await refresh()
    } catch (err) {
      onError?.(err instanceof Error ? err.message : 'Model switch failed')
    } finally {
      setLoading(false)
    }
  }

  if (!models.length) {
    return <p className="text-xs text-zinc-500">No V2 artifacts discovered. Train models or set RVIEW_MODEL_DIR.</p>
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">Active model</p>
        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => void refresh()}>
          Refresh
        </Button>
      </div>
      <select
        className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
        value={activeId}
        disabled={loading}
        onChange={(e) => void onSelect(e.target.value)}
      >
        {models.map((m) => (
          <option key={m.model_id} value={m.model_id}>
            {m.family} · {m.split_strategy} · {m.model_type}
            {m.load_error ? ' (unloadable)' : ''}
          </option>
        ))}
      </select>
      {activeId && (
        <p className="text-xs text-zinc-500">
          <Badge variant="model">INFERENCE</Badge> {activeId}
        </p>
      )}
    </div>
  )
}
