#!/usr/bin/env python3
"""Regenerate /generated/translate/translate.html — a translation-practice page.

Reads the curated sentence store at vocab/translations.json (difficult sentences
pulled from finished reading passages and listening scripts, each with an Uzbek
translation) and renders a self-contained page:

  * sentences shown in groups of 20 (1–20, 21–40, …) — pick a group to study it,
  * a Reading / Listening / All filter,
  * each sentence has a "Show translation" button that reveals the Uzbek,
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
        })
    return out


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
  <div id="list"></div>
  <div id="empty" class="empty" style="display:none">No sentences yet — add some to vocab/translations.json.</div>
</div>
<script>
const DATA = __DATA__;
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
    card.innerHTML =
      `<div class="srcrow"><span class="badge ${t}">${t}</span><span class="src">${esc(d.src||"")}</span></div>`+
      `<div class="en">${esc(d.en)}</div>`+
      (d.uz ? `<button class="showbtn">🇺🇿 Show translation</button>
               <div class="uz"><span class="flag">Uzbek</span>${esc(d.uz)}</div>` : ``);
    const btn=card.querySelector('.showbtn');
    if(btn){ btn.addEventListener('click',()=>{
      const uz=card.querySelector('.uz'); const open=uz.classList.toggle('open');
      btn.textContent = open ? "🇺🇿 Hide translation" : "🇺🇿 Show translation";
    }); }
    listEl.appendChild(card);
  });
}

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
    page = (PAGE_HEAD.replace("__DATA__", json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"))
            + PAGE_TAIL)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    nr = sum(1 for r in rows if r["type"] == "reading")
    nl = sum(1 for r in rows if r["type"] == "listening")
    print(f"Wrote {OUT}  ({len(rows)} sentences: {nr} reading, {nl} listening)")


if __name__ == "__main__":
    main()
