<script>
  import allChallenges from '../data/challenges.json';
  import { store, persist } from '../stores/store.svelte.js';
  import { untrack } from 'svelte';
  import { runChallenge } from '../pyodide.js';
  import { md } from '../md.js';
  import CodeEditor from './CodeEditor.svelte';

  let { chapter } = $props();
  const list = $derived(allChallenges[chapter.id] || []);

  let sel = $state(0);
  const current = $derived(list[sel]);

  let code = $state('');
  let results = $state(null);
  let running = $state(false);
  let status = $state('');
  let consoleTab = $state('tests');  // tests | solution
  let listOpen = $state(true);
  let split = $state(44);            // % width of description panel

  let dark = $state(typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches);
  $effect(() => {
    if (typeof matchMedia === 'undefined') return;
    const mq = matchMedia('(prefers-color-scheme: dark)');
    const h = (e) => dark = e.matches;
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  });

  // load saved or starter code when the *problem* changes (not when its
  // solved state is written back during a run)
  $effect(() => {
    const c = current;
    if (!c) return;
    const id = c.id; // establishes the dependency
    untrack(() => {
      code = store.solutions[id]?.code || c.starter;
      results = null; status = ''; consoleTab = 'tests';
    });
  });

  // pick a problem; on narrow screens the list is an overlay, so close it
  function pick(i) { sel = i; if (typeof window !== 'undefined' && window.innerWidth <= 860) listOpen = false; }
  function prev() { if (sel > 0) sel--; }
  function next() { if (sel < list.length - 1) sel++; }

  const fmtArgs = (args) => args.map(a => JSON.stringify(a)).join(', ');
  const examples = $derived((current?.tests || []).slice(0, 3));

  async function run() {
    if (running || !current) return;
    running = true; results = null; status = 'Loading…'; consoleTab = 'tests';
    store.solutions[current.id] = { ...(store.solutions[current.id] || {}), code };
    persist();
    try {
      const res = await runChallenge(code, current.func, current.tests, (s) => status = s);
      results = res;
      if (res.results && res.results.every(r => r.ok)) {
        store.solutions[current.id] = { code, solved: true, ts: Date.now() };
        persist();
      }
    } catch (e) {
      results = { fatal: 'Runtime failed to start: ' + e.message };
    } finally {
      running = false; status = '';
    }
  }
  function reset() { code = current.starter; results = null; }

  const passedCount = $derived(results?.results ? results.results.filter(r => r.ok).length : 0);
  const allPass = $derived(!!results?.results && results.results.every(r => r.ok));
  const solvedTotal = $derived(list.filter(c => store.solutions[c.id]?.solved).length);

  // ---- drag to resize split --------------------------------------------------
  let dragging = false, bodyEl = $state(null);
  function startDrag(e) {
    dragging = true; e.preventDefault();
    window.addEventListener('pointermove', onDrag);
    window.addEventListener('pointerup', stopDrag);
  }
  function onDrag(e) {
    if (!dragging || !bodyEl) return;
    const r = bodyEl.getBoundingClientRect();
    split = Math.min(72, Math.max(26, ((e.clientX - r.left) / r.width) * 100));
  }
  function stopDrag() {
    dragging = false;
    window.removeEventListener('pointermove', onDrag);
    window.removeEventListener('pointerup', stopDrag);
  }
</script>

