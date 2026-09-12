#!/usr/bin/env python3
"""Build generated/vocab/all-vocabs.html — every vocab card in the vault on one page.

Sources: vocab/learning.json (decks in progress) and vocab/need-to-review.json
(decks already finished). Cards that appear in more than one deck are merged into a
single entry that keeps every deck's own meaning.

The page itself is a self-contained A-Z browser: live search, deck / status / part-of-
speech filters, a letter rail, and a row that expands into the full card.

Run directly, or let dev/scripts/build_index.py run it.
"""
import json, os, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "generated", "vocab", "all-vocabs.html")


def load(name):
    p = os.path.join(ROOT, "vocab", name)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# keys whose auto-label would read badly
LABELS = {"mentalist-s1e1": "The Mentalist · S1E1"}


def deck_label(key):
    """'cambridge-21-test-2-listening' -> 'Cambridge 21 · Test 2 · Listening'."""
    if key in LABELS:
        return LABELS[key]
    s = key.replace("_", "-")
    s = re.sub(r"\bC(\d+)\b", r"Cambridge \1", s)
    s = re.sub(r"-r(\d+)\b", r"-reading-\1", s)
    parts = [p for p in s.split("-") if p]
    words, out = [], []
    for p in parts:
        words.append(p.capitalize() if not p.isdigit() else p)
    # group "cambridge 21" / "test 2" / "reading 3" so the label reads in chunks
    i = 0
    while i < len(words):
        if i + 1 < len(words) and words[i + 1].isdigit():
            out.append(words[i] + " " + words[i + 1]); i += 2
        else:
            out.append(words[i]); i += 1
    return " · ".join(out)


