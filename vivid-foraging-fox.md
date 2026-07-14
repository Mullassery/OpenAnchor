# PrismNote — Data Explorer + Visualization Pane (beat Positron)

## Context

PrismNote's data-inspection UX is currently minimal: the **Variables** and **Plots**
tabs live in `BottomPanel.tsx`, the "Plots" tab just lists `image/png` outputs, and
DataFrame results render through `DataFrameView.tsx` — a 200-row fallback `<table>` plus
hand-rolled inline-SVG bar/line charts. There is no way to truly *explore* a dataframe
(scroll past 200 rows, sort, filter, see per-column distributions/types) and no way to
build a chart without writing code.

The goal is a **Data Explorer** that feels like BigQuery/Snowflake's table view
(Schema / Preview / Statistics, server-side paging/sort/filter, per-column profiling),
and a **Visualization Pane** that combines a Positron-style plot-history gallery with a
**Looker-style no-code Explore** (drag dimensions/measures → pick chart → aggregate →
render). Both must scale past the current 200-row cap by pushing work into the live
Python kernel where the data already lives.

Decisions (confirmed with user):
- **Charts:** Vega-Lite via `react-vega` (export PNG/SVG, "copy as Altair code").
- **Scope:** Full — plot gallery **and** Looker Explore this round.
- **Grid:** `@tanstack/react-virtual` for windowed rows/cols.

## Architecture fit (existing code to reuse)

- **Kernel protocol** — `crates/server/src/kernel.rs`: line-framed JSON over stdin/stdout.
  Already has `__PRISM_INSPECT__` → `_inspect()` (Py) ↔ `KernelManager::inspect()` (Rust).
  We add one more command the same way; **no new process, no new framing.**
- **Variable list** — `api.rs::kernel_variables` (`GET /api/kernel/variables`) shows the
  pattern for reaching `state.kernel` from a handler. New explore handlers mirror it.
- **DataFrame MIME** — `_mime_bundle` already emits `application/vnd.prismnote.df+json`
  (`orient="split"`, capped 500 rows). Explorer reuses the same shape for page payloads.
- **Reproducibility / copy-as-code** — `DataPanel.insertAsCell` + `data.ts::queryCode`
  show the established "generate Python and drop it into a cell" idiom; Explorer export and
  Viz "copy as code" reuse it (`useNotebookStore.addCell/updateCell`).
- **Overlay panel pattern** — `App.tsx` renders full-bleed center overlays toggled by state
  (`dataOpen && <DataPanel/>`, `jobsOpen && <JobsPanel/>`). Data Explorer follows this.
- **Tabbed bottom dock** — `BottomPanel.tsx` already owns the **Variables** and **Plots**
  tabs and derives `imageOutputs` from notebook cell outputs. We upgrade these in place.
- **Plot rendering today** — `Output.tsx` `display_data` renders `image/png`; we also let it
  register plots into a store so the Visualization Pane can collect them.

---

## Backend (Rust + Python kernel)

### 1. New kernel command — `kernel.rs`
Add `_explore(req)` to the Python `DRIVER` and `KernelManager::explore(req: Value)` in Rust
(copy `inspect()` almost verbatim: write `__PRISM_EXPLORE__` + JSON line, read the
`__PRISM_RESULT__` reply). `_explore` dispatches on `req["op"]`, operating on
`_ns[req["var"]]` (pandas first; if polars, `.to_pandas()`; numpy → wrap in DataFrame):

- `op:"schema"` → `{ shape:[rows,cols], columns:[{name,dtype,logical:"number|string|datetime|bool|other",null_count,null_pct,unique?}], mem_bytes }`
- `op:"page"` → input `{var, offset, limit, sort:[{col,dir}], filters:[{col,op,value}], search}`.
  Apply filters (`==,!=,<,<=,>,>=,contains,in,isnull,notnull`) → global `search` (substring
  across stringified cols) → multi-sort → `.iloc[offset:offset+limit]`. Return
  `{columns, data, total}` (post-filter count) in df+json `split` shape. `limit` capped (e.g. 500).
- `op:"profile"` → input `{var, col}`. Numeric: `{kind:"number", min,max,mean,median,std,q:[...], null_pct, hist:{counts,edges}}`; categorical/string: `{kind:"category", cardinality, null_pct, top:[{value,count}] (k=20)}`; datetime: range + time histogram.
- `op:"aggregate"` (powers Looker Explore server-side) → input `{var, dims:[...], measures:[{col,agg}], filters, limit}` → grouped/aggregated rows in df+json shape. Keeps big-data aggregation in the kernel rather than shipping all rows to the browser.

Guard every op in try/except; on missing var or non-tabular value return `{error}`.

### 2. SVG figure capture (vector export) — `kernel.rs` `_capture_figures`
Also save each matplotlib figure as `image/svg+xml` (in addition to existing png) so the
Visualization Pane can offer crisp vector zoom/export — a concrete edge over Positron.

### 3. HTTP endpoints — `api.rs` + routes in `main.rs`
Mirror `kernel_variables` (lock `state.kernel`, call `explore`, JSON back):
- `POST /api/explore/schema`     `{var}`
- `POST /api/explore/page`       `{var, offset, limit, sort, filters, search}`
- `POST /api/explore/profile`    `{var, col}`
- `POST /api/explore/aggregate`  `{var, dims, measures, filters, limit}`
- `POST /api/explore/export-code` `{var, sort, filters}` → returns reproducible pandas code
  string (reuse the `queryCode`/`insertAsCell` idiom) for "copy as code" / insert-as-cell.

---

## Frontend

