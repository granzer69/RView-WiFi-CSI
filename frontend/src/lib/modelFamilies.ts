/** V2 model families surfaced in evaluation and workbench UIs. */
export const MODEL_FAMILIES = [
  'logreg',
  'rf',
  'mlp',
  'gbdt',
  'cnn1d',
  'gru',
  'tcn',
] as const

export type ModelFamily = (typeof MODEL_FAMILIES)[number]
