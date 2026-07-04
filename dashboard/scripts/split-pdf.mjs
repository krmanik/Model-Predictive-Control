// Split the MPC book PDF into per-chapter PDFs + per-chapter exercise PDFs.
// Page numbers below are 1-indexed *physical* PDF pages.
// Book (Rawlings, Mayne & Diehl, "Model Predictive Control", 2nd ed.) page N
// maps to physical page N + 48.
import { PDFDocument } from 'pdf-lib';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = join(__dirname, '..', '..', 'MPC-book-2nd-edition-1st-printing.pdf');
const OUT = join(__dirname, '..', 'public', 'book');

// id, title, chapter start page, chapter end page, exercises start page (null = none)
// (all physical PDF pages; = book page + 48)
const CH = [
  ['ch01', 'Getting Started with MPC',   49,  136, 108],
  ['ch02', 'MPC — Regulation',           137, 240, 220],
  ['ch03', 'Robust and Stochastic MPC',  241, 316, 310],
  ['ch04', 'State Estimation',           317, 386, 375],
  ['ch05', 'Output MPC',                 387, 416, 414],
  ['ch06', 'Distributed MPC',            417, 498, 483],
  ['ch07', 'Explicit Control Laws',      499, 538, 532],
  ['ch08', 'Numerical Optimal Control',  539, 648, 631],
];

async function extract(src, from, to) {
  const out = await PDFDocument.create();
  const idx = [];
  for (let p = from; p <= to; p++) idx.push(p - 1); // 0-indexed
  const pages = await out.copyPages(src, idx);
  pages.forEach((pg) => out.addPage(pg));
  return out.save();
}

const main = async () => {
  await mkdir(OUT, { recursive: true });
  const bytes = await readFile(SRC);
  const src = await PDFDocument.load(bytes, { ignoreEncryption: true });
  for (const [id, title, start, end, ex] of CH) {
    const chBytes = await extract(src, start, end);
    await writeFile(join(OUT, `${id}.pdf`), chBytes);
    let exInfo = '';
    if (ex) {
      const exBytes = await extract(src, ex, end);
      await writeFile(join(OUT, `${id}-ex.pdf`), exBytes);
      exInfo = ` + ex ${ex}-${end}`;
    }
    console.log(`${id} ${title}: pages ${start}-${end}${exInfo}  (${(chBytes.length / 1024 | 0)}KB)`);
  }
  console.log('done');
};
main();
