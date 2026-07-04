# Model Predictive Control

Study materials for *Model Predictive Control: Theory, Computation, and Design*
by Rawlings, Mayne & Diehl (2nd edition).

**Live demo:** https://krmanik.github.io/Model-Predictive-Control/

## Contents
- **`dashboard/`** — an interactive, browser-based study dashboard: a per-chapter
  PDF reader with highlights and notes, focused exercise pages, and in-browser
  Python coding challenges. Progress is saved locally.
- **`MPC-book-2nd-edition-1st-printing.pdf`** — the source text the dashboard is
  built from.

## Getting started
```bash
cd dashboard
npm install
npm run dev
```
Then open the printed local URL. See [`dashboard/README.md`](dashboard/README.md)
for the full feature tour and the data-generation pipeline.

## Building / hosting
`npm run build` (in `dashboard/`) produces a static bundle in `dashboard/dist/`,
hostable on GitHub Pages or any static host. The
[deploy workflow](.github/workflows/deploy.yml) builds and publishes to GitHub
Pages on every push to `main` that touches `dashboard/**`.
