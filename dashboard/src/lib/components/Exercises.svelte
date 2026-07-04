<script>
  import PdfViewer from './PdfViewer.svelte';
  import { store, persist } from '../stores/store.svelte.js';

  let { chapter } = $props();
  let page = $state((store.exercises[chapter.id]?.page) || 1);
  let total = $state(0);

  function save(p) {
    const e = (store.exercises[chapter.id] ||= { page: 1, furthest: 1, total: 0 });
    e.page = p;
    if (p > (e.furthest || 0)) e.furthest = p;
    e.total = total;
    persist();
  }
  function onload({ numPages }) { total = numPages; save(page); }
  function onpagechange(p) { save(p); }
</script>

<div class="ex">
  {#if !chapter.exPdf}
    <div class="empty">No exercises for this chapter.</div>
  {:else}
    <div class="note muted">Exercises from Chapter {chapter.n} (book pages {chapter.ex}–{chapter.end}).</div>
    <div class="vwrap">
      <PdfViewer url={chapter.exPdf} bind:page {onload} {onpagechange} />
    </div>
  {/if}
</div>

<style>
  .ex { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .note { padding: 8px 16px; border-bottom: 1px solid var(--border); background: var(--surface); font-size: 12.5px; }
  .vwrap { flex: 1; min-height: 0; }
  .empty { flex: 1; display: grid; place-items: center; color: var(--text-3); }
</style>
