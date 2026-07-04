// Tiny, safe markdown renderer for challenge prompts.
// Supports: **bold**, *italic*, `code`, blank-line paragraphs, and
// 4-space-indented lines rendered as monospace formula blocks.
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function inline(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
}
export function md(src) {
  if (!src) return '';
  const lines = src.split('\n');
  let html = '', para = [], pre = [];
  const flushP = () => { if (para.length) { html += '<p>' + para.join(' ') + '</p>'; para = []; } };
  const flushPre = () => { if (pre.length) { html += '<pre class="formula">' + pre.join('\n') + '</pre>'; pre = []; } };
  for (const ln of lines) {
    if (/^\s{4,}\S/.test(ln)) { flushP(); pre.push(esc(ln.replace(/^\s{4}/, ''))); }
    else if (ln.trim() === '') { flushP(); flushPre(); }
    else { flushPre(); para.push(inline(ln)); }
  }
  flushP(); flushPre();
  return html;
}
