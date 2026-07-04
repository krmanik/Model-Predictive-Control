<script>
  import { loadPdf, pdfjsLib } from '../pdf.js';
  import { asset } from '../asset.js';

  let {
    url,
    page = $bindable(1),
    goto = null,             // { page, y (0..1|null), seq } scroll request from the sidebar
    enableSelection = false,
    highlights = [],
    onload = () => {},
    onpagechange = () => {},
    onselect = () => {},
    onhighlightclick = () => {},
    ongoto = () => {},           // called once a goto target has been scrolled to
  } = $props();

  let doc = $state(null);
  let numPages = $state(0);
  let zoom = $state(1);
  let loading = $state(true);
  let errored = $state(false);
  let pageInput = $state(1);
  let pageW = $state(0);          // CSS px size of every page (book pages are uniform)
  let pageH = $state(0);
  let scale = 1;
  const GAP = 24;

  let scroller = $state(null);
  let pagesEl = $state(null);
  let wrapEls = $state([]);
  let canvasEls = $state([]);
  let textEls = $state([]);

  const rendered = new Set();
  let renderTasks = new Map();
  let scrollRaf = 0;
  let lastSeq = -1;               // last consumed goto.seq (avoids re-scrolling on unrelated updates)
  const dpr = () => Math.min(window.devicePixelRatio || 1, 2.5);
  const pages = $derived(Array.from({ length: numPages }, (_, i) => i + 1));

  // ---- load + layout ---------------------------------------------------------
  // Depends ONLY on the url. `page`/`goto` are read after the first await so they
  // don't retrigger a reload on page-turns/section-jumps. The previous document
  // stays on screen until the new one is ready → no white flash on chapter change.
  $effect(() => {
    const u = asset(url);
    if (!u) { doc = null; numPages = 0; rendered.clear(); loading = false; return; }
    loading = true;
    let alive = true;
    loadPdf(u).then(async (d) => {
      if (!alive) return;
      // swap in the new doc, discarding the old one's render state
      for (const t of renderTasks.values()) { try { t.cancel(); } catch {} }
      renderTasks.clear();
      rendered.clear();
      errored = false;
      doc = d; numPages = d.numPages;
      let p = page;                          // read after await → not a reactive dep
      if (p < 1) p = 1;
      if (p > numPages) p = numPages;
      page = p; pageInput = p;
      await measure();
      if (!alive) return;
      loading = false;
      onload({ numPages });
      await tick();
      // jump to the pending target (section/chapter click) or the saved page
      if (goto) { lastSeq = goto.seq; scrollToPage(goto.page, false, goto.y); ongoto(); }
      else scrollToPage(p, false);
      renderVisible();
    }).catch((e) => { if (alive) { errored = true; loading = false; console.error(e); } });
    return () => { alive = false; };
  });

  function tick() { return new Promise(r => requestAnimationFrame(() => r())); }

  // Same-chapter jump (section/chapter click while already loaded): smooth-scroll,
  // no reload. Only fires when goto.seq advances.
  $effect(() => {
    const g = goto;
    if (loading) return;              // a chapter (url) change is loading; its load path scrolls
    if (!g || !doc || g.seq === lastSeq) return;
    lastSeq = g.seq;
    scrollToPage(g.page, true, g.y);
    ongoto();
  });

  // Re-fit when the viewport width changes (mobile layout, rotation, sidebar toggle).
  // The initial measure can run before layout settles; this corrects it.
  $effect(() => {
    if (!scroller || typeof ResizeObserver === 'undefined') return;
    let lastW = scroller.clientWidth;
    let t = 0;
    const ro = new ResizeObserver(() => {
      const w = scroller.clientWidth;
      if (!w || Math.abs(w - lastW) < 4) return;
      lastW = w;
      clearTimeout(t);
      t = setTimeout(() => { if (doc) relayout(); }, 120);
    });
    ro.observe(scroller);
    return () => { ro.disconnect(); clearTimeout(t); };
  });

  async function measure() {
    const pg = await doc.getPage(1);
    const base = pg.getViewport({ scale: 1 });
    const avail = (scroller?.clientWidth || 800) - 48;
    const fit = avail / base.width;
    scale = Math.max(0.3, fit * zoom);
    const vp = pg.getViewport({ scale });
    pageW = Math.round(vp.width);
    pageH = Math.round(vp.height);
  }

  // ---- rendering -------------------------------------------------------------
  async function renderPage(n) {
    if (!doc || rendered.has(n)) return;
    const canvas = canvasEls[n - 1];
    if (!canvas) return;
    rendered.add(n);
    const pg = await doc.getPage(n);
    const vp = pg.getViewport({ scale });
    const ratio = dpr();
    canvas.width = Math.floor(vp.width * ratio);
    canvas.height = Math.floor(vp.height * ratio);
    canvas.style.width = vp.width + 'px';
    canvas.style.height = vp.height + 'px';
    const ctx = canvas.getContext('2d');
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const task = pg.render({ canvasContext: ctx, viewport: vp });
    renderTasks.set(n, task);
    try { await task.promise; } catch { rendered.delete(n); return; }
    const tdiv = textEls[n - 1];
    if (tdiv) {
      tdiv.replaceChildren();
      tdiv.style.setProperty('--scale-factor', scale);
      tdiv.style.width = vp.width + 'px';
      tdiv.style.height = vp.height + 'px';
      try {
        const tc = await pg.getTextContent();
        const tl = new pdfjsLib.TextLayer({ textContentSource: tc, container: tdiv, viewport: vp });
        await tl.render();
      } catch {}
    }
  }

  function renderVisible() {
    if (!scroller || !pageH) return;
    const unit = pageH + GAP;
    const top = scroller.scrollTop - 600;
    const bottom = scroller.scrollTop + scroller.clientHeight + 600;
    const first = Math.max(1, Math.floor(top / unit) + 1);
    const last = Math.min(numPages, Math.ceil(bottom / unit));
    for (let n = first; n <= last; n++) renderPage(n);
  }

  async function relayout() {
    if (!doc) return;
    // preserve what the reader is looking at, proportionally, across the re-fit
    const prevMax = scroller ? scroller.scrollHeight - scroller.clientHeight : 0;
    const frac = prevMax > 0 ? scroller.scrollTop / prevMax : 0;
    for (const t of renderTasks.values()) { try { t.cancel(); } catch {} }
    renderTasks.clear();
    rendered.clear();
    await measure();
    await tick();
    const newMax = scroller.scrollHeight - scroller.clientHeight;
    scroller.scrollTop = Math.max(0, frac * newMax);
    renderVisible();
  }

  // ---- scroll / navigation ---------------------------------------------------
  function onScroll() {
    if (scrollRaf) return;
    scrollRaf = requestAnimationFrame(() => {
      scrollRaf = 0;
      renderVisible();
      const unit = pageH + GAP;
      const cur = Math.min(numPages, Math.max(1, Math.round(scroller.scrollTop / unit) + 1));
      if (cur !== page) { page = cur; pageInput = cur; onpagechange(cur); }
    });
  }
  function scrollToPage(n, smooth = true, yFrac = null) {
    if (!scroller) return;
    const unit = pageH + GAP;
    // exact page top within the scroller (independent of offsetParent), fall back to estimate
    const wrap = wrapEls[n - 1];
    const base = wrap
      ? wrap.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop
      : (n - 1) * unit;
    const into = yFrac != null ? Math.max(0, yFrac * pageH - 48) : 0;  // margin above heading so it clears the toolbar
    scroller.scrollTo({ top: base + into, behavior: smooth ? 'smooth' : 'auto' });
  }
  function go(n) {
    const t = Math.min(numPages, Math.max(1, n));
    page = t; pageInput = t; onpagechange(t);
    scrollToPage(t);
  }
  function commitInput() {
    const n = parseInt(pageInput, 10);
    if (!isNaN(n)) go(n); else pageInput = page;
  }
  function setZoom(z) { zoom = Math.min(3, Math.max(0.4, +z.toFixed(2))); relayout(); }
  function onKey(e) {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') go(page + 1);
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(page - 1);
  }

  // ---- selection -------------------------------------------------------------
  function captureSelection() {
    if (!enableSelection) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const text = sel.toString().trim();
    if (!text) return;
    const rng = sel.getRangeAt(0);
    const node = rng.startContainer.nodeType === 1 ? rng.startContainer : rng.startContainer.parentElement;
    const wrap = node?.closest?.('.page-wrap');
    if (!wrap) return;
    const pNum = Number(wrap.dataset.page);
    const box = wrap.getBoundingClientRect();
    const rects = [...rng.getClientRects()]
      .filter(r => r.width > 1 && r.height > 1)
      .map(r => ({
        x: (r.left - box.left) / box.width,
        y: (r.top - box.top) / box.height,
        w: r.width / box.width,
        h: r.height / box.height,
      }));
    if (!rects.length) return;
    onselect({ text, page: pNum, rects });
  }
  const hlByPage = $derived.by(() => {
    const m = {};
    for (const h of highlights) (m[h.page] ||= []).push(h);
    return m;
  });
