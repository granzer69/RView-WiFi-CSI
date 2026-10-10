import { ActivityPanel } from '@/components/activity/ActivityPanel'
import { CsiHeatmap } from '@/components/csi/CsiHeatmap'
import { CsiTimeline } from '@/components/csi/CsiTimeline'
import { IntegrityLegend } from '@/components/layout/IntegrityLegend'
import { SessionPicker, SourceChip } from '@/components/session/SessionPicker'
import { TransportControls } from '@/components/session/TransportControls'
import { SimulatedFloorPlan } from '@/components/spatial/SimulatedFloorPlan'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useReplaySession } from '@/hooks/useReplaySession'
import { replayTransport } from '@/services/replayClient'
import { TIME_STEPS } from '@/types/csi'

export function LiveSensingPage() {
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
    error,
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
  const disabled = !trial

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 md:p-6">
      <header className="flex flex-col gap-2 border-b border-zinc-800 pb-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Visual CSI Activity Simulator</h1>
          <p className="text-sm text-zinc-400">R-View WiFi CSI · software-first replay (V1)</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Source</span>
          <SourceChip />
          <span className="text-xs text-zinc-600">V3 API · RF in_domain (dataset replay CSI)</span>
        </div>
      </header>

      {error && (
        <div className="rounded-md border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="flex flex-col gap-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
          <SessionPicker
            sessions={sessions}
            selectedId={selectedId}
            onSelect={(id) => void openSession(id)}
          />
          <TransportControls
            state={transportState}
            speed={speed}
            disabled={disabled}
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
          <Tabs defaultValue="csi">
            <TabsList>
              <TabsTrigger value="csi">CSI</TabsTrigger>
              <TabsTrigger value="activity">ACTIVITY</TabsTrigger>
              <TabsTrigger value="spatial">SPATIAL</TabsTrigger>
              <TabsTrigger value="system">SYSTEM</TabsTrigger>
            </TabsList>

            <TabsContent value="csi" className="space-y-4">
              <CsiHeatmap heatmap={heatmap} timeIndex={timeIndex} totalSteps={totalSteps} />
              <CsiTimeline
                timeIndex={timeIndex}
                totalSteps={totalSteps}
                label={meta?.normalized_label ?? '—'}
              />
            </TabsContent>

            <TabsContent value="activity">
              <ActivityPanel meta={meta} groundTruth={groundTruth} modelPrediction={modelPrediction} />
            </TabsContent>

            <TabsContent value="spatial">
              <SimulatedFloorPlan
                scenarioId={meta?.scenario_id ?? 1}
                scenarioName={meta?.scenario_name}
                prediction={modelPrediction ?? groundTruth}
              />
            </TabsContent>

            <TabsContent value="system">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 text-sm text-zinc-300">
                <ul className="list-disc space-y-1 pl-5 text-zinc-400">
                  <li>Transport: LocalReplayTransport (in-browser, manifest + exported trials)</li>
                  <li>Dataset: {manifest?.dataset_id ?? 'esp-fi-har'} · {manifest?.session_count ?? '—'} sessions in manifest</li>
                  <li>Nominal replay: {manifest?.nominal_replay_hz ?? 95} Hz (config only)</li>
                  <li>Python simulator: src/simulator/ · V3 API: src/api/ (POST /predict, WS /ws/stream)</li>
                </ul>
              </div>
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
