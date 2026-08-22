#!/usr/bin/env python3
"""Regenerate /generated/translate/translate.html — a translation-practice page.

Reads the curated sentence store at vocab/translations.json (difficult sentences
pulled from finished reading passages and listening scripts, each with an Uzbek
translation) and renders a self-contained page:

  * sentences shown in groups of 20 (1–20, 21–40, …) — pick a group to study it,
  * a Reading / Listening / All filter,
  * each sentence has a "Show translation" button that reveals the Uzbek,
  * a "Can't translate it" button that breaks the sentence into chunks, each
    labelled with its job in the sentence (Subject, Verb, Time phrase, …) and
    translated on its own, plus a note on the sentence's structure,
  * every word that is NOT in vocab/known.md is underlined with a dashed line;
    tapping it opens a word card (Uzbek, meaning, synonyms) built from
    vocab/learning.json + vocab/need-to-review.json, falling back to
    vocab/glossary.json,
  * light blue-gradient theme matching the rest of the vault.

The store is the single source of truth: when a passage is finished (moved to
done), add its hard sentences + translations to vocab/translations.json and
rebuild. This script is called from scripts/build_index.py, so the page always
updates on a rebuild.

Usage:
    python3 scripts/build_translate.py
"""
import os, re, json, html

# scripts/ now lives in dev/, so the site root is two levels up, not one.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORE = os.path.join(ROOT, "vocab", "translations.json")
KNOWN = os.path.join(ROOT, "vocab", "known.md")
GLOSS = os.path.join(ROOT, "vocab", "glossary.json")
CARD_STORES = [os.path.join(ROOT, "vocab", "learning.json"),
               os.path.join(ROOT, "vocab", "need-to-review.json")]
OUT = os.path.join(ROOT, "generated", "translate", "translate.html")


def load():
    if not os.path.exists(STORE):
        return []
    try:
        data = json.load(open(STORE, encoding="utf-8"))
    except Exception as e:
        print(f"WARNING: could not read {STORE} ({e})")
        return []
    out = []
    for row in data:
        en = str(row.get("en", "")).strip()
        if not en:
            continue
        out.append({
            "en": en,
            "uz": str(row.get("uz", "")).strip(),
            "src": str(row.get("src", "")).strip(),
            "type": (row.get("type") or "reading").strip().lower(),
            "structure": str(row.get("structure", "")).strip(),
            "chunks": [{"en": str(c.get("en", "")).strip(),
                        "role": str(c.get("role", "")).strip(),
                        "uz": str(c.get("uz", "")).strip()}
                       for c in (row.get("chunks") or []) if c.get("en")],
        })
    return out


# ---- unknown words -------------------------------------------------------

def load_known():
    """Every word listed in vocab/known.md (it is plain space-separated text)."""
    if not os.path.exists(KNOWN):
        return set()
    out = set()
    for line in open(KNOWN, encoding="utf-8"):
        if line.lstrip().startswith("#"):
            continue
        out.update(w.strip().lower() for w in line.split() if w.strip())
    return out


def variants(t):
    """Crude morphology, so 'collections' counts as known when 'collection' is.

    Only used to decide whether a word needs help — a false match just means one
    fewer underline, never a wrong translation.
    """
    v = {t}
    if t.endswith("'s"):            # artist's -> artist
        v.add(t[:-2])
    if t.endswith("'"):             # artists' -> artists
        v.add(t[:-1])
    for suf, adds in (("ies", ["y"]), ("es", [""]), ("s", [""]), ("ed", ["", "e"]),
                      ("ing", ["", "e"]), ("ly", [""]), ("d", [""]),
                      ("er", ["", "e"]), ("est", ["", "e"])):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            for a in adds:
                v.add(t[:-len(suf)] + a)
    if "-" in t:
        v.update(x for x in t.split("-") if x)
    return v


