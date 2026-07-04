import * as pdfjsLib from 'pdfjs-dist';
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

const cache = new Map();
export function loadPdf(url) {
  if (!cache.has(url)) {
    cache.set(url, pdfjsLib.getDocument(url).promise.catch((e) => { cache.delete(url); throw e; }));
  }
  return cache.get(url);
}

export { pdfjsLib };