def sort_key(w):
    s = unicodedata.normalize("NFKD", w.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return (re.sub(r"[^a-z0-9 ]", "", s), w.lower())


def first_letter(w):
    for c in unicodedata.normalize("NFKD", w.lower()):
        if c.isalpha():
            return c.upper()
    return "#"


def collect():
    decks, entries = [], {}
    for fname, status in (("learning.json", "learning"), ("need-to-review.json", "review")):
        for key, cards in load(fname).items():
            if not isinstance(cards, list):
                continue
            decks.append({"id": key, "label": deck_label(key), "status": status, "n": len(cards)})
            for c in cards:
                w = str(c.get("w", "")).strip()
                if not w:
                    continue
                e = entries.setdefault(w.lower(), {"w": w, "l": first_letter(w), "v": []})
                v = {k: c.get(k) for k in ("form", "formUz", "pos", "ipa", "forms", "def", "uz",
                                          "senses", "ex", "syn", "ant", "related", "mnem")
                     if c.get(k)}
                v["deck"] = key
                v["st"] = status
                e["v"].append(v)
    out = sorted(entries.values(), key=lambda e: sort_key(e["w"]))
    return decks, out


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>All vocabulary — one place</title>
<style>
  :root{
    --paper:#FCFCFA; --card:#FFFFFF;
    --ink:#17170F; --ink-2:#57564C; --ink-3:#8A897E;
    --line:#E4E3DC; --line-2:#EFEEE8; --soft:#F4F3EC;
    --focus:#2E5AAC; --ok:#1F5C3A; --mark:#FBE7A2;
    --r:14px;
    --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased}
  .wrap{max-width:760px;margin:0 auto;padding:24px 18px 90px}
  a{color:inherit}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3)}
  h1{font-family:var(--serif);font-weight:600;font-size:29px;line-height:1.12;margin:6px 0 4px;letter-spacing:-.01em}
  .lede{color:var(--ink-2);font-size:14.5px;margin:0 0 4px}
  .home{font-family:var(--mono);font-size:12px;color:var(--ink-3);text-decoration:none}
  .home:hover{color:var(--ink)}

  .toolbar{position:sticky;top:0;z-index:20;background:var(--paper);padding:14px 0 10px;margin-top:14px;border-bottom:1px solid var(--line-2)}
  .searchbox{position:relative}
  .searchbox input{width:100%;font-family:inherit;font-size:16px;color:var(--ink);background:var(--card);
    border:1px solid var(--line);border-radius:999px;padding:12px 40px 12px 16px;outline:none}
  .searchbox input:focus{border-color:var(--ink)}
  .searchbox .clr{position:absolute;right:6px;top:50%;transform:translateY(-50%);border:none;background:none;
    color:var(--ink-3);font-size:18px;padding:6px 10px;display:none}
  .searchbox.has .clr{display:block}

  .filters{display:flex;gap:6px;overflow-x:auto;margin-top:10px;padding-bottom:2px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .filters::-webkit-scrollbar{display:none}
  .chip{flex:0 0 auto;border:1px solid var(--line);background:var(--card);color:var(--ink-2);border-radius:999px;
    padding:6px 12px;font-size:12.5px;white-space:nowrap;font-family:inherit;cursor:pointer}
  .chip:hover{border-color:var(--ink-3)}
  .chip[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
  .chip .n{font-family:var(--mono);font-size:11px;opacity:.6;margin-left:5px}
  .frow{display:flex;align-items:center;gap:8px;margin-top:10px}
  .flab{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);flex:0 0 auto;width:52px}

  .rail{display:flex;flex-wrap:wrap;gap:2px;margin:12px 0 2px}
  .rail button{border:none;background:none;color:var(--ink-3);font-family:var(--mono);font-size:11.5px;padding:3px 5px;border-radius:6px;cursor:pointer}
  .rail button:hover{background:var(--soft);color:var(--ink)}
  .rail button:disabled{opacity:.25;cursor:default}

  .count{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:14px 0 6px}
  .letter{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--ink-3);
    padding:16px 2px 6px;border-bottom:1px solid var(--line-2);position:sticky;top:0;background:var(--paper)}

  .item{border-bottom:1px solid var(--line-2)}
  .head{display:flex;align-items:baseline;gap:10px;width:100%;text-align:left;background:none;border:none;
    padding:12px 2px;font-family:inherit;color:inherit;cursor:pointer}
  .head:hover .w{text-decoration:underline;text-decoration-color:var(--line)}
  .w{font-family:var(--serif);font-size:19px;font-weight:600;flex:0 0 auto}
  .w mark{background:linear-gradient(transparent 62%,var(--mark) 62%);color:inherit;padding:0 1px}
  .pos{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);flex:0 0 auto}
  .uz{font-size:14px;color:var(--ink-2);flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .say{border:none;background:none;color:var(--ink-3);font-size:14px;padding:4px 6px;flex:0 0 auto;cursor:pointer}
  .say:hover{color:var(--ink)}

  .body{display:none;padding:0 2px 18px}
  .item.open .body{display:block}
  .item.open .head .w{text-decoration:none}
  .sense{border-left:2px solid var(--line);padding:2px 0 2px 12px;margin-bottom:14px}
  .sense .deck{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px}
  .sense .deck i{font-style:normal;color:var(--ok)}
  .def{font-size:15.5px;margin:0 0 4px}
  .uzfull{font-size:15px;color:var(--ink-2);margin:0 0 9px}
  .ex{font-family:var(--serif);font-style:italic;font-size:15.5px;color:var(--ink);background:var(--soft);
    border-radius:10px;padding:10px 12px;margin:0 0 9px}
  .meta{font-size:13.5px;color:var(--ink-2);margin:0 0 5px}
  .meta b{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);
    font-weight:400;margin-right:6px}
  .mnem{background:var(--soft);border-radius:10px;padding:10px 12px;margin-top:9px}
  .mnem .kw{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:5px}
  .mnem .kw b{color:var(--ink);text-transform:none;font-size:13.5px;letter-spacing:0}
  .mnem .story{font-family:var(--serif);font-style:italic;font-size:14.5px;margin:0}

  .empty{text-align:center;color:var(--ink-3);font-size:14px;padding:50px 0}
  .top{position:fixed;right:16px;bottom:16px;border:1px solid var(--line);background:var(--card);color:var(--ink-2);
    border-radius:999px;padding:10px 15px;font-size:12.5px;font-family:var(--mono);cursor:pointer;display:none;
    box-shadow:0 2px 10px rgba(0,0,0,.06)}
  .top.on{display:block}
  :focus-visible{outline:2px solid var(--focus);outline-offset:2px}
  @media (max-width:520px){ .flab{display:none} .uz{display:none} }
