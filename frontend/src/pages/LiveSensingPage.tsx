import { useCallback, useState } from 'react'

import { ActivityPanel } from '@/components/activity/ActivityPanel'
import { CsiHeatmap } from '@/components/csi/CsiHeatmap'
import { CsiTimeline } from '@/components/csi/CsiTimeline'
import { SubcarrierWaveform } from '@/components/csi/SubcarrierWaveform'
import { DiagnosticsPanel } from '@/components/diagnostics/DiagnosticsPanel'
import { ConnectionStatusChip } from '@/components/layout/ConnectionStatusChip'
import { IntegrityLegend } from '@/components/layout/IntegrityLegend'
import { ModelPicker } from '@/components/model/ModelPicker'
import { SummaryMetricsBar } from '@/components/sensing/SummaryMetricsBar'
import { SessionPicker, SourceChip } from '@/components/session/SessionPicker'
import { TransportControls } from '@/components/session/TransportControls'
import { SimulatedFloorPlan } from '@/components/spatial/SimulatedFloorPlan'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useConnectionStatus } from '@/hooks/useConnectionStatus'
import { useReplaySession } from '@/hooks/useReplaySession'
import { replayTransport } from '@/services/replayClient'
import { TIME_STEPS } from '@/types/csi'

export function LiveSensingPage() {
  const [pickerError, setPickerError] = useState<string | null>(null)
  const [activeModelLabel, setActiveModelLabel] = useState<string>('—')
  const connection = useConnectionStatus()
  const {
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
  } = useReplaySession()

  const trial = replayTransport.getTrial()
  const totalSteps = trial?.time_steps ?? TIME_STEPS
  const meta = frame?.meta ?? trial?.meta ?? null
  const disabled = transportMode === 'local' && !trial
  const disabledReason =
    disabled
      ? 'Local mode: open a session from the manifest first.'
      : manifest == null
        ? 'Loading replay manifest…'
        : undefined
  const manifestEmpty = manifest != null && sessions.length === 0

  const onActiveModel = useCallback(
    (info: { model_id: string; family: string; split_strategy: string }) => {
      setActiveModelLabel(`${info.family} · ${info.split_strategy}`)
    },
    [],
  )

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <header className="flex flex-col gap-3 border-b border-zinc-800 pb-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="real">DATASET REPLAY</Badge>
            <SourceChip />
          </div>
          <p className="text-sm text-zinc-400">
            Research workstation · ESP-Fi amplitude replay (no hardware)
          </p>
          <ConnectionStatusChip status={connection} />
        </div>
        <div className="rounded-lg border border-zinc-800 surface-elevated px-3 py-2 text-sm">
          <p className="text-[10px] uppercase tracking-wide text-zinc-500">Active model</p>
          <p className="font-medium text-cyan-100">{activeModelLabel}</p>
        </div>
      </header>

      {(error || pickerError) && (
        <div className="rounded-md border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {error ?? pickerError}
        </div>
      )}

      {manifestEmpty && (
        <div className="rounded-md border border-amber-800 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
          Replay manifest has no sessions. Export trials or check RVIEW_DATA paths.
        </div>
      )}

      {!frame && transportState === 'idle' && !error && (
        <div className="skeleton-pulse h-16 w-full" aria-hidden />
      )}

      <SummaryMetricsBar
        meta={meta}
        groundTruth={groundTruth}
        modelPrediction={modelPrediction}
      />

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="flex flex-col gap-4 rounded-lg border border-zinc-800 surface-card p-4">
          <SessionPicker
            sessions={sessions}
            selectedId={selectedId}
            onSelect={(id) => void openSession(id)}
          />
          <ModelPicker onError={setPickerError} onActiveModelChange={onActiveModel} />
          <TransportControls
            state={transportState}
            speed={speed}
            disabled={disabled || manifestEmpty}
            disabledReason={disabledReason}
            onPlay={play}
            onPause={pause}
            onStop={stop}
            onRestart={restart}
            onSpeed={changeSpeed}
          />
          {manifest && (
            <p className="text-xs text-zinc-500">{manifest.timing_note}</p>
          )}
        </aside>

        <main className="flex flex-col gap-4">
          <Tabs defaultValue="sensing">
            <TabsList className="flex flex-wrap">
              <TabsTrigger value="sensing">Sensing</TabsTrigger>
              <TabsTrigger value="activity">Activity analysis</TabsTrigger>
              <TabsTrigger value="spatial">Spatial</TabsTrigger>
              <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
            </TabsList>

            <TabsContent value="sensing" className="space-y-4">
              <div className="grid gap-4 xl:grid-cols-2">
                <CsiHeatmap heatmap={heatmap} timeIndex={timeIndex} totalSteps={totalSteps} />
                <SubcarrierWaveform subcarriers={frame?.subcarriers ?? null} timeIndex={timeIndex} />
              </div>
              <CsiTimeline
                timeIndex={timeIndex}
                totalSteps={totalSteps}
                label={meta?.normalized_label ?? '—'}
              />
            </TabsContent>

            <TabsContent value="activity">
              <ActivityPanel
                meta={meta}
                groundTruth={groundTruth}
                modelPrediction={modelPrediction}
                predictionHistory={predictionHistory}
                timeline={timeline}
              />
            </TabsContent>

            <TabsContent value="spatial">
              <SimulatedFloorPlan
                scenarioId={meta?.scenario_id ?? 1}
                scenarioName={meta?.scenario_name}
                prediction={modelPrediction ?? groundTruth}
              />
            </TabsContent>

            <TabsContent value="diagnostics">
              <DiagnosticsPanel
                manifest={manifest}
                transportMode={transportMode}
                timeline={timeline}
                connection={connection}
              />
            </TabsContent>
          </Tabs>
        </main>
      </div>

      <footer className="border-t border-zinc-800 pt-4">
        <IntegrityLegend />
      </footer>
    </div>
  )
}
