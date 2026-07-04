// Single persisted reactive store for all dashboard state.
import challenges from '../data/challenges.json';
const KEY = 'mpc-dashboard-v1';

function load() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
  catch { return {}; }
}

const defaults = {
  ui: { chapter: 'ch01', tab: 'reader', collapsed: false, mobileNav: false, nonce: 0, readerGoto: null },
  reader: {},     // chId -> { page, furthest, scale }
  exercises: {},  // chId -> { page }
  notes: {},      // chId -> [ {id, type:'note'|'highlight', text, color, page, rects, body, ts} ]
  solutions: {},  // challengeId -> { code, solved, ts }
};

const raw = load();
// deep-merge defaults so new keys appear for old saves
const initial = structuredClone(defaults);
for (const k of Object.keys(defaults)) {
  if (raw[k] && typeof raw[k] === 'object') Object.assign(initial[k], raw[k]);
}

export const store = $state(initial);

let timer;
export function persist() {
  clearTimeout(timer);
  timer = setTimeout(() => {
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { console.warn('persist failed', e); }
  }, 150);
}

// ---- helpers -----------------------------------------------------------------
export function readerState(chId) {
  if (!store.reader[chId]) store.reader[chId] = { page: 1, furthest: 1, scale: 0 };
  return store.reader[chId];
}
export function setReaderPage(chId, page, total) {
  const r = readerState(chId);
  r.page = page;
  if (page > r.furthest) r.furthest = page;
  r.total = total;
  persist();
}
// reader-only progress (used by the Reader tab's own bar)
export function readerProgress(chId) {
  const r = store.reader[chId];
  if (r?.completed) return 1;
  if (!r || !r.total) return 0;
  return Math.min(1, r.furthest / r.total);
}
export function isChapterComplete(chId) { return !!store.reader[chId]?.completed; }

// composite chapter progress: average over the components that exist for the
// chapter (reading, exercises, videos watched, challenges solved)
export function chapterProgress(ch) {
  const r = store.reader[ch.id];
  if (r?.completed) return 1;
  const parts = [];
  if (ch.pdf) parts.push(r && r.total ? Math.min(1, r.furthest / r.total) : 0);
  if (ch.exPdf) { const e = store.exercises[ch.id]; parts.push(e && e.total ? Math.min(1, e.furthest / e.total) : 0); }
  const cl = challenges[ch.id] || [];
  if (cl.length) {
    const solved = cl.filter(c => store.solutions[c.id]?.solved).length;
    parts.push(solved / cl.length);
  }
  if (!parts.length) return 0;
  return parts.reduce((a, b) => a + b, 0) / parts.length;
}

export function markChapterComplete(chId) {
  const r = readerState(chId);
  r.completed = true;
  if (r.total) r.furthest = r.total;
  store.ui.nonce = (store.ui.nonce ?? 0) + 1;
  persist();
}

// Reset reading/watching progress for a chapter (keeps notes & challenge solutions).
export function resetChapterProgress(chId, chapter) {
  store.reader[chId] = { page: 1, furthest: 1, scale: 0, total: store.reader[chId]?.total };
  delete store.exercises[chId];
  for (const c of (challenges[chId] || [])) if (store.solutions[c.id]) store.solutions[c.id].solved = false;
  store.ui.nonce = (store.ui.nonce ?? 0) + 1; // force tab components to remount fresh
  persist();
}

const uid = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2));

export function notesFor(chId) {
  if (!store.notes[chId]) store.notes[chId] = [];
  return store.notes[chId];
}
export function addNote(chId, note) {
  notesFor(chId).unshift({ id: uid(), ts: Date.now(), ...note });
  persist();
}
export function removeNote(chId, id) {
  store.notes[chId] = notesFor(chId).filter(n => n.id !== id);
  persist();
}
export function updateNote(chId, id, patch) {
  const n = notesFor(chId).find(x => x.id === id);
  if (n) { Object.assign(n, patch); persist(); }
}

export { uid };

// ---- backup / restore --------------------------------------------------------
export function exportData() {
  return JSON.stringify({ app: 'mr-dashboard', version: 1, exportedAt: new Date().toISOString(), data: store }, null, 2);
}
export function importData(json) {
  const parsed = JSON.parse(json);
  const incoming = parsed.data ?? parsed; // accept raw store too
  for (const k of Object.keys(defaults)) {
    if (incoming[k] && typeof incoming[k] === 'object') store[k] = incoming[k];
  }
  persist();
}
