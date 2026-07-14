# PrismNote: Key Gaps Implementation Plan

## Context

Following the comprehensive design + accessibility audit and the Databricks competitive gap analysis, this plan addresses the highest-impact gaps in three groups:

1. **Accessibility / Safety (v1.0.3 critical)** — WCAG violations and data loss risk block enterprise adoption
2. **UX Clarity** — active state ambiguity and feature discoverability harm new-user experience
3. **Databricks Parity** — Execution Minimap and Drag-to-Reorder close the two remaining high-impact Databricks gaps (Display function is already scaffolded in Output.tsx/DataFrameView.tsx)

---

## Group 1: Accessibility & Safety

### 1a. `railBtn` — aria-pressed + active background

**File:** `frontend/src/App.tsx` (lines 279–293)

The `railBtn` helper has no ARIA semantics and the active state is visual-only (1px left bar). Fix both in one edit:

```tsx
const railBtn = (active: boolean, onClick: () => void, title: string, Icon: any, stop = false) => (
  <button
    aria-pressed={active}
    aria-label={title.split('  ')[0]}   // strip the "  ⌘E" shortcut hint
    onClick={(e) => { if (stop) e.stopPropagation(); onClick() }}
    title={title}
    className={`relative w-12 h-12 flex items-center justify-center transition-colors ${
      active ? 'pn-text bg-blue-500/10' : 'pn-faint hover:pn-text'
    }`}
  >
    {active && <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r prism-bar shadow-[0_0_10px_rgba(167,139,250,0.7)]" />}
    <Icon size={20} />
  </button>
)
```

### 1b. Color contrast tokens

**File:** `frontend/src/index.css`

- `.dark { --pn-faint: #5f6e85; }` → `#7a8697` (4.5:1 on dark bg)
- `:root { --pn-faint: #97a1b2; }` → `#7b8899` (4.5:1 on light bg)

### 1c. Focus outline — dual-ring fix

**File:** `frontend/src/index.css`