</style>
</head>
<body>
<div class="wrap">
  <a class="home" href="../../dev/index.html">← main page</a>
  <div class="eyebrow" style="margin-top:10px">Vocabulary · every deck</div>
  <h1>All vocabulary in one place</h1>
  <p class="lede">__LEDE__</p>

  <div class="toolbar">
    <div class="searchbox" id="sb">
      <input id="q" type="search" placeholder="Search word, meaning, Uzbek, example…" autocomplete="off" spellcheck="false" />
      <button class="clr" id="clr" aria-label="Clear search">×</button>
    </div>
    <div class="frow"><span class="flab">Status</span><div class="filters" id="fstatus"></div></div>
    <div class="frow"><span class="flab">Deck</span><div class="filters" id="fdeck"></div></div>
    <div class="frow"><span class="flab">Type</span><div class="filters" id="fpos"></div></div>
  </div>

  <div class="rail" id="rail"></div>
  <div class="count" id="count"></div>
  <div id="list"></div>
</div>
<button class="top" id="totop">↑ top</button>

<script>
const WORDS = __WORDS__;
const DECKS = __DECKS__;

const $ = s => document.querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* one searchable blob per word, built once */
WORDS.forEach(e => {
  const bits = [e.w];
  e.v.forEach(v => bits.push(v.def, v.uz, v.ex, v.form, v.formUz, v.forms, v.pos,
                             (v.syn||[]).join(" "), (v.ant||[]).join(" "),
                             (v.related||[]).join(" "), (v.senses||[]).join(" "),
                             v.mnem ? v.mnem.kw + " " + v.mnem.story : ""));
  e._s = bits.filter(Boolean).join(" ").toLowerCase();
  e._pos = [...new Set(e.v.map(v => (v.pos||"").split("/")[0].trim().toLowerCase()).filter(Boolean))];
  e._decks = [...new Set(e.v.map(v => v.deck))];
  e._st = [...new Set(e.v.map(v => v.st))];
});

const POS = [...new Set(WORDS.flatMap(e => e._pos))].sort();
const state = {q:"", status:"", deck:"", pos:""};

function chips(host, items, key){
  host.innerHTML = items.map(it =>
    `<button class="chip" data-v="${esc(it.v)}" aria-pressed="${state[key]===it.v}">${esc(it.label)}`
    + (it.n != null ? `<span class="n">${it.n}</span>` : "") + `</button>`).join("");
  host.querySelectorAll(".chip").forEach(b => b.onclick = () => {
    state[key] = state[key] === b.dataset.v ? "" : b.dataset.v;
    host.querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", state[key] === x.dataset.v));
    render();
  });
}

function match(e){
  if (state.status && !e._st.includes(state.status)) return false;
  if (state.deck && !e._decks.includes(state.deck)) return false;
  if (state.pos && !e._pos.includes(state.pos)) return false;
  if (state.q && !e._s.includes(state.q)) return false;
  return true;
}

function hi(w){
  if (!state.q) return esc(w);
  const i = w.toLowerCase().indexOf(state.q);
  if (i < 0) return esc(w);
  return esc(w.slice(0,i)) + "<mark>" + esc(w.slice(i, i+state.q.length)) + "</mark>" + esc(w.slice(i+state.q.length));
}

const deckLabel = id => (DECKS.find(d => d.id === id) || {label:id}).label;

function senseHTML(v){
  const line = (lab, val) => val && val.length ? `<p class="meta"><b>${lab}</b>${esc(Array.isArray(val)? val.join(" · ") : val)}</p>` : "";
  return `<div class="sense">
    <div class="deck">${esc(deckLabel(v.deck))}${v.st === "review" ? " · <i>learned</i>" : ""}</div>
    ${v.form ? `<p class="meta"><b>in text</b>${esc(v.form)}${v.formUz ? " — " + esc(v.formUz) : ""}</p>` : ""}
    <p class="def">${esc(v.def||"")}</p>
    ${v.uz ? `<p class="uzfull">${esc(v.uz)}</p>` : ""}
    ${v.ex ? `<p class="ex">${esc(v.ex)}</p>` : ""}
    ${line("syn", v.syn)}${line("ant", v.ant)}${line("related", v.related)}
    ${line("also", v.senses)}${line("family", v.forms)}
    ${v.mnem ? `<div class="mnem"><span class="kw">keyword — <b>${esc(v.mnem.kw)}</b></span><p class="story">${esc(v.mnem.story)}</p></div>` : ""}
  </div>`;
}