</script>

<div class="viewer">
  {#if !url}
    <div class="empty">No document for this chapter.</div>
  {:else}
  <div class="toolbar">
    <div class="grp">
      <button class="btn icon" onclick={() => go(page - 1)} disabled={page <= 1} title="Previous (←)">‹</button>
      <div class="pageno">
        <input type="text" bind:value={pageInput} onchange={commitInput} onfocus={(e) => e.target.select()} />
        <span class="muted">/ {numPages || '–'}</span>
      </div>
      <button class="btn icon" onclick={() => go(page + 1)} disabled={page >= numPages} title="Next (→)">›</button>
    </div>
    <div class="grp">
      <button class="btn icon" onclick={() => setZoom(zoom - 0.15)} title="Zoom out">−</button>
      <button class="btn" onclick={() => setZoom(1)} title="Fit width">{Math.round(zoom * 100)}%</button>
      <button class="btn icon" onclick={() => setZoom(zoom + 0.15)} title="Zoom in">+</button>
    </div>
    {#if enableSelection}<div class="hint muted">Select text → save as note or highlight</div>{/if}
  </div>

  <div class="scroll" bind:this={scroller} tabindex="0" onkeydown={onKey} onscroll={onScroll} onmouseup={captureSelection}>
    {#if errored}
      <div class="state">Could not load PDF.</div>
    {:else}
      <div class="pages" bind:this={pagesEl}>
        {#each pages as n (n)}
          <div class="page-wrap" data-page={n} class:selectable={enableSelection}
               style="width:{pageW}px;height:{pageH}px"
               bind:this={wrapEls[n - 1]}>
            <canvas bind:this={canvasEls[n - 1]}></canvas>
            <div class="textLayer" bind:this={textEls[n - 1]}></div>
            <div class="hl-layer">
              {#each (hlByPage[n] || []) as h (h.id)}
                {#each h.rects as r}
                  <div class="hl" role="button" tabindex="-1"
                    style="left:{r.x*100}%;top:{r.y*100}%;width:{r.w*100}%;height:{r.h*100}%;background:{h.color || 'var(--highlight)'}"
                    title={h.text} onclick={() => onhighlightclick(h.id)}></div>
                {/each}
              {/each}
            </div>
            <div class="pnum">{n}</div>
          </div>
        {/each}
      </div>
      {#if loading}<div class="state floating">Loading…</div>{/if}
    {/if}
  </div>
  {/if}
</div>

<style>
  .viewer { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .toolbar { display: flex; align-items: center; gap: 16px; padding: 8px 14px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .grp { display: flex; align-items: center; gap: 6px; }
  .pageno { display: flex; align-items: center; gap: 6px; }
  .pageno input { width: 46px; text-align: center; border: 1px solid var(--border-strong); border-radius: 6px; padding: 5px 4px; background: var(--bg); color: var(--text); font-family: inherit; }
  .hint { margin-left: auto; font-size: 12.5px; }

  .scroll { flex: 1; min-height: 0; overflow: auto; background: var(--bg); outline: none; }
  .pages { display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 24px; min-height: min-content; }
  .page-wrap { position: relative; box-shadow: var(--shadow); background: #fff; border-radius: 2px; flex: none; }
  canvas { display: block; border-radius: 2px; width: 100%; height: 100%; }

  .page-wrap :global(.textLayer) { position: absolute; inset: 0; }
  .page-wrap:not(.selectable) :global(.textLayer) { pointer-events: none; user-select: none; }

  .hl-layer { position: absolute; inset: 0; pointer-events: none; }
  .hl { position: absolute; border-radius: 2px; opacity: .42; mix-blend-mode: multiply; pointer-events: auto; cursor: pointer; transition: opacity .1s; }
  .hl:hover { opacity: .62; }

  .pnum { position: absolute; bottom: -19px; right: 2px; font-size: 11px; color: var(--text-3); }
  .empty { flex: 1; display: grid; place-items: center; color: var(--text-3); font-size: 14px; }
  .state { color: var(--text-2); padding: 40px; text-align: center; }
  .state.floating { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }

  @media (max-width: 860px) {
    .toolbar { gap: 8px; padding: 7px 10px; justify-content: space-between; }
    .hint { display: none; }
    .toolbar :global(.btn.icon) { width: 36px; height: 36px; }  /* bigger tap targets */
    .pageno input { padding: 7px 4px; }
    .pages { padding: 12px; gap: 16px; }
  }
</style>
