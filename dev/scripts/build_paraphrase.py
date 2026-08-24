#!/usr/bin/env python3
"""Build the paraphrase practice page from vocab/paraphrases.json.

The bank stores, per test, the pairs of wordings that mean the same thing —
what the question said vs what the passage said ("feeling of" / "sense of").
This turns them into generated/paraphrase/paraphrase.html: flip cards, a
matching game and a browsable list, filtered by test.

Never hand-edit the output — run this (or dev/scripts/build_index.py, which
calls it) instead. Adding pairs is the paraphrase-bank skill's job.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "vocab", "paraphrases.json")
OUT = os.path.join(ROOT, "generated", "paraphrase", "paraphrase.html")


def kind(test):
    """C20-r1 -> reading, C21-l3 -> listening."""
    m = re.search(r'-([rl])\d', test.lower())
    return {"r": "reading", "l": "listening"}.get(m.group(1) if m else "", "reading")


def load():
    if not os.path.exists(SRC):
        return []
    bank = json.load(open(SRC, encoding="utf-8"))
    out = []
    for test in sorted(bank):
        for pair in bank[test]:
            row = dict(pair)
            row["test"] = test
            row["type"] = kind(test)
            out.append(row)
    return out


PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<meta name="theme-color" content="#1e6de6"/>
<title>Paraphrase Practice — English Vault</title>
<style>
  :root{
    --bg:#f5f8fd;--card:#fff;--ink:#0f172a;--ink2:#475569;--ink3:#8a94a6;
    --line:#e6eaf1;--line2:#eef2f8;--soft:#eff4fb;
    --blue:#1e6de6;--blue2:#3b82f6;--blued:#0f2f66;--bluebg:#eff6ff;
    --green:#16a34a;--greenbg:#effdf4;--amber:#b45309;--amberbg:#fff7ed;
    --red:#dc2626;--redbg:#fef2f2;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased;padding-bottom:60px}
  .wrap{max-width:720px;margin:0 auto;padding:22px 20px}
  .hero{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;border-radius:20px;
    padding:18px 24px 24px;box-shadow:0 14px 36px rgba(30,109,230,.24);margin-bottom:18px}
  .nav{display:flex;gap:6px;margin:0 -4px 12px}
  .nav a{font-size:13px;font-weight:600;color:#dbeafe;text-decoration:none;padding:7px 13px;border-radius:999px;transition:.12s}
  .nav a:hover{background:rgba(255,255,255,.16);color:#fff}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#bfdbfe}
  h1{font-weight:800;font-size:26px;margin:8px 0 6px;letter-spacing:-.02em;color:#fff}
  .lede{color:#dbeafe;font-size:14px;margin:0}
  .lab{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin:0 2px 8px}
  .switch{display:inline-flex;flex-wrap:wrap;border:1px solid var(--line);border-radius:999px;padding:3px;background:var(--card);gap:2px;margin-bottom:14px}
  .switch button{border:none;background:none;border-radius:999px;padding:7px 13px;font-size:12.5px;font-weight:600;color:var(--ink2);cursor:pointer}
  .switch button[aria-pressed="true"]{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff}
  .switch button:disabled{opacity:.45;cursor:default}
  .count{font-family:var(--mono);font-size:12px;color:var(--ink3);margin:6px 2px 14px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:10px;box-shadow:0 1px 3px rgba(16,24,40,.05)}
  .srcrow{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
  .badge{font-size:10px;font-weight:800;padding:3px 9px;border-radius:999px;letter-spacing:.02em}
  .badge.reading{background:var(--bluebg);color:var(--blue)}
  .badge.listening{background:var(--amberbg);color:var(--amber)}
  .qno{font-family:var(--mono);font-size:11px;color:var(--ink3)}
  .side{margin:0 0 4px}
  .side .tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}
  .phrase{font-size:20px;font-weight:700;letter-spacing:-.01em;line-height:1.35;margin:2px 0 0}
  .phrase.p{color:var(--blue)}
  .phrase.q{color:var(--blued)}
  .arrow{color:var(--ink3);font-size:18px;text-align:center;margin:10px 0 6px}
  .ctx{font-size:14px;color:var(--ink2);line-height:1.6;border-left:2px solid var(--line);padding-left:11px;margin-top:8px}
  .ctx b{background:#fff3c4;color:var(--ink);font-weight:700;border-radius:3px;padding:0 2px}
  .uz{font-size:14px;color:var(--green);margin-top:10px;font-weight:600}
  .btn{border:1px solid var(--line);background:var(--soft);color:var(--ink);border-radius:12px;
    padding:12px;font-size:14px;font-weight:700;cursor:pointer;width:100%}
  .btn.primary{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;border:none}
  .row2{display:flex;gap:8px;margin-top:12px}
  .hidden{display:none!important}
  .prog{height:4px;background:var(--line2);border-radius:999px;overflow:hidden;margin:0 2px 14px}
  .prog i{display:block;height:100%;background:var(--blue);width:0;transition:width .2s}
  /* match game */
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .cols .colhead{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);padding:0 2px 4px}
  .tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:11px 12px;font-size:14.5px;
    font-weight:600;cursor:pointer;margin-bottom:8px;text-align:left;width:100%;color:var(--ink);line-height:1.4;transition:.12s}
  .tile:hover{border-color:var(--blue2)}
  .tile.sel{border-color:var(--blue);box-shadow:0 0 0 3px rgba(30,109,230,.14)}
  .tile.ok{background:var(--greenbg);border-color:#bbf7d0;color:var(--green);cursor:default}
  .tile.bad{background:var(--redbg);border-color:#fecaca;color:var(--red)}
  .empty{color:var(--ink2);padding:40px 4px;text-align:center}
  .hint{font-family:var(--mono);font-size:11px;color:var(--ink3);margin:-6px 2px 16px}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <nav class="nav">
      <a href="../../dev/index.html">Home</a>
      <a href="../../dev/player.html">Player</a>
      <a href="../../dev/progress.html">Progress</a>
    </nav>
    <div class="eyebrow">🔁 English Vault · Paraphrase</div>
    <h1>Paraphrase practice</h1>
    <p class="lede">The question never uses the passage's words. Every pair here is one you have already met in a test — learn them and you spot the answer faster.</p>
  </div>

  <div class="lab">Mode</div>
  <div class="switch" id="modeSwitch">
    <button data-mode="cards" aria-pressed="true">Flip cards</button>
    <button data-mode="match">Match</button>
    <button data-mode="browse">Browse</button>
  </div>

  <div class="lab">Test</div>
  <div class="switch" id="testSwitch"></div>

  <div class="lab" id="dirLab">Direction</div>
  <div class="switch" id="dirSwitch">
    <button data-dir="p2q" aria-pressed="true">Passage → question</button>
    <button data-dir="q2p">Question → passage</button>
    <button data-dir="mix">Mixed</button>
  </div>

  <div class="count" id="count"></div>
  <div class="prog" id="prog"><i></i></div>
  <div id="view"></div>
  <div id="empty" class="empty hidden">No pairs yet — collect some with the paraphrase-bank skill.</div>
</div>
<script>
const DATA = __DATA__;
</script>
<script>
"""