def load_help():
    """word -> {uz, def, syn, ex}: the rich vocab cards first, glossary second."""
    help_ = {}
    if os.path.exists(GLOSS):
        try:
            g = json.load(open(GLOSS, encoding="utf-8")).get("words", {})
            for w, e in g.items():
                help_[w.lower()] = {"uz": e.get("uz", ""), "def": e.get("def", ""),
                                    "syn": list(e.get("syn") or []), "ex": e.get("ex", "")}
        except Exception as e:
            print(f"WARNING: could not read {GLOSS} ({e})")
    for path in CARD_STORES:                    # cards win — they are richer
        if not os.path.exists(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"WARNING: could not read {path} ({e})")
            continue
        for cards in data.values():
            for c in cards:
                w = str(c.get("w", "")).strip().lower()
                if not w:
                    continue
                help_[w] = {"uz": c.get("uz", ""), "def": c.get("def", ""),
                            "syn": list(c.get("syn") or []), "ex": c.get("ex", "")}
    return help_


WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")


def mark_unknown(sentence, known, help_):
    """Return (html, {key: entry}) — unknown words wrapped in a tappable span.

    A word is unknown when neither it nor a simple variant of it appears in
    known.md. Capitalised words after the first are treated as names and left
    alone. A word with no help entry is still underlined, but not clickable.
    """
    out, used, pos, first = [], {}, 0, True
    for m in WORD_RE.finditer(sentence):
        raw = m.group(0)
        t = raw.lower().replace("\u2019", "'")
        out.append(html.escape(sentence[pos:m.start()]))
        pos = m.end()
        is_name = raw[0].isupper() and not first
        first = False
        if is_name or any(v in known for v in variants(t)):
            out.append(html.escape(raw))
            continue
        key = next((v for v in (t,) + tuple(sorted(variants(t))) if v in help_), None)
        if key:
            used[key] = help_[key]
            out.append(f'<span class="uw" data-w="{html.escape(key, quote=True)}"'
                       f' role="button" tabindex="0">{html.escape(raw)}</span>')
        else:
            out.append(f'<span class="uw nohelp">{html.escape(raw)}</span>')
            used.setdefault("__missing__", {})[t] = True
    out.append(html.escape(sentence[pos:]))
    return "".join(out), used


PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<meta name="theme-color" content="#1e6de6"/>
<title>Translation Practice — English Vault</title>
<style>
  :root{
    --bg:#f5f8fd;--card:#fff;--ink:#0f172a;--ink2:#475569;--ink3:#8a94a6;
    --line:#e6eaf1;--line2:#eef2f8;--soft:#eff4fb;
    --blue:#1e6de6;--blue2:#3b82f6;--blued:#0f2f66;--bluebg:#eff6ff;
    --green:#16a34a;--greenbg:#effdf4;--amber:#b45309;--amberbg:#fff7ed;
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
  .switch button:disabled{opacity:.5}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 16px;margin-bottom:10px;box-shadow:0 1px 3px rgba(16,24,40,.05)}
  .srcrow{display:flex;align-items:center;gap:8px;margin-bottom:8px}
  .badge{font-size:10px;font-weight:800;padding:3px 9px;border-radius:999px;letter-spacing:.02em}
  .badge.reading{background:var(--bluebg);color:var(--blue)}
  .badge.listening{background:var(--greenbg);color:var(--green)}
  .src{font-family:var(--mono);font-size:11px;color:var(--ink3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .en{font-size:16px;line-height:1.6;color:var(--ink)}
  .showbtn{margin-top:12px;display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;color:var(--blue);
    background:var(--bluebg);border:1px solid #d3e2fb;border-radius:999px;padding:7px 13px;cursor:pointer;transition:.12s}
  .showbtn:hover{background:#e0edff}
  .uz{display:none;margin-top:12px;padding-top:12px;border-top:1px dashed var(--line);font-size:15.5px;line-height:1.6;color:var(--blued)}
  .uz.open{display:block}
  .uz .flag{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);display:block;margin-bottom:4px}
  /* unknown word — dashed underline, tap for a word card */
  .uw{border-bottom:1px dashed var(--blue2);cursor:pointer;color:var(--blued);
    padding-bottom:1px;transition:background .12s}
  .uw:hover,.uw:focus-visible{background:var(--bluebg);outline:none;border-bottom-style:solid}
  .uw.nohelp{border-bottom-color:var(--ink3);color:inherit;cursor:default}
  .uw.nohelp:hover{background:none;border-bottom-style:dashed}
  /* chunk breakdown */
  .btnrow{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
  .helpbtn{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;
    color:var(--amber);background:var(--amberbg);border:1px solid #f6dfc0;border-radius:999px;
    padding:7px 13px;cursor:pointer;transition:.12s}
  .helpbtn:hover{background:#fdeedd}
  .breakdown{display:none;margin-top:14px;padding-top:13px;border-top:1px dashed var(--line)}
  .breakdown.open{display:block}
  .struct{background:var(--amberbg);border:1px solid #f6dfc0;border-radius:11px;
    padding:10px 12px;font-size:13.5px;line-height:1.55;color:#7a4a12;margin-bottom:12px}
  .struct b{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
    display:block;margin-bottom:4px;color:var(--amber)}
  .chunk{display:grid;grid-template-columns:22px 1fr;gap:10px;padding:9px 0;border-top:1px solid var(--line2)}
  .chunk:first-of-type{border-top:none}
  .chunk .n{font-family:var(--mono);font-size:11px;color:var(--ink3);padding-top:3px}
  .chunk .ce{font-size:15px;line-height:1.5;color:var(--ink)}
  .chunk .role{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.04em;
    background:var(--soft);border:1px solid var(--line);color:var(--ink2);
    border-radius:999px;padding:2px 8px;margin:5px 0 4px}
  .chunk .cu{font-size:14.5px;line-height:1.5;color:var(--blued)}
  .whole{margin-top:12px;padding-top:11px;border-top:1px solid var(--line2);
    font-size:15px;line-height:1.6;color:var(--blued)}
  .whole .flag{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;
    color:var(--ink3);display:block;margin-bottom:4px}
  /* word modal */
  .modal{position:fixed;inset:0;z-index:80;display:none;align-items:flex-end;justify-content:center;
    background:rgba(15,23,42,.42);padding:0}
  .modal.open{display:flex}
  .sheet{background:var(--card);width:100%;max-width:520px;border-radius:20px 20px 0 0;
    padding:20px 20px calc(22px + env(safe-area-inset-bottom));
    box-shadow:0 -12px 40px rgba(15,23,42,.28);max-height:82vh;overflow:auto;
    animation:up .18s ease-out}
  @keyframes up{from{transform:translateY(18px);opacity:.6}to{transform:none;opacity:1}}
  @media (min-width:560px){
    .modal{align-items:center;padding:20px}
    .sheet{border-radius:18px;animation:none}
  }
  .sheet .w{font-size:23px;font-weight:800;letter-spacing:-.01em}
  .sheet .wuz{color:var(--blue);font-size:16px;font-weight:700;margin-top:2px}
  .sheet .wdef{margin-top:12px;font-size:15px;line-height:1.6;color:var(--ink2)}
  .sheet .wex{margin-top:10px;font-size:14.5px;line-height:1.6;color:var(--ink2);
    border-left:2px solid var(--line);padding-left:11px;font-style:italic}
  .sheet .syns{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}
  .sheet .syns .lbl{width:100%;margin:0 0 2px}
  .sheet .syn{font-family:var(--mono);font-size:11.5px;background:var(--bluebg);color:var(--blue);
    border:1px solid #d3e2fb;border-radius:999px;padding:4px 10px}
  .sheet .close{margin-top:18px;width:100%;border:1px solid var(--line);background:var(--soft);
    color:var(--ink);border-radius:12px;padding:12px;font-size:14px;font-weight:700;cursor:pointer}
  .hint{font-family:var(--mono);font-size:11px;color:var(--ink3);margin:-6px 2px 16px}
  .empty{color:var(--ink2);padding:40px 4px;text-align:center}
  .count{font-family:var(--mono);font-size:12px;color:var(--ink3);margin:6px 2px 16px}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <nav class="nav">
      <a href="../../index.html">Home</a>
      <a href="../../player.html">Player</a>
      <a href="../../progress.html">Progress</a>
    </nav>
    <div class="eyebrow">📖 English Vault · Translation</div>
    <h1>Translation practice</h1>
    <p class="lede">Difficult sentences from finished passages and listening scripts. Read the English, then reveal the Uzbek.</p>
  </div>

  <div class="lab">Source</div>
  <div class="switch" id="typeSwitch">
    <button data-type="all" aria-pressed="true">All</button>
    <button data-type="reading">Reading</button>
    <button data-type="listening">Listening</button>
  </div>

  <div class="lab">Group of 20</div>
  <div class="switch" id="groupSwitch"></div>

  <div class="count" id="count"></div>
  <div class="hint">Words with a dashed underline aren't in your known list — tap one for its meaning.</div>
  <div id="list"></div>
  <div id="empty" class="empty" style="display:none">No sentences yet — add some to vocab/translations.json.</div>
</div>

<div class="modal" id="wordModal" role="dialog" aria-modal="true" aria-labelledby="mWord">
  <div class="sheet" id="wordSheet">
    <div class="w" id="mWord"></div>
    <div class="wuz" id="mUz"></div>
    <div class="wdef" id="mDef"></div>
    <div class="wex" id="mEx"></div>
    <div class="syns" id="mSyn"></div>
    <button class="close" id="mClose">Close</button>
  </div>
</div>
<script>
const DATA = __DATA__;
const HELP = __HELP__;
"""

PAGE_TAIL = r"""
const GROUP=20;
let type="all", groupIndex=0;
const listEl=document.getElementById('list');
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

function pool(){ return type==="all" ? DATA : DATA.filter(d=>d.type===type); }
function ranges(){ const n=pool().length, out=[]; for(let i=0;i<n;i+=GROUP) out.push([i,Math.min(i+GROUP,n)]); return out; }

function renderGroups(){
  const rs=ranges(), box=document.getElementById('groupSwitch');
  if(groupIndex>=rs.length) groupIndex=0;
  box.innerHTML="";
  if(!rs.length){ box.innerHTML='<button aria-pressed="true" disabled>—</button>'; return; }
  rs.forEach(([s,e],k)=>{
    const b=document.createElement('button'); b.dataset.g=k; b.textContent=(s+1)+"–"+e;
    if(k===groupIndex) b.setAttribute('aria-pressed','true');
    box.appendChild(b);
  });
}

function render(){
  const rs=ranges(); const r=rs[groupIndex];
  const items = r ? pool().slice(r[0], r[1]) : [];
  document.getElementById('count').textContent = pool().length + " sentence" + (pool().length===1?"":"s") + (rs.length>1 ? " · group "+(groupIndex+1)+"/"+rs.length : "");
  document.getElementById('empty').style.display = pool().length ? "none" : "block";
  listEl.innerHTML="";
  items.forEach((d,i)=>{
    const card=document.createElement('div'); card.className='card';
    const t = d.type==="listening" ? "listening" : "reading";
    // d.enHtml is built at build time: unknown words already wrapped in .uw spans
    card.innerHTML =
      `<div class="srcrow"><span class="badge ${t}">${t}</span><span class="src">${esc(d.src||"")}</span></div>`+
      `<div class="en">${d.enHtml}</div>`+
      `<div class="btnrow">`+
        (d.uz ? `<button class="showbtn">🇺🇿 Show translation</button>` : ``)+
        (d.chunks && d.chunks.length ? `<button class="helpbtn">🧩 Can't translate it</button>` : ``)+
      `</div>`+
      (d.uz ? `<div class="uz"><span class="flag">Uzbek</span>${esc(d.uz)}</div>` : ``)+
      (d.chunks && d.chunks.length ? `<div class="breakdown">${breakdownHtml(d)}</div>` : ``);
    const btn=card.querySelector('.showbtn');
    if(btn){ btn.addEventListener('click',()=>{
      const uz=card.querySelector('.uz'); const open=uz.classList.toggle('open');
      btn.textContent = open ? "🇺🇿 Hide translation" : "🇺🇿 Show translation";
    }); }
    const hb=card.querySelector('.helpbtn');
    if(hb){ hb.addEventListener('click',()=>{
      const bd=card.querySelector('.breakdown'); const open=bd.classList.toggle('open');
      hb.textContent = open ? "🧩 Hide the breakdown" : "🧩 Can't translate it";
    }); }
    listEl.appendChild(card);
  });
}

// chunk-by-chunk breakdown: each piece of the sentence, what job it does, and its Uzbek
function breakdownHtml(d){
  let h = d.structure
    ? `<div class="struct"><b>How the sentence is built</b>${esc(d.structure)}</div>` : "";
  h += d.chunks.map((c,k)=>
    `<div class="chunk"><div class="n">${k+1}</div><div>`+
      `<div class="ce">${esc(c.en)}</div>`+
      (c.role ? `<span class="role">${esc(c.role)}</span>` : ``)+
      (c.uz ? `<div class="cu">${esc(c.uz)}</div>` : ``)+
    `</div></div>`).join("");
  if(d.uz) h += `<div class="whole"><span class="flag">All together</span>${esc(d.uz)}</div>`;
  return h;
}

// ---- word card modal ----
const modal=document.getElementById('wordModal');
let lastFocus=null;
function openWord(key){
  const e=HELP[key]; if(!e) return;
  lastFocus=document.activeElement;
  document.getElementById('mWord').textContent=key;
  const uz=document.getElementById('mUz'); uz.textContent=e.uz||""; uz.style.display=e.uz?"":"none";
  const df=document.getElementById('mDef'); df.textContent=e.def||""; df.style.display=e.def?"":"none";
  const ex=document.getElementById('mEx'); ex.textContent=e.ex?("“"+e.ex+"”"):""; ex.style.display=e.ex?"":"none";
  const sy=document.getElementById('mSyn');
  sy.innerHTML=(e.syn&&e.syn.length)
    ? `<span class="lab lbl">Synonyms</span>`+e.syn.map(x=>`<span class="syn">${esc(x)}</span>`).join("")
    : "";
  sy.style.display=(e.syn&&e.syn.length)?"":"none";
  modal.classList.add('open');
  document.getElementById('mClose').focus();
}
function closeWord(){
  modal.classList.remove('open');
  if(lastFocus&&lastFocus.focus) lastFocus.focus();
}
document.getElementById('mClose').addEventListener('click',closeWord);
modal.addEventListener('click',e=>{ if(e.target===modal) closeWord(); });
document.addEventListener('keydown',e=>{ if(e.key==="Escape"&&modal.classList.contains('open')) closeWord(); });
// one delegated listener for every underlined word on the page
listEl.addEventListener('click',e=>{
  const w=e.target.closest('.uw[data-w]'); if(w) openWord(w.dataset.w);
});
listEl.addEventListener('keydown',e=>{
  if(e.key!=="Enter"&&e.key!==" ") return;
  const w=e.target.closest&&e.target.closest('.uw[data-w]');
  if(w){ e.preventDefault(); openWord(w.dataset.w); }
});

document.getElementById('typeSwitch').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute('aria-pressed', x===b));
  type=b.dataset.type; groupIndex=0; renderGroups(); render();
});
document.getElementById('groupSwitch').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b||b.disabled) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute('aria-pressed', x===b));
  groupIndex=+b.dataset.g; render();
});

renderGroups();
render();
</script>
</body>
</html>
"""


def main():
    rows = load()
    known, help_ = load_known(), load_help()
    used, missing = {}, set()
    for r in rows:
        r["enHtml"], hit = mark_unknown(r["en"], known, help_)
        missing.update(hit.pop("__missing__", {}))
        used.update(hit)
    if missing:
        print("NOTE: no word help for " + ", ".join(sorted(missing))
              + " — add them to vocab/glossary.json")
    j = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE_HEAD.replace("__DATA__", j(rows)).replace("__HELP__", j(used))
            + PAGE_TAIL)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    nr = sum(1 for r in rows if r["type"] == "reading")
    nl = sum(1 for r in rows if r["type"] == "listening")
    nc = sum(1 for r in rows if r["chunks"])
    print(f"Wrote {OUT}  ({len(rows)} sentences: {nr} reading, {nl} listening; "
          f"{nc} with a chunk breakdown, {len(used)} words explained)")


if __name__ == "__main__":
    main()
