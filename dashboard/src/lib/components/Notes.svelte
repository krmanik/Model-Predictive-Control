<script>
  import { store, notesFor, addNote, removeNote, updateNote, readerState, persist } from '../stores/store.svelte.js';

  let { chapter } = $props();
  let filter = $state('all');   // all | note | highlight
  let draft = $state('');

  const items = $derived(
    (store.notes[chapter.id] || []).filter(n => filter === 'all' ? true : n.type === filter)
  );

  function addFree() {
    const t = draft.trim();
    if (!t) return;
    addNote(chapter.id, { type: 'note', text: '', page: readerState(chapter.id).page || 1, color: '#c5cae9', body: t });
    draft = '';
  }
  function gotoPage(p) {
    readerState(chapter.id).page = p;
    store.ui.tab = 'reader';
    persist();
  }
  const fmtDate = (ts) => new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
</script>

<div class="notes">
  <div class="head">
    <div class="filters">
      {#each [['all','All'],['highlight','Highlights'],['note','Notes']] as [v,l]}
        <button class="f" class:active={filter === v} onclick={() => filter = v}>{l}</button>
      {/each}
    </div>
    <span class="muted">{(store.notes[chapter.id] || []).length} saved</span>
  </div>

  <div class="add">
    <textarea bind:value={draft} placeholder="Write a quick note for this chapter…" rows="2"
      onkeydown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) addFree(); }}></textarea>
    <button class="btn primary" onclick={addFree} disabled={!draft.trim()}>Add note</button>
  </div>

  <div class="scroll">
    {#if items.length === 0}
      <div class="empty">
        <p>No {filter === 'all' ? 'notes or highlights' : filter + 's'} yet.</p>
        <p class="muted">Select text in the Reader to highlight it or save it as a note.</p>
      </div>
    {:else}
      {#each items as n (n.id)}
        <div class="card">
          <div class="card-top">
            <span class="dot" style="background:{n.color}"></span>
            <span class="tag">{n.type}</span>
            {#if n.page}<button class="page-link" onclick={() => gotoPage(n.page)}>page {n.page} ↗</button>{/if}
            <span class="muted date">{fmtDate(n.ts)}</span>
            <button class="del" onclick={() => removeNote(chapter.id, n.id)} title="Delete">Delete</button>
          </div>
          {#if n.text}<blockquote>{n.text}</blockquote>{/if}
          <textarea
            class="body"
            value={n.body}
            placeholder="Add your comment…"
            rows="2"
            oninput={(e) => updateNote(chapter.id, n.id, { body: e.target.value })}
          ></textarea>
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .notes { display: flex; flex-direction: column; height: 100%; min-height: 0; max-width: 820px; margin: 0 auto; width: 100%; }
  .head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px 10px; }
  .filters { display: flex; gap: 4px; background: var(--surface-2); padding: 3px; border-radius: 8px; }
  .f { border: none; background: transparent; padding: 5px 12px; border-radius: 6px; font-weight: 550; color: var(--text-2); }
  .f.active { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }

  .add { display: flex; gap: 8px; padding: 0 18px 12px; border-bottom: 1px solid var(--border); }
  .add textarea { flex: 1; resize: vertical; }
  textarea {
    font-family: inherit; font-size: 13.5px; color: var(--text);
    border: 1px solid var(--border-strong); border-radius: 8px; padding: 8px 10px;
    background: var(--bg); line-height: 1.45;
  }
  textarea:focus { outline: 2px solid var(--accent-soft); border-color: var(--accent); }

  .scroll { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 18px 28px; }
  .empty { text-align: center; padding: 60px 20px; color: var(--text-2); }
  .empty p { margin: 6px 0; }

  .card { border: 1px solid var(--border); background: var(--surface); border-radius: var(--radius); padding: 12px 14px; margin-bottom: 12px; box-shadow: var(--shadow); }
  .card-top { display: flex; align-items: center; gap: 9px; margin-bottom: 8px; }
  .dot { width: 11px; height: 11px; border-radius: 50%; flex: none; border: 1px solid rgba(0,0,0,.12); }
  .tag { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--text-3); font-weight: 600; }
  .page-link { border: none; background: var(--surface-2); padding: 2px 8px; border-radius: 20px; font-size: 12px; color: var(--accent-text); font-weight: 500; }
  .page-link:hover { background: var(--accent-soft); }
  .date { margin-left: auto; font-size: 12px; }
  .del { border: none; background: transparent; color: var(--text-3); font-size: 12px; padding: 2px 6px; border-radius: 6px; }
  .del:hover { color: var(--danger); background: var(--surface-2); }
  blockquote { margin: 0 0 8px; padding: 7px 11px; border-left: 3px solid var(--border-strong); background: var(--bg); border-radius: 0 6px 6px 0; color: var(--text); font-size: 13px; }
  .body { width: 100%; resize: vertical; }
</style>
