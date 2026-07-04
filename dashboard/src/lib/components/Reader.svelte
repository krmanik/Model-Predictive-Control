<script>
  import { untrack } from 'svelte';
  import PdfViewer from './PdfViewer.svelte';
  import { store, setReaderPage, readerProgress, addNote, persist } from '../stores/store.svelte.js';

  let { chapter } = $props();

  const rs = $derived(store.reader[chapter.id] ?? { page: 1, furthest: 1, scale: 0 });

  // scroll target coming from the sidebar (section/chapter click) for THIS chapter
  const goto = $derived(store.ui.readerGoto?.ch === chapter.id ? store.ui.readerGoto : null);
  let page = $state(1);
  let total = $state(0);
  let pending = $state(null);   // { text, page, rects }

  // The Reader is not remounted on chapter change (to avoid a reload flash), so
  // re-sync local state when the chapter — or a progress reset (nonce) — changes.
  $effect(() => {
    const id = chapter.id;
    store.ui.nonce;                       // re-sync after a reset
    const g = store.ui.readerGoto;        // re-sync on a sidebar jump
    untrack(() => {
      page = (g && g.ch === id ? g.page : (store.reader[id]?.page ?? 1)) || 1;
      pending = null;
    });
  });

  const COLORS = ['#ffe79a', '#a8e6cf', '#ffd3b6', '#c5cae9', '#f8bbd0'];

  const highlights = $derived((store.notes[chapter.id] || []).filter(n => n.type === 'highlight'));

  function onload({ numPages }) {
    total = numPages;
    setReaderPage(chapter.id, page, numPages);
  }
  function onpagechange(p) {
    setReaderPage(chapter.id, p, total);
  }
  function onselect(d) { pending = d; }

  function makeHighlight(color) {
    addNote(chapter.id, { type: 'highlight', text: pending.text, page: pending.page, rects: pending.rects, color, body: '' });
    pending = null;
    window.getSelection()?.removeAllRanges();
  }
  function makeNote() {
    addNote(chapter.id, { type: 'note', text: pending.text, page: pending.page, rects: pending.rects, color: COLORS[0], body: '' });
    pending = null;
    window.getSelection()?.removeAllRanges();
  }
  function copyText() { navigator.clipboard?.writeText(pending.text); pending = null; }
  function dismiss() { pending = null; window.getSelection()?.removeAllRanges(); }

  function gotoNotes() { store.ui.tab = 'notes'; persist(); }

  const pct = $derived(Math.round(readerProgress(chapter.id) * 100));
</script>

<div class="reader">
  {#if pending}
    <div class="sel-bar">
      <span class="sel-text">“{pending.text.length > 80 ? pending.text.slice(0, 80) + '…' : pending.text}”</span>
      <div class="sel-actions">
        <span class="lbl muted">Highlight:</span>
        {#each COLORS as c}
          <button class="swatch" style="background:{c}" onclick={() => makeHighlight(c)} aria-label="highlight"></button>
        {/each}
        <button class="btn" onclick={makeNote}>＋ Note</button>
        <button class="btn" onclick={copyText}>Copy</button>
        <button class="btn icon" onclick={dismiss} title="Dismiss">✕</button>
      </div>
    </div>
  {/if}

  <div class="bar">
    <div class="prog-wrap">
      <div class="prog-bar"><span style="width:{pct}%"></span></div>
      <span class="muted">{pct}% read · furthest p{rs.furthest}{total ? ` / ${total}` : ''}</span>
    </div>
  </div>

  <div class="vwrap">
    <PdfViewer
      url={chapter.pdf}
      bind:page
      {goto}
      ongoto={() => { if (store.ui.readerGoto) { store.ui.readerGoto = null; persist(); } }}
      enableSelection
      {highlights}
      {onload}
      {onpagechange}
      {onselect}
      onhighlightclick={gotoNotes}
    />
  </div>
</div>

<style>
  .reader { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .bar { padding: 8px 16px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .prog-wrap { display: flex; align-items: center; gap: 12px; }
  .prog-bar { flex: 1; height: 5px; background: var(--surface-2); border-radius: 4px; overflow: hidden; max-width: 360px; }
  .prog-bar span { display: block; height: 100%; background: var(--accent); transition: width .2s; }
  .prog-wrap .muted { font-size: 12.5px; white-space: nowrap; }
  .vwrap { flex: 1; min-height: 0; }

  .sel-bar {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    padding: 9px 16px; background: var(--accent-soft);
    border-bottom: 1px solid var(--border);
  }
  .sel-text { font-style: italic; color: var(--accent-text); flex: 1; min-width: 160px; font-size: 13px; }
  .sel-actions { display: flex; align-items: center; gap: 6px; }
  .lbl { font-size: 12px; }
  .swatch { width: 20px; height: 20px; border-radius: 50%; border: 1px solid rgba(0,0,0,.15); cursor: pointer; }
  .swatch:hover { transform: scale(1.12); }
</style>
