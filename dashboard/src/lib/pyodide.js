// Lazy Pyodide loader (from CDN) + a test-runner harness for challenges.
const PYODIDE_VERSION = 'v0.26.4';
const CDN = `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`;

let pyodidePromise = null;

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement('script');
    s.src = src; s.onload = resolve; s.onerror = () => reject(new Error('Failed to load ' + src));
    document.head.appendChild(s);
  });
}

export function getPyodide(onStatus = () => {}) {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      onStatus('Downloading Python runtime…');
      await loadScript(CDN + 'pyodide.js');
      onStatus('Starting Python…');
      const py = await window.loadPyodide({ indexURL: CDN });
      onStatus('Loading numpy…');
      try { await py.loadPackage('numpy'); } catch (e) { console.warn('numpy load failed', e); }
      onStatus('');
      return py;
    })().catch((e) => { pyodidePromise = null; throw e; });
  }
  return pyodidePromise;
}

const HARNESS = `
import json, math
try:
    import numpy as np
    _HAS_NP = True
except Exception:
    _HAS_NP = False

def _norm(x):
    if _HAS_NP and isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, tuple):
        return [_norm(i) for i in x]
    return x

def _eq(a, b, tol=1e-6):
    a, b = _norm(a), _norm(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_eq(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol * max(1.0, abs(b))
    return a == b

def _round(x):
    x = _norm(x)
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, list):
        return [_round(i) for i in x]
    return x

def _run(user_code, func_name, tests):
    out = []
    ns = {}
    try:
        exec(user_code, ns)
    except Exception as e:
        return json.dumps({'fatal': 'Error in your code: ' + str(e)})
    fn = ns.get(func_name)
    if not callable(fn):
        return json.dumps({'fatal': "Define a function named '" + func_name + "'."})
    for t in tests:
        rec = {'args': _round(t['args'])}
        try:
            got = fn(*t['args'])
            rec['got'] = _round(got)
            rec['expected'] = _round(t['expected'])
            rec['ok'] = _eq(got, t['expected'])
        except Exception as e:
            rec['ok'] = False
            rec['error'] = str(e)
            rec['expected'] = _round(t['expected'])
        out.append(rec)
    return json.dumps({'results': out})
`;

export async function runChallenge(code, funcName, tests, onStatus) {
  const py = await getPyodide(onStatus);
  py.runPython(HARNESS);
  const runner = py.globals.get('_run');
  const testsPy = py.toPy(tests);
  try {
    const json = runner(code, funcName, testsPy);
    return JSON.parse(json);
  } finally {
    testsPy?.destroy?.();
    runner?.destroy?.();
  }
}