function itemHTML(e, i){
  const v0 = e.v[0];
  return `<div class="item" data-i="${i}">
    <button class="head">
      <span class="w">${hi(e.w)}</span>
      <span class="pos">${esc((v0.pos||"").split("/")[0].trim())}</span>
      <span class="uz">${esc(v0.uz||v0.def||"")}</span>
      <span class="say" role="button" tabindex="-1" aria-label="Pronounce">▶</span>
    </button>
    <div class="body">${e.v.map(senseHTML).join("")}</div>
  </div>`;
}

function render(){
  const hits = WORDS.filter(match);
  const seen = new Set(hits.map(e => e.l));
  $("#rail").querySelectorAll("button").forEach(b => { b.disabled = b.dataset.l && !seen.has(b.dataset.l); });
  $("#count").textContent = hits.length + (hits.length === 1 ? " word" : " words")
    + (hits.length !== WORDS.length ? " of " + WORDS.length : "");
  if (!hits.length){ $("#list").innerHTML = `<div class="empty">Nothing matches that.</div>`; return; }
  let html = "", letter = "";
  hits.forEach((e, i) => {
    if (e.l !== letter){ letter = e.l; html += `<div class="letter" id="L${letter}">${letter}</div>`; }
    html += itemHTML(e, WORDS.indexOf(e));
  });
  $("#list").innerHTML = html;
}

/* speak the word aloud, same as the decks do */
function speak(w){
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(w);
    u.lang = "en-GB"; u.rate = .9;
    speechSynthesis.speak(u);
  } catch(_){}
}

$("#list").addEventListener("click", ev => {
  const item = ev.target.closest(".item");
  if (!item) return;
  if (ev.target.closest(".say")){ speak(WORDS[+item.dataset.i].w); return; }
  item.classList.toggle("open");
});

const q = $("#q");
let t;
q.addEventListener("input", () => {
  $("#sb").classList.toggle("has", !!q.value);
  clearTimeout(t);
  t = setTimeout(() => { state.q = q.value.trim().toLowerCase(); render(); }, 90);
});
$("#clr").onclick = () => { q.value = ""; state.q = ""; $("#sb").classList.remove("has"); q.focus(); render(); };

chips($("#fstatus"), [{v:"learning",label:"Learning now"},{v:"review",label:"Learned · review"}], "status");
chips($("#fdeck"), DECKS.map(d => ({v:d.id, label:d.label, n:d.n})), "deck");
chips($("#fpos"), POS.map(p => ({v:p, label:p})), "pos");

$("#rail").innerHTML = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map(l => `<button data-l="${l}">${l}</button>`).join("");
$("#rail").onclick = ev => {
  const b = ev.target.closest("button"); if (!b || b.disabled) return;
  const el = document.getElementById("L" + b.dataset.l);
  if (el) window.scrollTo({top: el.getBoundingClientRect().top + scrollY - 130, behavior:"smooth"});
};

addEventListener("scroll", () => $("#totop").classList.toggle("on", scrollY > 700));
$("#totop").onclick = () => window.scrollTo({top:0, behavior:"smooth"});
addEventListener("keydown", ev => {
  if (ev.key === "/" && document.activeElement !== q){ ev.preventDefault(); q.focus(); q.select(); }
  if (ev.key === "Escape" && document.activeElement === q){ $("#clr").click(); q.blur(); }
});

render();
</script>
</body>
</html>
"""


def main():
    decks, words = collect()
    lede = ("%d words from %d decks, A–Z. Search by word, meaning, Uzbek or example; "
            "filter by deck, status or part of speech; tap a word to open the full card."
            % (len(words), len(decks)))
    html = (PAGE.replace("__WORDS__", json.dumps(words, ensure_ascii=False))
                .replace("__DECKS__", json.dumps(decks, ensure_ascii=False))
                .replace("__LEDE__", lede))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote %s (%d words, %d decks)" % (OUT, len(words), len(decks)))


if __name__ == "__main__":
    main()