{#if list.length === 0}
  <div class="none">No challenges for this chapter yet.</div>
{:else}
<div class="lc">
  <header class="top">
    <button class="btn icon listbtn" onclick={() => listOpen = !listOpen} title="Problem list">☰</button>
    <button class="btn icon" onclick={prev} disabled={sel === 0} title="Previous">‹</button>
    <button class="btn icon" onclick={next} disabled={sel === list.length - 1} title="Next">›</button>
    <span class="idx muted">{sel + 1}/{list.length}</span>
    <h2 class="title">{current.title}</h2>
    {#if current.section}<span class="secref" title="Book section {current.section}">§{current.section}</span>{/if}
    <span class="pill d-{current.difficulty.toLowerCase()}">{current.difficulty}</span>
    <div class="spacer"></div>
    <span class="solved-pill">{solvedTotal}/{list.length} solved</span>
  </header>

  <div class="body" bind:this={bodyEl}>
    <!-- problem list drawer -->
    {#if listOpen}
      <div class="backdrop" onclick={() => listOpen = false}></div>
      <div class="drawer">
        <div class="drawer-h">Chapter {chapter.n} · Problems</div>
        {#each list as c, i}
          {@const solved = store.solutions[c.id]?.solved}
          <button class="di" class:active={i === sel} onclick={() => pick(i)}>
            <span class="ck" class:on={solved}></span>
            <span class="dinfo"><span class="dname">{c.title}</span>
              <span class="dmeta">{#if c.section}<span class="dsec">§{c.section}</span>{/if}<span class="d-{c.difficulty.toLowerCase()} dd">{c.difficulty}</span></span></span>
          </button>
        {/each}
      </div>
    {/if}

    <!-- description -->
    <section class="desc" style="flex-basis:{split}%">
      <div class="prose">{@html md(current.prompt)}</div>

      <div class="examples">
        <h3>Examples</h3>
        {#each examples as ex, i}
          <div class="ex">
            <div class="ex-l muted">Example {i + 1}</div>
            <div><span class="ex-k">Input</span> <code>{current.func}({fmtArgs(ex.args)})</code></div>
            <div><span class="ex-k">Output</span> <code>{JSON.stringify(ex.expected)}</code></div>
          </div>
        {/each}
      </div>

      {#if current.tags?.length}
        <div class="tags">{#each current.tags as t}<span class="tag">{t}</span>{/each}</div>
      {/if}
    </section>

    <div class="resizer" onpointerdown={startDrag}></div>

    <!-- editor + console -->
    <section class="ide">
      <div class="ide-bar">
        <span class="lang">Python 3</span>
        <span class="fn muted">def {current.func}(…)</span>
        <div class="spacer"></div>
        <button class="btn" onclick={reset}>Reset</button>
        <button class="btn primary" onclick={run} disabled={running}>{running ? 'Running…' : 'Run'}</button>
      </div>

      <div class="ed"><CodeEditor bind:value={code} {dark} /></div>

      <div class="console">
        <div class="console-tabs">
          <button class="ct" class:active={consoleTab === 'tests'} onclick={() => consoleTab = 'tests'}>Test Results</button>
          <button class="ct" class:active={consoleTab === 'solution'} onclick={() => consoleTab = 'solution'}>Solution</button>
          {#if results?.results}
            <span class="verdict {allPass ? 'ok' : 'bad'}">{allPass ? 'Accepted' : 'Wrong Answer'}</span>
          {/if}
        </div>
        <div class="console-body">
          {#if consoleTab === 'solution'}
            <pre class="solcode">{current.solution}</pre>
          {:else if running}
            <div class="cstate">{status || 'Running…'}</div>
          {:else if results?.fatal}
            <div class="fatal">{results.fatal}</div>
          {:else if results?.results}
            <div class="summary {allPass ? 'ok' : 'bad'}">{passedCount} / {results.results.length} test cases passed</div>
            {#each results.results as r}
              <div class="case {r.ok ? 'ok' : 'bad'}">
                <span class="cbadge">{r.ok ? 'PASS' : 'FAIL'}</span>
                <code class="cargs">{current.func}({fmtArgs(r.args)})</code>
                {#if r.error}<span class="cerr">→ {r.error}</span>
                {:else}<span class="ccmp">→ <code>{JSON.stringify(r.got)}</code>{#if !r.ok} <span class="exp">expected <code>{JSON.stringify(r.expected)}</code></span>{/if}</span>{/if}
              </div>
            {/each}
          {:else}
            <div class="cstate muted">Write your solution and press <b>Run</b>. The first run downloads the Python runtime (cached afterward).</div>
          {/if}
        </div>
      </div>
    </section>
  </div>
</div>
{/if}

<style>
  .none { padding: 50px; text-align: center; color: var(--text-2); }
  .lc { display: flex; flex-direction: column; height: 100%; min-height: 0; }

  .top { display: flex; align-items: center; gap: 8px; padding: 9px 14px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .idx { font-size: 12.5px; }
  .title { margin: 0 2px; font-size: 16px; font-weight: 650; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .spacer { flex: 1; }
  .pill, .dd { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
  .d-easy { color: #2f8f5b; } .d-medium { color: #c08a16; } .d-hard { color: var(--danger); }
  .solved-pill { font-size: 12px; color: var(--text-2); background: var(--surface-2); padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
  .secref { font-size: 11px; font-weight: 600; color: var(--accent-text); background: var(--accent-soft); padding: 2px 7px; border-radius: 20px; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .dmeta { display: inline-flex; align-items: center; gap: 7px; }
  .dsec { font-size: 10.5px; font-weight: 600; color: var(--accent-text); font-variant-numeric: tabular-nums; }

  .body { flex: 1; min-height: 0; display: flex; position: relative; }

  .desc { overflow-y: auto; padding: 20px 22px 30px; min-width: 0; flex: none; }
  .prose :global(p) { margin: 0 0 12px; line-height: 1.6; }
  .prose :global(code) { font-family: var(--mono); font-size: 12.5px; background: var(--surface-2); padding: 1px 5px; border-radius: 5px; }
  .prose :global(strong) { font-weight: 650; }
  .prose :global(.formula) { font-family: var(--mono); font-size: 13px; background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 6px; padding: 10px 12px; margin: 0 0 12px; white-space: pre-wrap; overflow-x: auto; }

  .examples h3 { font-size: 13px; margin: 18px 0 8px; }
  .ex { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; font-size: 13px; }
  .ex-l { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
  .ex-k { display: inline-block; width: 56px; color: var(--text-3); font-size: 12px; }
  .ex code { font-family: var(--mono); font-size: 12px; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 16px; }
  .tag { font-size: 11.5px; background: var(--surface-2); color: var(--text-2); padding: 3px 9px; border-radius: 20px; }

  .resizer { width: 6px; flex: none; cursor: col-resize; background: var(--border); opacity: .5; transition: opacity .12s; }
  .resizer:hover { opacity: 1; background: var(--accent); }

  .ide { flex: 1; min-width: 0; display: flex; flex-direction: column; border-left: 1px solid var(--border); }
  .ide-bar { display: flex; align-items: center; gap: 10px; padding: 7px 12px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .lang { font-size: 12px; font-weight: 600; background: var(--surface-2); padding: 3px 9px; border-radius: 6px; }
  .fn { font-family: var(--mono); font-size: 12px; }
  .ed { flex: 1; min-height: 120px; overflow: hidden; background: var(--surface); }

  .console { height: 42%; min-height: 150px; display: flex; flex-direction: column; border-top: 1px solid var(--border); background: var(--surface); }
  .console-tabs { display: flex; align-items: center; gap: 4px; padding: 6px 10px; border-bottom: 1px solid var(--border); }
  .ct { border: none; background: transparent; padding: 5px 10px; border-radius: 6px; font-weight: 550; color: var(--text-2); font-size: 12.5px; }
  .ct.active { background: var(--surface-2); color: var(--text); }
  .verdict { margin-left: auto; font-weight: 700; font-size: 13px; }
  .verdict.ok { color: #2f8f5b; } .verdict.bad { color: var(--danger); }
  .console-body { flex: 1; overflow-y: auto; padding: 10px 12px; }
  .summary { font-weight: 650; margin-bottom: 8px; }
  .summary.ok { color: #2f8f5b; } .summary.bad { color: var(--danger); }
  .case { display: flex; align-items: baseline; gap: 8px; padding: 6px 10px; border-radius: 7px; margin-bottom: 4px; font-size: 12.5px; }
  .case.ok { background: color-mix(in srgb, #2f8f5b 9%, transparent); }
  .case.bad { background: color-mix(in srgb, var(--danger) 9%, transparent); }
  .cbadge { font-weight: 700; font-size: 10px; letter-spacing: .03em; min-width: 30px; }
  .case.ok .cbadge { color: #2f8f5b; } .case.bad .cbadge { color: var(--danger); }
  .cargs, .ccmp code { font-family: var(--mono); }
  .ccmp { color: var(--text-2); } .exp { color: var(--danger); }
  .cerr { color: var(--danger); font-family: var(--mono); }
  .fatal { padding: 10px 12px; background: color-mix(in srgb, var(--danger) 12%, transparent); color: var(--danger); border-radius: 8px; font-family: var(--mono); font-size: 12.5px; white-space: pre-wrap; }
  .cstate { padding: 8px 2px; }
  .solcode { font-family: var(--mono); font-size: 12.5px; white-space: pre-wrap; margin: 0; }

  /* problem list — docked sidebar on desktop, overlay drawer on mobile */
  .backdrop { display: none; }
  .drawer { position: relative; flex: none; width: 260px; background: var(--surface); border-right: 1px solid var(--border); overflow-y: auto; }
  .drawer-h { padding: 14px 16px 8px; font-weight: 650; font-size: 13px; }
  .di { width: 100%; display: flex; align-items: center; gap: 10px; text-align: left; border: none; background: transparent; padding: 9px 14px; color: var(--text); }
  .di:hover { background: var(--surface-2); } .di.active { background: var(--accent-soft); }
  .ck { flex: none; width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--border-strong); display: grid; place-items: center; font-size: 11px; color: var(--accent); }
  .ck.on { background: var(--accent); border-color: var(--accent); color: #fff; }
  .dinfo { display: flex; flex-direction: column; gap: 1px; }
  .dname { font-size: 13px; }

  @media (max-width: 860px) {
    .body { flex-direction: column; }
    .backdrop { display: block; position: absolute; inset: 0; background: rgba(0,0,0,.25); z-index: 9; }
    .drawer { position: absolute; left: 0; top: 0; bottom: 0; width: 300px; max-width: 85%; z-index: 10; box-shadow: var(--shadow); }
    .desc { flex-basis: auto !important; max-height: 38%; border-bottom: 1px solid var(--border); }
    .resizer { display: none; }
    .ide { border-left: none; }
    .title { font-size: 14px; }
    .solved-pill { display: none; }
  }
</style>
