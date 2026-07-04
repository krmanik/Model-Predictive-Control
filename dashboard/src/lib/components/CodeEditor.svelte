<script>
  import { EditorView, basicSetup } from 'codemirror';
  import { Compartment } from '@codemirror/state';
  import { indentUnit } from '@codemirror/language';
  import { python } from '@codemirror/lang-python';
  import { oneDark } from '@codemirror/theme-one-dark';

  let { value = $bindable(''), dark = false } = $props();

  let host = $state(null);
  let view;
  let applying = false;
  const themeC = new Compartment();

  const baseTheme = EditorView.theme({
    '&': { height: '100%', fontSize: '13px', backgroundColor: 'transparent' },
    '.cm-scroller': { fontFamily: 'var(--mono)', lineHeight: '1.6' },
    '.cm-content': { padding: '12px 0' },
    '.cm-gutters': { backgroundColor: 'transparent', border: 'none', color: 'var(--text-3)' },
    '&.cm-focused': { outline: 'none' },
    '.cm-activeLine': { backgroundColor: 'color-mix(in srgb, var(--accent) 5%, transparent)' },
    '.cm-activeLineGutter': { backgroundColor: 'transparent' },
  });

  $effect(() => {
    if (!host || view) return;
    view = new EditorView({
      doc: value,
      parent: host,
      extensions: [
        basicSetup,
        python(),
        indentUnit.of('    '),
        baseTheme,
        themeC.of(dark ? oneDark : []),
        EditorView.updateListener.of((u) => {
          if (u.docChanged && !applying) value = u.state.doc.toString();
        }),
      ],
    });
    return () => { view?.destroy(); view = null; };
  });

  // external value changes (switch problem / reset)
  $effect(() => {
    const v = value;
    if (view && v !== view.state.doc.toString()) {
      applying = true;
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: v } });
      applying = false;
    }
  });

  // theme switch
  $effect(() => {
    if (view) view.dispatch({ effects: themeC.reconfigure(dark ? oneDark : []) });
  });
</script>

<div class="cm" bind:this={host}></div>

<style>
  .cm { height: 100%; overflow: hidden; }
  .cm :global(.cm-editor) { height: 100%; }
</style>
