// Emit src/lib/data/manifest.json for the MPC dashboard.
// The book PDF has no embedded outline, so per-chapter sections (N.M) are
// parsed from the printed "Contents" pages (physical PDF pages 13–18).
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const OUT = join(__dirname, '..', 'src', 'lib', 'data', 'manifest.json');
const BOOK = join(ROOT, 'MPC-book-2nd-edition-1st-printing.pdf');

// Book (not physical) page numbers. Physical page = book page + 48.
const CH = [
  { id: 'ch01', n: 1, title: 'Getting Started with MPC',   start: 1,   end: 88,  ex: 60 },
  { id: 'ch02', n: 2, title: 'MPC — Regulation',           start: 89,  end: 192, ex: 172 },
  { id: 'ch03', n: 3, title: 'Robust and Stochastic MPC',  start: 193, end: 268, ex: 262 },
  { id: 'ch04', n: 4, title: 'State Estimation',           start: 269, end: 338, ex: 327 },
  { id: 'ch05', n: 5, title: 'Output MPC',                 start: 339, end: 368, ex: 366 },
  { id: 'ch06', n: 6, title: 'Distributed MPC',            start: 369, end: 450, ex: 435 },
  { id: 'ch07', n: 7, title: 'Explicit Control Laws',      start: 451, end: 490, ex: 484 },
  { id: 'ch08', n: 8, title: 'Numerical Optimal Control',  start: 491, end: 600, ex: 583 },
];
const CONTENTS_PAGES = [13, 14, 15, 16, 17, 18]; // physical pages holding the main-chapter TOC

// --- parse "N.M  Title . . . . page" entries from the Contents pages ----------
async function parseSections() {
  const byChapter = {};  // n -> [{num, title, page, y}]
  let text = '';
  try {
    const doc = await getDocument({ data: new Uint8Array(await readFile(BOOK)) }).promise;
    for (const p of CONTENTS_PAGES) {
      const pg = await doc.getPage(p);
      text += ' ' + (await pg.getTextContent()).items.map(i => i.str).join(' ');
    }
  } catch (e) {
    console.warn('sections: could not read Contents pages —', e.message);
    return byChapter;
  }
  text = text.replace(/\s+/g, ' ');
  // Tokenize by every section-number marker (N.M or N.M.K). Each entry's text
  // runs until the next marker; its page is the last integer in that span and
  // its title is what precedes the dot leader. This is robust to titles that
  // wrap past their page number in the flattened TOC stream.
  const marker = /(\d+)\.(\d+)(?:\.(\d+))?(?=\s)/g;
  const toks = [];
  let mm;
  while ((mm = marker.exec(text)) !== null) {
    toks.push({ n: Number(mm[1]), m: Number(mm[2]), k: mm[3], start: mm.index, end: marker.lastIndex });
  }
  const parent = {};   // chapterN -> last level-2 section object (to attach subs)
  for (let i = 0; i < toks.length; i++) {
    const t = toks[i];
    const ch = CH.find(c => c.n === t.n);
    if (!ch) continue;
    const span = text.slice(t.end, toks[i + 1]?.start ?? text.length);
    const nums = span.match(/\d+/g);
    if (!nums) continue;
    const book = Number(nums[nums.length - 1]);
    if (book < ch.start || book > ch.end) continue;
    const title = span.replace(/\s*\.(\s*\.)+.*$/, '').replace(/\s+\d+\b.*$/, '').replace(/\s+\.\s*$/, '').replace(/\s+/g, ' ').trim();
    if (!title) continue;
    const entry = { num: t.k ? `${t.n}.${t.m}.${t.k}` : `${t.n}.${t.m}`, title, book };
    if (t.k) {
      // level-3 (N.M.K) → nest under the current level-2 parent of the same major
      const p = parent[t.n];
      if (p && p.num === `${t.n}.${t.m}`) p._subs.push(entry);
    } else {
      entry._subs = [];
      parent[t.n] = entry;
      (byChapter[t.n] ||= []).push(entry);
    }
  }
  // de-dupe and compute page-within-chapter (sections + their subsections).
  // `book` is kept so resolveYs() can locate the heading on the physical page;
  // it is stripped from the output in main().
  for (const n of Object.keys(byChapter)) {
    const ch = CH.find(c => c.n === Number(n));
    const toPage = (book) => book - ch.start + 1;
    const seen = new Set();
    byChapter[n] = byChapter[n]
      .filter(s => (seen.has(s.num) ? false : seen.add(s.num)))
      .map(s => {
        const seenSub = new Set();
        const subs = (s._subs || [])
          .filter(x => (seenSub.has(x.num) ? false : seenSub.add(x.num)))
          .map(x => ({ num: x.num, title: x.title, page: toPage(x.book), book: x.book, y: 0 }));
        return { num: s.num, title: s.title, page: toPage(s.book), book: s.book, y: 0, subs };
      });
  }
  return byChapter;
}