### 4. API client — `frontend/src/api/explore.ts`
Typed wrappers for the five endpoints above (`schema/page/profile/aggregate/exportCode`),
plus shared TS types (`ColumnSchema`, `ColumnProfile`, `PageResult`, `Filter`, `Sort`).

### 5. Data Explorer — `frontend/src/components/DataExplorer.tsx`
Full-bleed center overlay (same shell as `DataPanel`), opened with a target `var` name.
BigQuery/Snowflake-style **tabs**:
- **Preview (grid):** `@tanstack/react-virtual` windowed grid, sticky header, server paging
  on scroll via `/explore/page`. Column header = name + dtype chip + null% bar + a mini
  histogram/sparkline (from `/explore/profile`, lazy + cached). Click header → sort
  (asc/desc/none; shift = multi-sort). Per-column quick filter (numeric range, categorical
  multiselect, text contains) + a global search box → rebuilds the `page` request.
- **Schema:** column list with type, logical type, null%, uniqueness (table form).
- **Statistics:** per-column profile cards (full stats + larger histogram / top values).
- **Side summary panel:** clicking a column opens detailed stats + distribution.
- **Status bar:** total rows, filtered rows, memory.
- **Export:** "Copy as code" / "Insert as cell" (via `/explore/export-code` +
  `useNotebookStore`) and "Download CSV".

### 6. Visualization Pane — `frontend/src/components/VizPane.tsx`
Add a new dependency `react-vega` + `vega`/`vega-lite`. Two modes via an internal toggle,
mounted as the upgraded **Plots** tab content in `BottomPanel.tsx` (and reachable from the
Data Explorer "Visualize" button):
- **Gallery (Positron-style):** collects plots from a new `usePlots` store — large active
  view with wheel-zoom / pan / fit, a thumbnail filmstrip + prev/next, and a toolbar:
  Copy to clipboard, Save PNG, Save SVG (uses the new svg capture), Open in new tab,
  Clear all, light/dark plot background.
- **Explore (Looker-style, no-code):** pick a dataframe (from `/api/kernel/variables`,
  DataFrame-typed only) → drag columns into **Dimensions / Measures / Color / Size** shelves
  → choose chart type (bar/line/area/scatter/heatmap/pie/histogram/boxplot) + aggregation
  (sum/avg/count/min/max) → builds a Vega-Lite spec rendered with `react-vega`. Data comes
  from `/explore/aggregate` (kernel-side grouping). "Copy as code" emits equivalent Altair
  (Python) into a cell; export PNG/SVG via Vega's `exporter`.

### 7. Plot collection store — `frontend/src/hooks/usePlots.ts`
Zustand store (same pattern as `useNotebook`): `plots[]`, `currentIndex`, `addPlot(output)`,
`select`, `clear`. `Output.tsx` registers an output when it carries `image/png` /
`image/svg+xml` (dedupe by content hash so re-renders don't duplicate). Gallery reads it.

### 8. Wiring — `App.tsx`, `BottomPanel.tsx`, variables list
**Data Explorer is the product's #1 surface — rank it above the Notebook everywhere:**
- `App.tsx`: add `explorerVar` state + `{explorerVar && <DataExplorer var={explorerVar} onClose/>}`
  overlay. Make Data Explorer the **first/topmost activity-rail button** (above Files/Notebook),
  with a distinct primary-accent icon (Table) so it reads as the headline feature.
- **Default landing:** when no notebook is open, the empty state's primary call-to-action is
  **"Open Data Explorer"** (the New-Notebook button becomes secondary), and the Data Explorer
  opens with a variable picker when no var is chosen.
- **Menus/commands:** list "Data Explorer" first in the command palette and the MenuBar
  (before Notebook actions), with a memorable shortcut (e.g. ⌘E).
- `BottomPanel.tsx`: **Variables** tab — add an "Open in Data Explorer" action on
  DataFrame/ndarray rows (sets `explorerVar`). **Plots** tab — replace the current
  `imageOutputs` list with `<VizPane/>`.
- Keep existing inline `DataFrameView` in cell outputs, but add an "Open in Data Explorer"
  affordance on DataFrame outputs.

---

## Verification (end-to-end)

1. **Build:** `cargo check` (server) and `cd frontend && npm install && npx tsc --noEmit`
   (after adding `react-vega vega vega-lite @tanstack/react-virtual`).
2. **Run app:** start the server (`cargo run`) + frontend (`npm run dev`); open a notebook.
3. **Data Explorer:** run a cell creating a large frame
   (`import pandas as pd, numpy as np; df = pd.DataFrame({'x':np.random.randn(100000),'g':np.random.choice(list('abcd'),100000)})`).
   Variables tab → Open in Data Explorer → confirm: scrolls past 200 rows smoothly (virtualized),
   header histograms render, sort + numeric-range filter + global search update the grid,
   Statistics tab shows correct mean/quantiles, "Insert as cell" produces runnable pandas.
4. **Viz Gallery:** run a matplotlib cell (`df['x'].hist()`); Plots tab → gallery shows it,
   zoom/pan works, Save SVG downloads a vector file, Clear empties the store.
5. **Looker Explore:** Plots → Explore → pick `df`, drag `g`→Dimensions, `x`→Measures (avg),
   chart = bar → renders via Vega-Lite; "Copy as code" inserts Altair that reproduces it.
6. **Scale/robustness:** confirm `/explore/page` returns quickly on 100k rows and that a bad
   var name / non-DataFrame surfaces a clean error (no kernel desync).

## Notes / follow-ups
- Polars support is best-effort (`to_pandas()`); document if a dep is missing.
- Security: the GitHub PAT pasted in chat must be **revoked/rotated** (plus the prior
  2026-06-21 token); not used for this feature — pushing later will go through `gh auth login`.