Current outline (#2563eb) is invisible on the blue rail/status bar. Replace with a high-contrast dual ring:
```css
:focus-visible {
  outline: 2px solid #60a5fa;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(11, 15, 23, 0.9);  /* dark halo for contrast on any bg */
}
```

### 1d. Modal ARIA semantics

**Files:** `SettingsModal.tsx`, `CommandPalette.tsx`, `KeyboardShortcutsModal.tsx`, `DataExplorer.tsx` (ExplorerPicker)

All four use plain `<div>` wrappers with no dialog semantics. Pattern to apply to each inner panel div:
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="UNIQUE-title-id"
  ...existing className...
>
  <h2 id="UNIQUE-title-id">...</h2>
```

For `ExplorerPicker` which uses `absolute inset-0` instead of a centered modal, add `role="dialog" aria-modal="true" aria-label="Data Explorer — choose a dataset"` on the root `div`.

### 1e. SettingsModal form labels

**File:** `frontend/src/components/SettingsModal.tsx`

The file has a `Row` helper that renders labels as plain `<div>`. For each `<input>` / `<select>` / `<input type="range">` in Settings, add a matching `id` attribute and update `Row` (or wrap inline) to use `<label htmlFor={id}>`. The existing `Input.tsx` component at `components/common/Input.tsx` already handles this correctly — use it for the endpoint/model/API-key text inputs.

### 1f. Data loss prevention

**File:** `frontend/src/App.tsx` + `frontend/src/hooks/useNotebook.ts`

Two changes:

**1. Call `saveNotebook` after structural mutations** (currently missing):
In `useNotebook.ts`, add `setTimeout(() => get().saveNotebook(), 500)` at the end of `addCell`, `deleteCell`, and `moveCell` (same pattern as `updateCell`).

**2. `beforeunload` safety net** in App.tsx:
```tsx
useEffect(() => {
  const handler = (e: BeforeUnloadEvent) => {
    const nb = (useNotebookStore.getState() as any).currentNotebook
    if (nb) { e.preventDefault(); e.returnValue = '' }
  }
  window.addEventListener('beforeunload', handler)
  return () => window.removeEventListener('beforeunload', handler)
}, [])
```

### 1g. Stagger responsive breakpoints

**File:** `frontend/src/App.tsx` (lines 78–98)

Current: NARROW=1000 collapses BOTH sidebars simultaneously. Replace with three thresholds:
```ts
const HIDE_AI    = 1400  // hide AI assistant first
const HIDE_FILES = 900   // then files panel
const TIGHT      = 700   // then bottom panel
```
Update the resize handler logic accordingly (three independent conditions, not two).

---

## Group 2: UX Clarity

### 2a. Data Explorer first-run hint

**File:** `frontend/src/App.tsx` (welcome screen, lines 406–434)

Add a subtle hint line below the two CTA buttons:
```tsx
<p className="mt-5 text-xs pn-faint">
  Tip — press <kbd className="px-1 py-0.5 rounded bg-white/10 font-mono">⌘E</kbd> anytime to explore data files, DataFrames, or run SQL.
</p>
```

---

## Group 3: Databricks Parity

### 3a. Execution Minimap

**New file:** `frontend/src/hooks/useCellExecution.ts`

Tiny Zustand store (no persistence, ephemeral UI state):
```ts
interface ExecEntry { state: 'running' | 'success' | 'error'; ms?: number }
interface CellExecutionStore {
  states: Record<string, ExecEntry>       // keyed by cell.id
  set: (id: string, e: ExecEntry) => void
  clear: (id: string) => void
}
export const useCellExecution = create<CellExecutionStore>(...)
```

**Modified file:** `frontend/src/components/Cell.tsx` — `handleRun`

After `await executeCell(cellIndex)`, check outputs from store for errors:
```ts
const handleRun = async () => {
  const { set: setExec } = useCellExecution.getState()
  setIsExecuting(true)
  setExec(cell.id, { state: 'running' })
  const t0 = Date.now()
  setLiveOut('')
  try {
    await executeCell(cellIndex)
    const freshCell = (useNotebookStore.getState() as any).currentNotebook?.cells[cellIndex]
    const hasErr = (freshCell?.outputs ?? []).some((o: any) => o.output_type === 'error')
    setExec(cell.id, { state: hasErr ? 'error' : 'success', ms: Date.now() - t0 })
  } catch {
    setExec(cell.id, { state: 'error', ms: Date.now() - t0 })
  } finally {
    setIsExecuting(false)
    setLiveOut('')
  }
}
```

**New file:** `frontend/src/components/ExecutionMinimap.tsx`

Narrow (w-5) column, fixed to the right inside the Notebook scroll area. One dot per cell:
- `⚪ bg-slate-600` — never run
- `🔵 bg-blue-400 animate-pulse` — running
- `🟢 bg-emerald-400` — success
- `🔴 bg-red-400` — error

Click → `scrollIntoView` on `data-cell-index`. Tooltip shows cell number + execution time. Cells without execution state show as dots; running cells pulse.

**Modified file:** `frontend/src/components/Notebook.tsx`

Change the scrollable area wrapper from:
```tsx
<div className="flex-1 overflow-y-auto p-4 min-w-0">
```
to a flex row with the minimap:
```tsx
<div className="flex-1 flex overflow-hidden">
  <div className="flex-1 overflow-y-auto p-4 min-w-0">
    ...cells...
  </div>
  <ExecutionMinimap cells={currentNotebook.cells} />
</div>
```

### 3b. Drag-to-Reorder Cells

**Modified file:** `frontend/src/hooks/useNotebook.ts`

Add `reorderCell(fromIdx: number, toIdx: number)` action:
```ts
reorderCell: (fromIdx, toIdx) => {
  set((state) => {
    if (!state.currentNotebook) return state
    if (fromIdx === toIdx) return state
    const cells = [...state.currentNotebook.cells]
    const [cell] = cells.splice(fromIdx, 1)
    cells.splice(toIdx, 0, cell)
    return {
      currentNotebook: { ...state.currentNotebook, cells },
      selectedCellIndex: toIdx,
    }
  })
  setTimeout(() => get().saveNotebook(), 500)
},
```

Also update `NotebookStore` interface to include `reorderCell`.

**Modified file:** `frontend/src/components/Cell.tsx`

Import `GripVertical` from lucide-react. Add drag handle before the collapse chevron in the header:
```tsx
<div
  className="cursor-grab active:cursor-grabbing p-1 rounded hover:bg-slate-700 pn-faint hover:pn-text"
  title="Drag to reorder"
  onMouseDown={(e) => e.stopPropagation()}  // prevent cell selection
  data-drag-handle
>
  <GripVertical size={14} />
</div>
```

The drag state itself is managed in Notebook.tsx (see below) — Cell.tsx only contributes the visual handle.

**Modified file:** `frontend/src/components/Notebook.tsx`

Use HTML5 native drag-and-drop (no new dependencies). Track drag state in Notebook with `useState`:
```ts
const [dragFrom, setDragFrom] = useState<number | null>(null)
const [dragOver, setDragOver] = useState<number | null>(null)
```

Wrap each cell container with drag props:
```tsx
<div
  key={cell.id}
  data-cell-index={idx}
  draggable
  onDragStart={() => setDragFrom(idx)}
  onDragEnd={() => { setDragFrom(null); setDragOver(null) }}
  onDragOver={(e) => { e.preventDefault(); setDragOver(idx) }}
  onDrop={(e) => {
    e.preventDefault()
    if (dragFrom !== null && dragFrom !== idx) reorderCell(dragFrom, idx)
    setDragFrom(null); setDragOver(null)
  }}
  className={`... ${dragFrom === idx ? 'opacity-40' : ''} ${dragOver === idx && dragFrom !== idx ? 'border-t-2 border-blue-500' : ''}`}
>
```

---

## File Change Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `App.tsx` | Modify | railBtn aria-pressed+active-bg, beforeunload, stagger breakpoints, explorer hint |
| `index.css` | Modify | --pn-faint contrast, :focus-visible dual-ring |
| `SettingsModal.tsx` | Modify | role="dialog" + form labels |
| `CommandPalette.tsx` | Modify | role="dialog" aria-modal aria-labelledby |
| `KeyboardShortcutsModal.tsx` | Modify | role="dialog" aria-modal aria-labelledby |
| `DataExplorer.tsx` | Modify | ExplorerPicker: role="dialog" aria-label |
| `useNotebook.ts` | Modify | saveNotebook after addCell/deleteCell/moveCell; add reorderCell |
| `Cell.tsx` | Modify | handleRun tracks execution; GripVertical drag handle |
| `Notebook.tsx` | Modify | drag-and-drop state; ExecutionMinimap column |
| `useCellExecution.ts` | **New** | Ephemeral execution state Zustand store |
| `ExecutionMinimap.tsx` | **New** | Status dot column with click-to-scroll |

---

## Verification

1. **Accessibility**: After implementation, toggle Files panel with keyboard (Tab + Space), verify screen reader announces "Files, pressed/not pressed". Open Settings (⌘,), verify focus trap works and dialog is announced.
2. **Contrast**: Use browser DevTools → Accessibility → check `--pn-faint` elements report ≥ 4.5:1.
3. **Focus ring**: Tab to a rail button on blue background; verify ring is visible (light blue + dark shadow).
4. **Beforeunload**: Edit a cell → close browser tab → confirm browser warning appears.
5. **Breakpoints**: Resize viewport to 1350px → AI panel collapses, Files stays. Resize to 850px → Files collapses too.
6. **Minimap**: Run a cell → dot turns blue (running) → then green/red (done/error). Click dot → scrolls to cell.
7. **Drag**: Drag handle grip on cell → drag to new position → cell reorders → dot counts stay correct.
8. **Explorer hint**: Open with no notebook; verify tip line "press ⌘E anytime…" visible at bottom of welcome screen.