// Physical PDF page = book page + PAGE_OFFSET (front matter). The split per-chapter
// PDFs keep page geometry, so a heading's vertical fraction on the physical page is
// the same fraction the reader scrolls to.
const PAGE_OFFSET = 48;
const norm = (s) => s.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '');

// Find the fraction (0..1 from the page top) where heading `num`/`title` sits on
// its book page. Matches the exact section-number token, then confirms the title's
// first word follows so equation/cross-references (e.g. "Section 2.1") don't win.
// Returns 0 (page top) when nothing convincing is found.
async function resolveY(doc, book, num, title) {
  const phys = book + PAGE_OFFSET;
  if (phys < 1 || phys > doc.numPages) return 0;
  let items, vp;
  try {
    const pg = await doc.getPage(phys);
    vp = pg.getViewport({ scale: 1 });
    items = (await pg.getTextContent()).items;
  } catch { return 0; }
  const want = norm(title).slice(0, 24);
  const yFrac = (it) => vp.convertToViewportPoint(it.transform[4], it.transform[5])[1] / vp.height;
  let fallback = null;
  for (let i = 0; i < items.length; i++) {
    if (items[i].str.trim() !== num) continue;
    if (fallback == null) fallback = yFrac(items[i]);
    // gather the next few non-empty items on roughly the same line as the title
    let joined = '';
    for (let j = i + 1; j < items.length && joined.length < 32; j++) joined += items[j].str;
    if (want && norm(joined).startsWith(want.slice(0, 4))) return +yFrac(items[i]).toFixed(4);
  }
  return fallback != null ? +fallback.toFixed(4) : 0;
}

// Fill in the `y` fraction for every section and subsection, in place.
async function resolveYs(byChapter) {
  let doc;
  try {
    doc = await getDocument({ data: new Uint8Array(await readFile(BOOK)) }).promise;
  } catch (e) {
    console.warn('y-resolve: could not open book —', e.message);
    return;
  }
  let hit = 0, miss = 0;
  for (const n of Object.keys(byChapter)) {
    for (const s of byChapter[n]) {
      s.y = await resolveY(doc, s.book, s.num, s.title);
      (s.y > 0 ? hit++ : miss++);
      for (const x of s.subs) {
        x.y = await resolveY(doc, x.book, x.num, x.title);
        (x.y > 0 ? hit++ : miss++);
      }
    }
  }
  console.log(`y-resolve: ${hit} located, ${miss} defaulted to page top`);
}

const main = async () => {
  const secs = await parseSections();
  await resolveYs(secs);
  const stripBook = ({ book, ...rest }) => ({ ...rest, subs: rest.subs?.map(stripBook) });
  const chapters = CH.map(c => ({
    ...c,
    pdf: `/book/${c.id}.pdf`,
    exPdf: c.ex ? `/book/${c.id}-ex.pdf` : null,
    pages: c.end - c.start + 1,
    sections: (secs[c.n] || []).map(stripBook),
    slides: [],
    videos: [],
  }));
  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify({ generated: new Date().toISOString(), chapters }, null, 2));
  const nsec = chapters.reduce((a, c) => a + c.sections.length, 0);
  console.log(`manifest: ${chapters.length} chapters, ${nsec} sections`);
};
main();
