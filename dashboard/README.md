# Model Predictive Control — Study Dashboard

A clean, client-side study dashboard for *Model Predictive Control: Theory,
Computation, and Design* (Rawlings, Mayne & Diehl, 2nd ed.), built with
Svelte 5 + Vite. Everything runs in the browser; progress, notes, highlights and
solved challenges are saved in `localStorage`.

## Layout
- **Left sidebar** — 8 chapters, each expandable to its numbered sections (N.M)
  for one-click jumps. Shows per-chapter read progress and a ✓ when complete.
  Collapsible (on mobile it becomes a slide-in drawer).
- **Top bar** — four tabs: Reader · Exercises · Challenges · Notes. The `⋯` menu
  marks a chapter complete or resets its progress.

## Tabs
- **Reader** — the book PDF split per chapter, continuous scroll, zoom, page jump.
  Tracks current/furthest page (read %). Select text to **highlight** (5 colors)
  or **save as a note**.
- **Exercises** — just the exercises pages of the chapter as a focused PDF.
- **Challenges** — LeetCode-style Python problems set in each chapter's context
  (35 total: LQR/Riccati, MPC cost & stability, robust tubes, Kalman/MHE,
  distributed iterations, explicit PWA laws, RK4/shooting). Real Python runs
  in-browser via **Pyodide** against hidden test cases; syntax-highlighted editor
  (CodeMirror), examples, and a Solution tab.
- **Notes** — all highlights/notes for the chapter; edit, delete, jump to the page.

## Run it
```bash
cd dashboard
npm install
npm run dev      # open the printed http://localhost:5173
```
The per-chapter book PDFs (`public/book/`) are generated from the source PDF at the
repo root and committed, so it works immediately.

## Regenerating data (only if source files change)
```bash
npm run split       # MPC book PDF -> public/book/chNN.pdf + chNN-ex.pdf
npm run manifest    # chapter table + parse section list from the Contents pages
npm run challenges  # author challenges -> challenges.json (needs python3)
npm run data        # all of the above
```

## Notes
- Chapter/exercise page ranges are hard-coded from the printed table of contents
  (physical PDF page = book page + 48). The PDF has no embedded outline, so the
  per-chapter section list is parsed from the Contents pages at build time.
- Challenge expected outputs are computed from pure-python reference solutions at
  authoring time, so they are guaranteed correct.
