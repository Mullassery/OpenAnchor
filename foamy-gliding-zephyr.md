# PrismNote — Implementation Plan

## Context
Build PrismNote: a modern, Deepnote-quality OSS data science notebook with a Rust backend and Python kernel support. Installable via pip, uv, and curl. Targets the key gaps in JupyterLab/Colab: slow UI, no reproducibility, no AI, cloud lock-in.

## Architecture

```
prismnote/
├── Cargo.toml                  # Rust workspace
├── crates/
│   └── server/                 # Axum HTTP + WebSocket server
│       ├── src/
│       │   ├── main.rs
│       │   ├── api/            # REST endpoints (notebooks CRUD)
│       │   ├── kernel/         # Jupyter ZMQ kernel manager
│       │   ├── ws/             # WebSocket handler (cell execution msgs)
│       │   └── files/          # .ipynb read/write
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Notebook.tsx
│   │   │   ├── Cell.tsx        # Code + Markdown cell
│   │   │   ├── Output.tsx      # Rich output (HTML, images, tables)
│   │   │   ├── Sidebar.tsx
│   │   │   └── Toolbar.tsx
│   │   ├── hooks/
│   │   │   ├── useKernel.ts    # WebSocket kernel state
│   │   │   └── useNotebook.ts  # Notebook state management
│   │   ├── styles/             # Tailwind + custom design tokens
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── python/                     # pip/uv installable package
│   ├── pyproject.toml
│   ├── prismnote/
│   │   ├── __init__.py
│   │   ├── __main__.py         # python -m prismnote
│   │   └── _cli.py             # downloads binary, starts server
│   └── MANIFEST.in
└── install.sh                  # curl installer script
```

## Stack
- **Backend**: Rust + Axum + Tokio + Tower
- **Kernel protocol**: Jupyter ZMQ via `zeromq` crate (connects to ipykernel)
- **Frontend**: React 18 + TypeScript + Vite + Monaco Editor + Tailwind CSS
- **Notebook format**: .ipynb (nbformat v4) — full Jupyter compatibility
- **AI**: Claude API (claude-haiku-4-5) for code completions/explanations
- **Python package**: Pure Python wrapper — downloads platform binary on first run

## Installation Methods

### pip / uv
`prismnote/pyproject.toml` declares a `prismnote` CLI entry point.  
On first `prismnote` run, `_cli.py` downloads the correct platform binary from GitHub Releases, caches at `~/.prismnote/bin/`, and exec's it.

### curl
`install.sh` — detects OS/arch, downloads binary from GitHub Releases, installs to `/usr/local/bin/prismnote`.

## MVP Features (all in v1)
1. **Code cells** — Python via Jupyter kernel protocol (ZMQ → ipykernel)
2. **Markdown cells** — rendered with syntax highlighting
3. **Rich output** — text, HTML, images (PNG), pandas DataFrames (HTML table), matplotlib inline
4. **AI assistance** — Claude API: explain cell, suggest fix, complete code
5. **.ipynb import/export** — full nbformat v4 round-trip
6. **Modern UI** — dark/light theme, Deepnote-quality polish, Monaco editor

## UI Design Principles
- Clean sidebar (file tree) + main notebook area + right panel (AI)
- Cells have: run button, type indicator, execution count, status ring
- Output area with collapsible sections
- Dark theme default, toggleable light theme
- Keyboard shortcuts: Shift+Enter (run), Ctrl+Enter (run in place), B/A (insert cell), DD (delete)

## Implementation Steps
1. Scaffold Rust workspace + Axum server with static file serving
2. Build .ipynb parser/writer (serde_json)
3. Implement Jupyter kernel manager (ZMQ handshake, execute_request/reply)
4. WebSocket bridge: browser ↔ Rust ↔ Jupyter kernel
5. REST API: GET/POST/DELETE notebooks, list files
6. Build React frontend with Vite
7. Monaco editor integration for code cells
8. Markdown cell with @uiw/react-markdown-preview
9. Output renderer (text, HTML, image/png, application/vnd.dataresource+json)
10. AI panel (Claude API calls via Rust proxy)
11. Tailwind design system (dark/light, typography, colors)
12. Python package wrapper (_cli.py downloads binary)
13. install.sh curl script
14. Build script that bundles frontend into Rust binary (include_dir!)

## Verification
- `cargo build --release` succeeds
- `pip install -e ./python && prismnote` opens browser
- `uv tool install ./python && prismnote` works
- `bash install.sh` installs binary
- Open .ipynb, run Python cell, see output
- Switch dark/light theme
- AI panel explains a cell
