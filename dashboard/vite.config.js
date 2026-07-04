import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ command }) => ({
  // "/" for the dev server; the GitHub Pages project subpath for the build.
  base: command === 'build' ? '/Model-Predictive-Control/' : '/',
  plugins: [svelte()],
  worker: { format: 'es' },
  optimizeDeps: { exclude: ['pdfjs-dist'] },
  // per-chapter book PDFs live in public/ and are committed.
  build: { copyPublicDir: true },
}));