PAGE_TAIL = r"""
const esc = s => String(s == null ? '' : s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const view = document.getElementById('view');
const countEl = document.getElementById('count');
const progEl = document.getElementById('prog').firstElementChild;
const emptyEl = document.getElementById('empty');

let mode = 'cards', test = 'all', dir = 'p2q';
let order = [], at = 0, shown = false;

/* ---- highlight the phrase inside its sentence ---- */
function mark(sentence, phrase) {
  if (!sentence) return '';
  const s = esc(sentence), needle = esc(phrase);
  const hit = (hay, what) => hay.toLowerCase().indexOf(what.toLowerCase());
  let i = hit(s, needle), len = needle.length;
  if (i < 0) {
    // the phrase is often quoted with an ellipsis ("we observe ... we create"),
    // so fall back to its first few words rather than showing no highlight
    const words = needle.split(/\s+/);
    for (let n = Math.min(5, words.length); n >= 2 && i < 0; n--) {
      const head = words.slice(0, n).join(' ');
      i = hit(s, head); len = head.length;
    }
  }
  if (i < 0) return s;
  return s.slice(0, i) + '<b>' + s.slice(i, i + len) + '</b>' + s.slice(i + len);
}

function pool() { return test === 'all' ? DATA : DATA.filter(d => d.test === test); }

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

/* ---- the test filter is built from the data ---- */
(function buildTestSwitch() {
  const wrap = document.getElementById('testSwitch');
  const tests = [...new Set(DATA.map(d => d.test))].sort();
  const mk = (val, label) => {
    const b = document.createElement('button');
    b.dataset.test = val; b.textContent = label;
    b.setAttribute('aria-pressed', String(val === 'all'));
    b.onclick = () => { test = val; [...wrap.children].forEach(c => c.setAttribute('aria-pressed', String(c.dataset.test === val))); reset(); };
    wrap.appendChild(b);
  };
  mk('all', 'All');
  tests.forEach(t => mk(t, t));
})();

document.getElementById('modeSwitch').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  mode = b.dataset.mode;
  [...b.parentElement.children].forEach(c => c.setAttribute('aria-pressed', String(c === b)));
  reset();
});
document.getElementById('dirSwitch').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  dir = b.dataset.dir;
  [...b.parentElement.children].forEach(c => c.setAttribute('aria-pressed', String(c === b)));
  reset();
});

function reset() {
  const n = pool().length;
  emptyEl.classList.toggle('hidden', n > 0);
  document.getElementById('dirLab').classList.toggle('hidden', mode !== 'cards');
  document.getElementById('dirSwitch').classList.toggle('hidden', mode !== 'cards');
  document.getElementById('prog').classList.toggle('hidden', mode !== 'cards');
  order = shuffle(pool().slice()); at = 0; shown = false;
  render();
}

/* ---------------------------------------------------------------- cards */
function frontSide(d) {
  if (dir === 'q2p') return 'q';
  if (dir === 'p2q') return 'p';
  return (d.qno && Number(d.qno) % 2) ? 'q' : 'p';
}

function cardHtml(d) {
  const f = frontSide(d), b = f === 'q' ? 'p' : 'q';
  const label = { q: 'The question said', p: 'The passage said' };
  const ctx = { q: d.qtext, p: d.ptext };
  return `<div class="card">
    <div class="srcrow"><span class="badge ${esc(d.type)}">${esc(d.test)}</span>
      ${d.qno ? `<span class="qno">Q${esc(d.qno)}</span>` : ''}</div>
    <div class="side"><div class="tag">${label[f]}</div><div class="phrase ${f}">${esc(d[f])}</div></div>
    ${ctx[f] ? `<div class="ctx">${mark(ctx[f], d[f])}</div>` : ''}
    <div class="arrow">↓</div>
    ${shown ? `<div class="side"><div class="tag">${label[b]}</div><div class="phrase ${b}">${esc(d[b])}</div></div>
        ${ctx[b] ? `<div class="ctx">${mark(ctx[b], d[b])}</div>` : ''}
        ${d.uz ? `<div class="uz">${esc(d.uz)}</div>` : ''}`
      : `<div class="side"><div class="phrase" style="color:var(--ink3)">· · ·</div></div>`}
    <div class="row2">
      ${shown ? `<button class="btn primary" id="next">Next →</button>`
              : `<button class="btn primary" id="reveal">Show the other wording</button>`}
    </div>
  </div>`;
}

function renderCards() {
  if (!order.length) { view.innerHTML = ''; countEl.textContent = ''; progEl.style.width = '0'; return; }
  if (at >= order.length) {
    view.innerHTML = `<div class="card" style="text-align:center">
      <div class="phrase">Done — ${order.length} pairs</div>
      <div class="row2"><button class="btn primary" id="again">Go again</button></div></div>`;
    countEl.textContent = '';
    progEl.style.width = '100%';
    document.getElementById('again').onclick = reset;
    return;
  }
  view.innerHTML = cardHtml(order[at]);
  countEl.textContent = `${at + 1} / ${order.length}`;
  progEl.style.width = ((at) / order.length * 100) + '%';
  const rev = document.getElementById('reveal'), nxt = document.getElementById('next');
  if (rev) rev.onclick = () => { shown = true; renderCards(); };
  if (nxt) nxt.onclick = () => { at++; shown = false; renderCards(); };
}

document.addEventListener('keydown', e => {
  if (mode !== 'cards') return;
  const t = e.target;
  if (t && t.closest && t.closest('input,textarea,[contenteditable]')) return;
  if (e.key === ' ' || e.key === 'Enter' || e.key === 'ArrowRight') {
    e.preventDefault();
    if (!shown) { shown = true; } else { at++; shown = false; }
    renderCards();
  }
});

/* ---------------------------------------------------------------- match */
const ROUND = 5;
let matchSel = null, matchLeft = [];

function renderMatch() {
  const all = pool();
  if (!all.length) { view.innerHTML = ''; countEl.textContent = ''; return; }
  if (!matchLeft.length) matchLeft = shuffle(all.slice());
  const round = matchLeft.slice(0, ROUND);
  const left = round.map((d, i) => ({ d, i }));
  const right = shuffle(round.map((d, i) => ({ d, i })));
  countEl.textContent = `${matchLeft.length} left · tap a question wording, then its passage wording`;
  view.innerHTML = `<div class="cols">
    <div><div class="colhead">Question wording</div>
      ${left.map(x => `<button class="tile" data-side="q" data-i="${x.i}">${esc(x.d.q)}</button>`).join('')}</div>
    <div><div class="colhead">Passage wording</div>
      ${right.map(x => `<button class="tile" data-side="p" data-i="${x.i}">${esc(x.d.p)}</button>`).join('')}</div>
  </div>
  <div class="row2"><button class="btn" id="skipRound">New set →</button></div>`;

  document.getElementById('skipRound').onclick = () => { matchLeft = matchLeft.slice(ROUND); matchSel = null; renderMatch(); };

  let solved = 0;
  view.querySelectorAll('.tile').forEach(tile => {
    tile.onclick = () => {
      if (tile.classList.contains('ok')) return;
      if (!matchSel) { matchSel = tile; tile.classList.add('sel'); return; }
      if (matchSel === tile) { tile.classList.remove('sel'); matchSel = null; return; }
      if (matchSel.dataset.side === tile.dataset.side) {
        matchSel.classList.remove('sel'); matchSel = tile; tile.classList.add('sel'); return;
      }
      const hit = matchSel.dataset.i === tile.dataset.i;
      const a = matchSel; matchSel = null; a.classList.remove('sel');
      if (hit) {
        a.classList.add('ok'); tile.classList.add('ok');
        if (++solved >= round.length) {
          setTimeout(() => { matchLeft = matchLeft.slice(ROUND); renderMatch(); }, 650);
        }
      } else {
        a.classList.add('bad'); tile.classList.add('bad');
        setTimeout(() => { a.classList.remove('bad'); tile.classList.remove('bad'); }, 420);
      }
    };
  });
}

/* --------------------------------------------------------------- browse */
function renderBrowse() {
  const all = pool();
  countEl.textContent = `${all.length} pair${all.length === 1 ? '' : 's'}`;
  view.innerHTML = all.map(d => `<div class="card">
    <div class="srcrow"><span class="badge ${esc(d.type)}">${esc(d.test)}</span>
      ${d.qno ? `<span class="qno">Q${esc(d.qno)}</span>` : ''}</div>
    <div class="side"><div class="tag">The question said</div><div class="phrase q">${esc(d.q)}</div></div>
    ${d.qtext ? `<div class="ctx">${mark(d.qtext, d.q)}</div>` : ''}
    <div class="arrow">↓</div>
    <div class="side"><div class="tag">The passage said</div><div class="phrase p">${esc(d.p)}</div></div>
    ${d.ptext ? `<div class="ctx">${mark(d.ptext, d.p)}</div>` : ''}
    ${d.uz ? `<div class="uz">${esc(d.uz)}</div>` : ''}
  </div>`).join('');
}

function render() {
  if (mode === 'cards') renderCards();
  else if (mode === 'match') { matchSel = null; matchLeft = []; renderMatch(); }
  else renderBrowse();
}

reset();
</script>
</body>
</html>
"""


def main():
    rows = load()
    html = PAGE_HEAD.replace("__DATA__", json.dumps(rows, ensure_ascii=False)) + PAGE_TAIL
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    tests = len({r["test"] for r in rows})
    print(f"Wrote {OUT}  ({len(rows)} paraphrase pairs from {tests} test(s))")


if __name__ == "__main__":
    main()
