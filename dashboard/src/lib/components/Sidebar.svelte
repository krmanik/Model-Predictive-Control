<script>
  import { store, chapterProgress, isChapterComplete, persist, exportData, importData } from '../stores/store.svelte.js';
  let { chapters } = $props();

  let fileInput = $state(null);
  function doExport() {
    const blob = new Blob([exportData()], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `mr-dashboard-progress-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
  function doImport(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      try { importData(String(r.result)); location.reload(); }
      catch { alert('Invalid backup file.'); }
    };
    r.readAsText(f);
  }

  let isMobile = $state(typeof matchMedia !== 'undefined' && matchMedia('(max-width: 860px)').matches);
  $effect(() => {
    if (typeof matchMedia === 'undefined') return;
    const mq = matchMedia('(max-width: 860px)');
    const h = (e) => isMobile = e.matches;
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  });
  const collapsed = $derived(store.ui.collapsed && !isMobile);

  // Ask the reader to scroll to {page, y}. A bumped seq re-triggers even for the
  // same target; the chapter itself only remounts when the PDF changes (App key).
  let seq = 0;
  function gotoReader(chId, page, y) {
    store.ui.chapter = chId;
    store.ui.tab = 'reader';
    store.ui.readerGoto = { ch: chId, page, y: y ?? null, seq: ++seq };
    store.ui.mobileNav = false;
    persist();
  }

  function select(id) {
    // plain chapter click → move to the start of that chapter
    gotoReader(id, 1, 0);
  }
  function toggle() { store.ui.collapsed = !store.ui.collapsed; persist(); }
  function closeMobile() { store.ui.mobileNav = false; persist(); }

  // section (2.1, 2.2, …) expand/jump
  let expanded = $state({});   // chId -> bool (explicit override; active chapter auto-expands)
  const isExpanded = (id) => expanded[id] ?? (store.ui.chapter === id);
  function toggleSections(e, id) { e.stopPropagation(); expanded[id] = !isExpanded(id); }

  // jump the reader to a section's page and show it
  function openSection(ch, sec) {
    expanded[ch.id] = true;
    gotoReader(ch.id, sec.page, sec.y);
  }

  // subsection (N.M.K) expand/jump — keyed by "chId:secNum"
  let secOpen = $state({});
  const isSecOpen = (chId, num) => !!secOpen[`${chId}:${num}`];
  function toggleSubs(e, chId, num) { e.stopPropagation(); secOpen[`${chId}:${num}`] = !isSecOpen(chId, num); }
  function openSub(ch, sec, sub) {
    expanded[ch.id] = true;
    secOpen[`${ch.id}:${sec.num}`] = true;
    gotoReader(ch.id, sub.page, sub.y);
  }

  // which section the reader is currently sitting in (for highlight)
  function currentSection(ch) {
    if (store.ui.chapter !== ch.id || !ch.sections?.length) return null;
    const p = store.reader[ch.id]?.page ?? 1;
    let cur = null;
    for (const s of ch.sections) { if (s.page <= p) cur = s; else break; }
    return cur?.num ?? null;
  }
</script>

{#if store.ui.mobileNav}
  <div class="m-backdrop" onclick={closeMobile}></div>
{/if}

<aside class="sidebar" class:collapsed class:mobile-open={store.ui.mobileNav}>
  <div class="brand">
    <div class="logo">MPC</div>
    {#if !collapsed}
      <div class="titles">
        <div class="t1">Model Predictive Control</div>
        <div class="t2">Study Dashboard</div>
      </div>
    {/if}
    <button class="toggle" onclick={toggle} title={collapsed ? 'Expand' : 'Collapse'}>{collapsed ? '»' : '«'}</button>
  </div>

  <nav class="nav">
    {#if !collapsed}<div class="nav-label">Chapters</div>{/if}
    {#each chapters as ch}
      {@const active = store.ui.chapter === ch.id}
      {@const prog = chapterProgress(ch)}
      {@const done = isChapterComplete(ch.id)}
      {@const hasSecs = !collapsed && ch.sections?.length > 0}
      {@const open = hasSecs && isExpanded(ch.id)}
      <button class="chap" class:active onclick={() => select(ch.id)} title={ch.title}>
        <span class="num" class:done>{ch.id === 'capstone' ? 'C' : ch.n}</span>
        {#if !collapsed}
          <span class="name">{ch.title}</span>
          {#if done}<span class="badge done">Done</span>{:else if prog > 0}<span class="badge">{Math.round(prog * 100)}%</span>{/if}
          {#if hasSecs}
            <span class="chev" class:open onclick={(e) => toggleSections(e, ch.id)}
                  role="button" tabindex="-1" title={open ? 'Hide sections' : 'Show sections'}>›</span>
          {/if}
        {/if}
        {#if prog > 0}<span class="prog" style="width:{prog * 100}%"></span>{/if}
      </button>
      {#if open}
        {@const curSec = currentSection(ch)}
        <div class="secs">
          {#each ch.sections as sec}
            {@const hasSubs = sec.subs?.length > 0}
            {@const subsOpen = hasSubs && isSecOpen(ch.id, sec.num)}
            <button class="sec" class:active={sec.num === curSec} onclick={() => openSection(ch, sec)} title={sec.title}>
              <span class="snum">{sec.num}</span>
              <span class="sname">{sec.title}</span>
              {#if hasSubs}
                <span class="chev sub" class:open={subsOpen} onclick={(e) => toggleSubs(e, ch.id, sec.num)}
                      role="button" tabindex="-1" title={subsOpen ? 'Hide subsections' : 'Show subsections'}>›</span>
              {/if}
            </button>
            {#if subsOpen}
              <div class="subs">
                {#each sec.subs as sub}
                  <button class="sub-item" onclick={() => openSub(ch, sec, sub)} title={sub.title}>
                    <span class="snum">{sub.num}</span>
                    <span class="sname">{sub.title}</span>
                  </button>
                {/each}
              </div>
            {/if}
          {/each}
        </div>
      {/if}
    {/each}
  </nav>

  {#if !collapsed}
    <div class="foot">
      <div class="backup">
        <button class="bk" onclick={doExport}>Export progress</button>
        <button class="bk" onclick={() => fileInput.click()}>Import</button>
        <input type="file" accept="application/json" bind:this={fileInput} onchange={doImport} hidden />
      </div>
      <div class="cite">Rawlings, Mayne &amp; Diehl · 2nd ed.</div>
    </div>
  {/if}
</aside>

<style>
  .sidebar { background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; height: 100%; overflow: hidden; }
  .brand { display: flex; align-items: center; gap: 11px; padding: 16px 14px; border-bottom: 1px solid var(--border); }
  .logo { width: 36px; height: 36px; flex: none; border-radius: 9px; background: var(--accent); color: #fff; display: grid; place-items: center; font-weight: 700; letter-spacing: .5px; }
  .titles { min-width: 0; }
  .titles .t1 { font-weight: 650; line-height: 1.2; white-space: nowrap; }
  .titles .t2 { font-size: 12px; color: var(--text-2); white-space: nowrap; }
  .toggle { margin-left: auto; border: 1px solid var(--border); background: var(--surface); border-radius: 7px; width: 26px; height: 26px; color: var(--text-2); flex: none; }
  .toggle:hover { background: var(--surface-2); color: var(--text); }
  .collapsed .brand { flex-direction: column; gap: 8px; padding: 14px 8px; }
  .collapsed .toggle { margin-left: 0; }

  .nav { flex: 1; overflow-y: auto; padding: 12px 10px; }
  .collapsed .nav { padding: 12px 8px; }
  .nav-label { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--text-3); padding: 4px 8px 8px; font-weight: 600; }
  .chap { position: relative; width: 100%; display: flex; align-items: center; gap: 10px; text-align: left; border: none; background: transparent; border-radius: var(--radius-sm); padding: 8px 10px; color: var(--text); overflow: hidden; margin-bottom: 1px; }
  .collapsed .chap { justify-content: center; padding: 7px 0; }
  .chap:hover { background: var(--surface-2); }
  .chap.active { background: var(--accent-soft); color: var(--accent-text); }
  .num { flex: none; width: 22px; height: 22px; display: grid; place-items: center; border-radius: 6px; background: var(--surface-2); font-size: 12px; font-weight: 600; color: var(--text-2); }
  .chap.active .num { background: var(--accent); color: #fff; }
  .num.done { background: var(--accent); color: #fff; }
  .name { flex: 1; font-size: 13.5px; line-height: 1.25; }
  .badge { font-size: 10.5px; font-weight: 600; color: var(--accent-text); background: color-mix(in srgb, var(--accent) 14%, transparent); padding: 1px 6px; border-radius: 20px; }
  .badge.done { background: var(--accent); color: #fff; }
  .prog { position: absolute; left: 0; bottom: 0; height: 2px; background: var(--accent); opacity: .55; }

  .chev { flex: none; width: 18px; height: 18px; display: grid; place-items: center; border-radius: 5px; color: var(--text-3); font-size: 15px; line-height: 1; transition: transform .15s, background .15s; }
  .chev:hover { background: var(--surface-2); color: var(--text); }
  .chev.open { transform: rotate(90deg); }

  .secs { margin: 1px 0 4px; padding-left: 22px; }
  .sec { position: relative; width: 100%; display: flex; align-items: baseline; gap: 8px; text-align: left; border: none; background: transparent; border-radius: var(--radius-sm); padding: 5px 9px; color: var(--text-2); }
  .sec::before { content: ''; position: absolute; left: 3px; top: 0; bottom: 0; width: 1px; background: var(--border); }
  .sec:hover { background: var(--surface-2); color: var(--text); }
  .sec.active { color: var(--accent-text); background: var(--accent-soft); }
  .snum { flex: none; font-size: 11px; font-weight: 600; color: var(--text-3); min-width: 26px; font-variant-numeric: tabular-nums; }
  .sec.active .snum { color: var(--accent-text); }
  .sname { flex: 1; font-size: 12.5px; line-height: 1.25; min-width: 0; }
  .chev.sub { width: 16px; height: 16px; font-size: 13px; align-self: center; }

  .subs { margin: 0 0 2px; padding-left: 20px; }
  .sub-item { position: relative; width: 100%; display: flex; align-items: baseline; gap: 7px; text-align: left; border: none; background: transparent; border-radius: var(--radius-sm); padding: 4px 9px; color: var(--text-3); }
  .sub-item::before { content: ''; position: absolute; left: 3px; top: 0; bottom: 0; width: 1px; background: var(--border); }
  .sub-item:hover { background: var(--surface-2); color: var(--text-2); }
  .sub-item .snum { min-width: 34px; font-size: 10.5px; }
  .sub-item .sname { font-size: 12px; }
  .foot { padding: 10px 12px; border-top: 1px solid var(--border); }
  .backup { display: flex; gap: 6px; margin-bottom: 8px; }
  .bk { flex: 1; border: 1px solid var(--border-strong); background: var(--surface); border-radius: 7px; padding: 6px 8px; font-size: 12px; color: var(--text-2); }
  .bk:hover { background: var(--surface-2); color: var(--text); }
  .cite { font-size: 11.5px; color: var(--text-3); padding: 0 6px; }

  .m-backdrop { display: none; }
  @media (max-width: 860px) {
    .sidebar { position: fixed; z-index: 60; width: 270px; height: 100%; transform: translateX(-100%); transition: transform .2s ease; box-shadow: none; }
    .sidebar.collapsed { width: 270px; }
    .sidebar.mobile-open { transform: none; box-shadow: 0 0 40px rgba(0,0,0,.3); }
    .sidebar .toggle { display: none; }
    .m-backdrop { display: block; position: fixed; inset: 0; background: rgba(0,0,0,.35); z-index: 55; }
  }
</style>
