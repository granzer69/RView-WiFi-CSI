# Sensing Studio UI reskin (2026)

Scientific-workstation refresh for R-View Sensing Studio. Tailwind v4 + existing shadcn-style primitives only (no new component library).

## Visual system

| Token / utility | Role |
| --- | --- |
| `--color-signal-cyan` / `text-signal` | Primary accent, active nav, key metrics |
| `--color-surface-card` / `.surface-card` | Panel backgrounds (slate-violet tint) |
| `--color-surface-elevated` / `.surface-elevated` | Nested panels, table headers |
| `--color-border-subtle` | Dividers and card borders |
| `.workstation-grid` | Subtle lab grid on page shells |
| `.font-display` | Page titles (system-ui stack, tight tracking) |
| `.data-table` | Evaluation / research tables (zebra, readable numerics) |

## Typography hierarchy

1. **Eyebrow** — uppercase, wide tracking (`StudioPageChrome` eyebrow).
2. **Page title** — `font-display` 2xl–3xl semibold.
3. **Section titles** — `CardTitle` sm semibold.
4. **Body / captions** — zinc-400 body, zinc-500 meta; minimum 12px for table cells.

## Navigation

- Sticky header with backdrop blur and bottom border.
- Active route: cyan-tinted fill + ring (`WorkspaceShell` `navLinkClass`).
- Footer mirrors primary routes for keyboard/screen-reader wayfinding.

## Integrity labels (unchanged semantics)

- **REAL DATA** / **DATASET REPLAY** — measured ESP-Fi replay.
- **MODEL PREDICTION** — active V2 artifact inference.
- **SIMULATED** — spatial floor plan and non-measured overlays only.

## Label inference caveat

`LabelInferenceCaveat` is shown on **Research Lab**, **CSI Explorer**, and **Experiments** (workbench) pages. Copy matches dataset documentation: scenarios 1/2/4 labels are inferred from the scenario-3 folder map.

## States

- **Loading** — `.skeleton-pulse` blocks; explicit “Loading…” copy where data is fetched.
- **Empty** — neutral zinc copy; no placeholder metrics.
- **Error** — `border-rose-900/50` panels with API message text only.

## Components touched

- `frontend/src/index.css` — tokens and utilities
- `frontend/src/components/layout/WorkspaceShell.tsx`
- `frontend/src/components/layout/StudioPageChrome.tsx`
- `frontend/src/components/layout/LabelInferenceCaveat.tsx`
- `frontend/src/components/ui/card.tsx`
- Major pages: sensing home, evaluation, research, explorer, experiments

## Accessibility

- WCAG-friendly contrast on amber caveat and cyan accents on zinc-950.
- `role="note"` on caveat; `aria-label` on primary nav.
- Responsive stacks: header nav wraps; tables scroll horizontally inside cards.
