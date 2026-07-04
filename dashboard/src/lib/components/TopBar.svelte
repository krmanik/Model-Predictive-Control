<script>
  import { store, persist, markChapterComplete, resetChapterProgress, isChapterComplete } from '../stores/store.svelte.js';
  let { chapter, tabs } = $props();

  let menuOpen = $state(false);

  function counts(id) {
    if (id === 'notes') return (store.notes[chapter.id] || []).length;
    return 0;
  }
  function disabled(id) {
    if (id === 'reader' || id === 'notes' || id === 'challenges') return !chapter.pdf;
    if (id === 'exercises') return !chapter.exPdf;
    return false;
  }
  function pick(id) { if (disabled(id)) return; store.ui.tab = id; persist(); }

  function complete() { markChapterComplete(chapter.id); menuOpen = false; }
  function reset() {
    if (confirm(`Reset reading and exercise progress for "${chapter.title}"?\n\nYour notes and solved challenges are kept.`)) {
      resetChapterProgress(chapter.id, chapter);
    }
    menuOpen = false;
  }
  const done = $derived(isChapterComplete(chapter.id));
</script>

<header class="topbar">
  <button class="btn icon burger" onclick={() => { store.ui.mobileNav = true; persist(); }} title="Menu">☰</button>

  <div class="ch-head">
    <span class="kicker">Chapter {chapter.n}{#if done} · Completed{/if}</span>
    <h1>{chapter.title}</h1>
  </div>

  <nav class="tabs">
    {#each tabs as t}
      {@const n = counts(t.id)}
      <button class="tab" class:active={store.ui.tab === t.id} disabled={disabled(t.id)} onclick={() => pick(t.id)}>
        {t.label}{#if n}<span class="count">{n}</span>{/if}
      </button>
    {/each}
  </nav>

  <div class="menu-wrap">
    <button class="btn icon" onclick={() => menuOpen = !menuOpen} title="Chapter options">⋯</button>
    {#if menuOpen}
      <div class="backdrop" onclick={() => menuOpen = false}></div>
      <div class="menu">
        <button class="mi" onclick={complete} disabled={done}>{done ? 'Completed' : 'Mark chapter complete'}</button>
        <button class="mi danger" onclick={reset}>Reset chapter progress…</button>
      </div>
    {/if}
  </div>
</header>

<style>
  .topbar { position: relative; z-index: 20; display: flex; align-items: center; gap: 14px; padding: 10px 16px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .burger { display: none; }
  .ch-head { min-width: 0; }
  .kicker { font-size: 11px; text-transform: uppercase; letter-spacing: .09em; color: var(--accent-text); font-weight: 700; white-space: nowrap; }
  h1 { margin: 1px 0 0; font-size: 18px; font-weight: 650; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .tabs { display: flex; gap: 2px; flex: none; margin-left: auto; background: var(--surface-2); padding: 3px; border-radius: 9px; max-width: 100%; overflow-x: auto; }
  .tab { border: none; background: transparent; padding: 6px 13px; border-radius: 6px; font-weight: 550; color: var(--text-2); display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; transition: background .12s, color .12s; }
  .tab:hover:not(:disabled) { color: var(--text); }
  .tab.active { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }
  .tab:disabled { opacity: .38; cursor: not-allowed; }
  .count { font-size: 11px; font-weight: 600; background: var(--border-strong); color: var(--text-2); padding: 0 5px; border-radius: 10px; min-width: 16px; text-align: center; }
  .tab.active .count { background: var(--accent); color: #fff; }

  .menu-wrap { position: relative; flex: none; }
  .backdrop { position: fixed; inset: 0; z-index: 30; }
  .menu { position: absolute; right: 0; top: calc(100% + 6px); z-index: 31; background: var(--surface); border: 1px solid var(--border-strong); border-radius: var(--radius); box-shadow: var(--shadow); padding: 5px; min-width: 220px; }
  .mi { display: block; width: 100%; text-align: left; border: none; background: transparent; padding: 9px 11px; border-radius: 7px; font-size: 13px; color: var(--text); }
  .mi:hover:not(:disabled) { background: var(--surface-2); }
  .mi:disabled { color: var(--text-3); }
  .mi.danger { color: var(--danger); }

  @media (max-width: 860px) {
    .burger { display: inline-flex; }
    .ch-head h1 { font-size: 15px; }
    .kicker { font-size: 10px; }
    .tabs { width: 100%; order: 3; margin-left: 0; }
    .topbar { flex-wrap: wrap; gap: 10px; }
  }
</style>
