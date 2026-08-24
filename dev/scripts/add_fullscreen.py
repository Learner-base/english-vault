#!/usr/bin/env python3
"""Add a Full screen button to the header of every listening / reading test.

The tests come from several generations and their headers differ (Tailwind
`<header class="bg-white ...">` for the C20 + template family, a plain
`<header>` with `.header-right` for the older C18 family, and the C21 family
which already shipped its own button).  What they share is a header whose last
top-level child is the right-hand group, so the button is appended inside that
group -- which lands it at the right-hand end on every generation.  The CSS and
the JS are self-contained (no Tailwind classes), so they work in all of them.

Idempotent: a file that already has `id="fullscreen-btn"` is left alone.

    python3 dev/scripts/add_fullscreen.py              # every test + template
    python3 dev/scripts/add_fullscreen.py path.html …  # only these
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CSS = """
    <style>
      /* Full screen button (dev/scripts/add_fullscreen.py) */
      #fullscreen-btn{display:inline-flex;align-items:center;justify-content:center;
        flex:0 0 auto;width:34px;height:34px;padding:0;margin-left:8px;
        border:1px solid #e5e7eb;border-radius:8px;background:#fff;color:#4b5563;
        cursor:pointer;transition:background .15s,color .15s,box-shadow .15s}
      #fullscreen-btn:hover{background:#f3f4f6;color:#111827;box-shadow:0 1px 2px rgba(0,0,0,.08)}
      #fullscreen-btn:active{transform:translateY(1px)}
      #fullscreen-btn svg{width:18px;height:18px;display:block}
      #fullscreen-btn .fs-i-exit{display:none}
      #fullscreen-btn.is-fs .fs-i-enter{display:none}
      #fullscreen-btn.is-fs .fs-i-exit{display:block}
    </style>
"""

BUTTON = """
        <button id="fullscreen-btn" type="button" title="Full screen" aria-label="Full screen">
          <svg class="fs-i-enter" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>
          <svg class="fs-i-exit" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>
        </button>
"""

JS = """
<script>
/* Full screen toggle (dev/scripts/add_fullscreen.py) */
(function () {
  var btn = document.getElementById('fullscreen-btn');
  if (!btn) return;
  var root = document.documentElement;
  function isFs() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
  }
  function sync() {
    var f = isFs();
    btn.classList.toggle('is-fs', f);
    btn.title = f ? 'Exit full screen' : 'Full screen';
    btn.setAttribute('aria-label', btn.title);
  }
  btn.addEventListener('click', function () {
    if (!isFs()) {
      var req = root.requestFullscreen || root.webkitRequestFullscreen || root.msRequestFullscreen;
      if (req) req.call(root);
    } else {
      var exit = document.exitFullscreen || document.webkitExitFullscreen || document.msExitFullscreen;
      if (exit) exit.call(document);
    }
  });
  ['fullscreenchange', 'webkitfullscreenchange', 'MSFullscreenChange'].forEach(function (ev) {
    document.addEventListener(ev, sync);
  });
  sync();
})();
</script>
"""


def targets():
    out = []
    for folder in ('listening', 'reading'):
        out += sorted((ROOT / folder).rglob('*.html'))
    for tpl in ('reading.html', 'listening.html'):
        p = ROOT / 'dev' / 'templates' / tpl
        if p.exists():
            out.append(p)
    return out


VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
TAG = re.compile(r'<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>')


def children(inner):
    """Top-level (depth 0) element children of `inner`, as (name, start, end)."""
    out, depth, open_at, open_name = [], 0, None, None
    for m in TAG.finditer(inner):
        closing, name, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if name in VOID or selfclose == '/':
            continue
        if not closing:
            if depth == 0:
                open_at, open_name = m.start(), name
            depth += 1
        else:
            depth -= 1
            if depth == 0 and open_at is not None:
                out.append((open_name, open_at, m.end()))
                open_at = None
            elif depth < 0:          # stray close tag -- give up on nesting
                depth = 0
    return out


def insert_button(html):
    """Append the button inside the last group of the header."""
    m = re.search(r'<header[\s>][^>]*>', html, re.I)
    if not m:
        return None
    end = html.lower().find('</header>', m.end())
    if end == -1:
        return None
    base, inner = m.end(), html[m.end():end]

    # A header with a single wrapper div: step into it, its children are the groups.
    kids = children(inner)
    if len(kids) == 1 and kids[0][0] == 'div':
        name, s0, e0 = kids[0]
        open_len = TAG.match(inner, s0).end() - s0
        base, inner = base + s0 + open_len, inner[s0 + open_len:e0 - len('</div>')]
        kids = children(inner)

    if kids and kids[-1][0] == 'div':
        # last group is a container -- put the button inside it, at the end
        at = base + kids[-1][2] - len('</div>')
    elif kids:
        at = base + kids[-1][2]      # no container: sit next to the last child
    else:
        at = base + len(inner)
    return html[:at] + BUTTON.strip('\n') + '\n      ' + html[at:]


def patch(path):
    html = path.read_text(encoding='utf-8')
    if 'id="fullscreen-btn"' in html:
        return 'has it already'
    out = insert_button(html)
    if out is None:
        return 'SKIPPED: no <header> found'
    i = out.lower().rfind('</head>')
    if i == -1:
        return 'SKIPPED: no </head> found'
    out = out[:i] + CSS.strip('\n') + '\n  ' + out[i:]
    j = out.lower().rfind('</body>')
    if j == -1:
        return 'SKIPPED: no </body> found'
    out = out[:j] + JS.strip('\n') + '\n' + out[j:]
    path.write_text(out, encoding='utf-8')
    return 'added'


def main(argv):
    files = [Path(a).resolve() for a in argv] or targets()
    for f in files:
        print(f'{patch(f):<22} {f.relative_to(ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1:])
