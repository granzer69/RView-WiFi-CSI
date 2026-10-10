import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Prediction } from '@/types/prediction'
import type { SessionMeta } from '@/types/session'

type Props = {
  meta: SessionMeta | null
  groundTruth: Prediction | null
  modelPrediction: Prediction | null
}

export function ActivityPanel({ meta, groundTruth, modelPrediction }: Props) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Card className="border-emerald-800/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Ground truth
            <Badge variant="real">REAL DATA</Badge>
            <Badge variant="neutral">GROUND TRUTH</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {meta ? (
            <>
              <p className="text-2xl font-semibold capitalize">{meta.normalized_label}</p>
              <p className="text-zinc-400">
                Code {meta.activity_code} · dataset label {meta.dataset_label}
              </p>
              <p className="text-xs text-zinc-500">
                {meta.label_verified_by_folder
                  ? 'Verified by scenario-3 class folder'
                  : 'Inferred from filename code (scenarios 1, 2, 4 unverified)'}
              </p>
            </>
          ) : (
            <p className="text-zinc-500">Select a session and press play.</p>
          )}
          {groundTruth && (
            <p className="text-xs text-zinc-500">
              Echo tier: dataset_replay · confidence {groundTruth.confidence.toFixed(2)}
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="border-sky-800/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Model output
            <Badge variant="model">MODEL PREDICTION</Badge>
            {modelPrediction?.model_version?.startsWith('stub') ? (
              <Badge variant="neutral">STUB</Badge>
            ) : (
              <Badge variant="real">V3 API</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {modelPrediction ? (
            <>
              <p className="text-2xl font-semibold capitalize">{modelPrediction.activity}</p>
              <p className="text-zinc-400">
                Confidence {(modelPrediction.confidence * 100).toFixed(1)}% · latency{' '}
                {modelPrediction.latency_ms} ms
              </p>
              {modelPrediction.model_version?.startsWith('stub') ? (
                <p className="text-xs text-amber-200/90">
                  API unreachable — showing synthetic stub. Start the V3 API on port 45231.
                </p>
              ) : (
                <p className="text-xs text-emerald-200/90">
                  Live inference via POST /predict (V2 RF artifact, dataset replay CSI).
                </p>
              )}
              <p className="text-xs text-zinc-500">Version: {modelPrediction.model_version}</p>
            </>
          ) : (
            <p className="text-zinc-500">Play replay to emit model predictions.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
