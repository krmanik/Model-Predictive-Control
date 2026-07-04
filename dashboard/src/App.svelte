<script>
  import manifest from './lib/data/manifest.json';
  import { store, persist } from './lib/stores/store.svelte.js';
  import Sidebar from './lib/components/Sidebar.svelte';
  import TopBar from './lib/components/TopBar.svelte';
  import Reader from './lib/components/Reader.svelte';
  import Exercises from './lib/components/Exercises.svelte';
  import Challenges from './lib/components/Challenges.svelte';
  import Notes from './lib/components/Notes.svelte';

  const chapters = manifest.chapters;
  const chapter = $derived(chapters.find(c => c.id === store.ui.chapter) ?? chapters[0]);

  const tabs = [
    { id: 'reader', label: 'Reader' },
    { id: 'exercises', label: 'Exercises' },
    { id: 'challenges', label: 'Challenges' },
    { id: 'notes', label: 'Notes' },
  ];

  function tabAvailable(id, c) {
    if (id === 'reader' || id === 'notes' || id === 'challenges') return !!c.pdf;
    if (id === 'exercises') return !!c.exPdf;
    return false;
  }

  // if the active tab isn't available for this chapter, fall back to the first that is
  $effect(() => {
    if (!tabAvailable(store.ui.tab, chapter)) {
      const next = tabs.find(t => tabAvailable(t.id, chapter));
      if (next) { store.ui.tab = next.id; persist(); }
    }
  });
</script>

<div class="app" class:collapsed={store.ui.collapsed}>
  <Sidebar {chapters} />
  <main class="main">
    <TopBar {chapter} {tabs} />
    <div class="content">
      <!-- Reader stays mounted across chapter changes so the PDF swaps in place
           (no remount → no white flash). It syncs on chapter/nonce internally. -->
      <div class="pane" class:hidden={store.ui.tab !== 'reader'}>
        <Reader {chapter} />
      </div>
      {#if store.ui.tab !== 'reader'}
        {#key store.ui.chapter + ':' + (store.ui.nonce ?? 0)}
          {#if store.ui.tab === 'exercises'}
            <Exercises {chapter} />
          {:else if store.ui.tab === 'challenges'}
            <Challenges {chapter} />
          {:else if store.ui.tab === 'notes'}
            <Notes {chapter} />
          {/if}
        {/key}
      {/if}
    </div>
  </main>
</div>

<style>
  .app {
    display: grid;
    grid-template-columns: var(--sidebar-w) 1fr;
    grid-template-rows: minmax(0, 1fr);
    height: 100%;
    transition: grid-template-columns .18s ease;
  }
  .app.collapsed { grid-template-columns: 66px 1fr; }
  @media (max-width: 860px) {
    .app, .app.collapsed { grid-template-columns: 1fr; }
  }
  .main {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
    height: 100%;
  }
  .content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    position: relative;
  }
  .pane { height: 100%; min-height: 0; }
  .pane.hidden { display: none; }
</style>
