#!/usr/bin/env python3
"""Regenerate /player.html — a self-contained, lightweight listening-audio player.

Scans every listening test HTML under listening/, and takes each test's audio FROM
THE TEST ITSELF (no separate audio files are created):
  * Cambridge 20 tests reference their four section tracks (Google-Drive URLs) via the
    `const AUDIO = [...]` array — each part becomes one playlist track.
  * Other tests (e.g. Cambridge 21/18) reference a single remote audio URL — reused as-is.

It also pulls each test's **audio script** out of the test HTML when present, so the
player can show a collapsible read-along transcript per track:
  * Cambridge 20 — full per-part transcript (`TEST.transcript = {1:[{who,text}|{sys}],…}`).
  * Cambridge 21 — per-question answer snippets (`questionTranscripts = {n:{speaker,html}}`).
  * Cambridge 18 (and anything without transcript data) — no script.

The result is a single, light-themed /player.html: every track in one playlist,
continuous autoplay, resume-where-you-left-off, lock-screen / car controls
(Media Session API), and lazy-rendered transcript panels.

Run after adding or moving any listening test:
    python3 scripts/build_player.py
It is also called automatically at the end of scripts/build_index.py.
"""
import os, re, json, html

# scripts/ now lives in dev/, so the site root is two levels up, not one.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LISTEN_DIR = os.path.join(ROOT, "listening")
# The player lives in dev/; Vercel rewrites serve it at /player.html.
OUT = os.path.join(ROOT, "dev", "player.html")


def parse_book_test(fname):
    # short form "C20-l3.html" or legacy "Cambridge 20 Test 3 …"
    m = re.search(r"(?:cambridge[\s\-]*|\bc)(\d+)", fname, re.I)
    book = int(m.group(1)) if m else 0
    m = (re.search(r"test[\s\-]*?(\d+)", fname, re.I)
         or re.search(r"[\-\s][rl](\d+)", fname, re.I))
    test = int(m.group(1)) if m else 0
    return book, test


def slice_balanced(s, i):
    """s[i] is an opening '{' or '['. Return the substring inside the balanced
    bracket pair, string-literal aware (handles ", ', ` and backslash escapes)."""
    open_ch = s[i]
    close_ch = "}" if open_ch == "{" else "]"
    depth, j, quote, n = 0, i, None, len(s)
    while j < n:
        c = s[j]
        if quote:
            if c == "\\":
                j += 2
                continue
            if c == quote:
                quote = None
        else:
            if c in ('"', "'", "`"):
                quote = c
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return s[i + 1:j]
        j += 1
    return s[i + 1:]


def extract_tracks(txt):
    """Return list of (src, part_index_or_None) for one test HTML."""
    m = re.search(r"const AUDIO\s*=\s*\[(.*?)\]", txt, re.S)
    if m:
        srcs = [s for s in re.findall(r'"([^"]+)"', m.group(1))
                if s.startswith(("data:", "http", "/", "audio/"))]
        if srcs:
            return [(s, i + 1) for i, s in enumerate(srcs)]
    for pat in (r'<source[^>]+src="([^"]+)"', r'<audio[^>]+src="([^"]+)"'):
        m = re.search(pat, txt)
        if m and m.group(1).startswith(("http", "data:")):
            return [(m.group(1), None)]
    return []


# ---- transcript extraction ------------------------------------------------

def _cam20_part_html(arr_inner):
    """Turn one part's array body into read-along HTML."""
    out = []
    for em in re.finditer(
        r'\{\s*who\s*:\s*"([^"]*)"\s*,\s*text\s*:\s*"([^"]*)"\s*\}'
        r'|\{\s*sys\s*:\s*"([^"]*)"\s*\}', arr_inner):
        if em.group(1) is not None:
            out.append(f'<p class="ln"><b>{html.escape(em.group(1))}</b> '
                       f'{html.escape(em.group(2))}</p>')
        elif em.group(3) is not None:
            out.append(f'<p class="sys">{html.escape(em.group(3))}</p>')
    return "".join(out)


def extract_cam20_transcript(txt):
    """{part:int -> html} from `TEST.transcript = {1:[…],2:[…],…}`."""
    m = re.search(r"\btranscript\s*:\s*\{", txt)
    if not m:
        return {}
    inner = slice_balanced(txt, m.end() - 1)
    parts = {}
    for pm in re.finditer(r"(\d+)\s*:\s*\[", inner):
        arr_inner = slice_balanced(inner, pm.end() - 1)
        h = _cam20_part_html(arr_inner)
        if h:
            parts[int(pm.group(1))] = h
    return parts


def extract_cam21_transcript(txt):
    """Answer-snippet html from `questionTranscripts = {n:{speaker?,html}}`.

    `speaker` is present in some tests, absent in others — both are handled.
    """
    m = re.search(r"questionTranscripts\s*=\s*\{", txt)
    if not m:
        return ""
    inner = slice_balanced(txt, m.end() - 1)
    out, pos = [], 0
    for em in re.finditer(r"(\d+)\s*:\s*\{", inner):
        open_idx = em.end() - 1
        if open_idx < pos:          # a brace nested inside a previous entry body
            continue
        body = slice_balanced(inner, open_idx)
        pos = open_idx + 2 + len(body)
        hm = re.search(r"html\s*:\s*'((?:\\.|[^'\\])*)'", body)
        if not hm:
            continue
        snippet = hm.group(1).replace("\\'", "'").replace("\\\\", "\\")
        sm = re.search(r"speaker\s*:\s*'((?:\\.|[^'\\])*)'", body)
        q = em.group(1)
        if sm and sm.group(1):
            who = f"Q{q} · {html.escape(sm.group(1).replace(chr(92) + chr(39), chr(39)))}"
        else:
            who = f"Q{q}"
        out.append(f'<p class="ln"><b>{who}</b> {snippet}</p>')
    return "".join(out)


def collect():
    tracks = []
    for dirpath, _dirs, files in os.walk(LISTEN_DIR):
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            path = os.path.join(dirpath, f)
            txt = open(path, encoding="utf-8", errors="ignore").read()
            book, test = parse_book_test(f)
            found = extract_tracks(txt)
            multi = len(found) > 1
            cam20 = extract_cam20_transcript(txt) if multi else {}
            cam21 = "" if multi else extract_cam21_transcript(txt)
            for src, part in found:
                offline = not re.match(r"https?://", src)
                if multi and part:
                    label = f"Test {test} · Part {part}"
                    media = f"Cambridge {book} — Test {test}, Part {part}"
                else:
                    label = f"Test {test}"
                    media = f"Cambridge {book} — Test {test}"
                tr = cam20.get(part, "") if multi else cam21
                trtype = ("full" if multi else "snippets") if tr else ""
                tracks.append({
                    "group": f"Cambridge {book}", "book": book, "test": test,
                    "part": part or 0, "label": label, "media": media,
                    "src": src, "offline": offline, "tr": tr, "trtype": trtype,
                    "rel": os.path.relpath(path, ROOT),
                })
    for t in tracks:
        # page sits in dev/, so a repo-relative audio path needs one level up
        if not t["src"].startswith(("http", "data:", "/")):
            t["src"] = "../" + t["src"]
    tracks.sort(key=lambda t: (t["book"], t["test"], t["part"]))
    for i, t in enumerate(tracks):
        t["id"] = f"t{i}"
    return tracks


PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<meta name="theme-color" content="#1e6de6"/>
<title>Listening Player</title>
<style>
  :root{
    --bg:#f4f7fb;--card:#fff;--line:#e6eaf1;--ink:#111827;--ink2:#6b7280;
    --blue:#1e6de6;--blue2:#3b82f6;--blued:#0f2f66;--bluebg:#eff6ff;
    --green:#16a34a;--greenbg:#effdf4;--amber:#b45309;--amberbg:#fff7ed;
    --shadow:0 1px 2px rgba(16,24,40,.04),0 1px 3px rgba(16,24,40,.06);
  }
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased;padding-bottom:196px}
  .wrap{max-width:660px;margin:0 auto;padding:16px 16px 24px}
  /* hero */
  .hero{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;border-radius:18px;
    padding:22px 20px;box-shadow:0 10px 30px rgba(30,109,230,.25);margin-bottom:18px}
  .hero h1{font-size:22px;margin:0 0 4px;letter-spacing:-.02em;font-weight:800}
  .hero p{margin:0;font-size:13px;color:#dbeafe;line-height:1.5}
  .hero .stats{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
  .chip{font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;
    background:rgba(255,255,255,.16);color:#fff;backdrop-filter:blur(4px)}
  /* group heading */
  .grp{margin:20px 4px 8px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--ink2);font-weight:800}
  /* track card */
  .card{border:1px solid var(--line);background:var(--card);border-radius:14px;
    margin-bottom:9px;box-shadow:var(--shadow);overflow:hidden;transition:.14s}
  .card.active{border-color:var(--blue);box-shadow:0 0 0 3px rgba(30,109,230,.14),var(--shadow)}
  .trk{display:flex;align-items:center;gap:12px;padding:13px 14px;cursor:pointer}
  .card:hover{border-color:#c9d6ee}
  .card.active .trk{background:var(--bluebg)}
  .idx{width:34px;height:34px;flex:none;border-radius:10px;background:#eef2f8;color:var(--ink2);
    display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800}
  .card.active .idx{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff}
  .meta{min-width:0;flex:1}
  .meta .t{font-size:15px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .meta .d{font-size:12px;color:var(--ink2);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .badge{font-size:10px;font-weight:800;padding:3px 8px;border-radius:999px;flex:none;letter-spacing:.02em}
  .badge.off{background:var(--greenbg);color:var(--green)}
  .badge.on{background:var(--amberbg);color:var(--amber)}
  .badge.bad{background:#fef2f2;color:#b91c1c}
  .card.dead .meta .t,.card.dead .idx{opacity:.55}
  .bar .st.err{color:#b91c1c;font-weight:650}
  /* equalizer (now playing) */
  .eq{display:none;align-items:flex-end;gap:2px;height:16px;width:16px;flex:none}
  .card.playing .eq{display:inline-flex}
  .eq i{width:3px;background:var(--blue);border-radius:2px;animation:eq .9s ease-in-out infinite}
  .eq i:nth-child(1){animation-delay:-.2s}.eq i:nth-child(2){animation-delay:-.5s}.eq i:nth-child(3){animation-delay:-.1s}
  @keyframes eq{0%,100%{height:4px}50%{height:16px}}
  /* script toggle + panel */
  .scriptbtn{flex:none;display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:800;
    color:var(--blue);background:var(--bluebg);border:1px solid #d3e2fb;border-radius:999px;
    padding:5px 10px;cursor:pointer;transition:.12s}
  .scriptbtn:hover{background:#e0edff}
  .scriptbtn .cv{transition:transform .18s;font-size:9px}
  .scriptbtn[aria-expanded="true"] .cv{transform:rotate(180deg)}
  .panel{display:none;border-top:1px solid var(--line);background:#f8fafc;
    padding:14px 16px;max-height:340px;overflow:auto;font-size:14px;line-height:1.7}
  .panel.open{display:block}
  .panel .cap{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
    color:var(--ink2);margin:0 0 8px}
  .panel .ln{margin:0 0 9px}
  .panel .ln b{color:var(--blued);font-weight:750;margin-right:4px}
  .panel .sys{margin:0 0 9px;font-style:italic;color:var(--ink2);font-size:13px}
  .panel mark{background:#fff3bf;color:#7a5b00;padding:0 3px;border-radius:3px;font-weight:700}
  .empty{color:var(--ink2);padding:44px 0;text-align:center}
  /* bottom bar */
  .bar{position:fixed;left:0;right:0;bottom:0;background:rgba(255,255,255,.9);
    backdrop-filter:saturate(1.4) blur(14px);border-top:1px solid var(--line);
    padding:11px 16px calc(11px + env(safe-area-inset-bottom));z-index:50;
    box-shadow:0 -6px 24px rgba(16,24,40,.06)}
  .bar .inner{max-width:660px;margin:0 auto}
  .bar .title{font-size:14px;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .bar .st{font-size:12px;color:var(--ink2);margin-bottom:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .seekrow{display:flex;align-items:center;gap:10px}
  .time{font-size:11px;color:var(--ink2);font-variant-numeric:tabular-nums;min-width:38px;text-align:center}
  input[type=range]{-webkit-appearance:none;appearance:none;height:6px;border-radius:5px;
    background:#e2e8f2;flex:1;cursor:pointer}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;
    background:var(--blue);box-shadow:0 0 0 3px rgba(30,109,230,.18);border:2px solid #fff}
  input[type=range]::-moz-range-thumb{width:15px;height:15px;border:2px solid #fff;border-radius:50%;background:var(--blue)}
  .ctrls{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:9px}
  .cbtn{background:#eef2f8;color:var(--ink);border:none;border-radius:11px;height:44px;min-width:44px;
    padding:0 14px;font-size:15px;font-weight:600;cursor:pointer;display:flex;align-items:center;
    justify-content:center;transition:.12s}
  .cbtn:hover{background:#e2e8f2}
  .cbtn.play{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;min-width:62px;font-size:19px;
    box-shadow:0 4px 12px rgba(30,109,230,.3)}
  .cbtn.small{font-size:12px;font-weight:800;color:var(--ink2);background:transparent}
  .cbtn.small:hover{background:#eef2f8}
  /* speed popover */
  .rate-wrap{position:relative;display:inline-flex}
  .rate-menu{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);background:#fff;
    border:1px solid var(--line);border-radius:12px;box-shadow:0 12px 32px rgba(2,6,23,.2);padding:5px;min-width:136px;z-index:60}
  .rate-menu[hidden]{display:none}
  .rate-menu .rl{font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);padding:5px 10px 3px}
  .rate-opt{display:flex;justify-content:space-between;align-items:center;width:100%;gap:10px;background:none;border:none;
    color:var(--ink);font-size:13px;font-weight:650;padding:8px 10px;border-radius:8px;cursor:pointer;text-align:left}
  .rate-opt:hover{background:#f1f5f9}
  .rate-opt.active{background:var(--bluebg);color:var(--blue)}
  .rate-opt.active::after{content:'✓';font-weight:800}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>🎧 Listening Player</h1>
    <p>Every listening track in one place — tap to play, plays continuously. Tap <b>Script</b> to read along. <b>offline</b> tracks work with no signal; <b>online</b> need internet.</p>
    <div class="stats" id="stats"></div>
  </div>
  <div id="list"></div>
  <div id="empty" class="empty" style="display:none">No listening tracks found.</div>
</div>

<div class="bar">
  <div class="inner">
    <div class="title" id="npTitle">Select a track</div>
    <div class="st" id="npSub">—</div>
    <div class="seekrow">
      <span class="time" id="cur">0:00</span>
      <input type="range" id="seek" min="0" max="1000" value="0" aria-label="Seek"/>
      <span class="time" id="dur">0:00</span>
    </div>
    <div class="ctrls">
      <div class="rate-wrap">
        <button class="cbtn small" id="rate" title="Playback speed" aria-haspopup="true" aria-expanded="false">1×</button>
        <div class="rate-menu" id="rateMenu" role="menu" hidden>
          <div class="rl">Speed</div>
          <button class="rate-opt" data-rate="0.75" role="menuitemradio">0.75×</button>
          <button class="rate-opt active" data-rate="1" role="menuitemradio">Normal</button>
          <button class="rate-opt" data-rate="1.25" role="menuitemradio">1.25×</button>
          <button class="rate-opt" data-rate="1.5" role="menuitemradio">1.5×</button>
          <button class="rate-opt" data-rate="2" role="menuitemradio">2×</button>
        </div>
      </div>
      <button class="cbtn" id="prev" title="Previous" aria-label="Previous">⏮</button>
      <button class="cbtn" id="back" title="Back 15s" aria-label="Back 15 seconds">−15</button>
      <button class="cbtn play" id="play" aria-label="Play">▶</button>
      <button class="cbtn" id="fwd" title="Forward 15s" aria-label="Forward 15 seconds">+15</button>
      <button class="cbtn" id="next" title="Next" aria-label="Next">⏭</button>
    </div>
  </div>
</div>

<div id="tracks" style="display:none">__AUDIO_ELEMENTS__</div>
<script>
const PLAYLIST = __PLAYLIST__;
"""

PAGE_TAIL = r"""
const listEl=document.getElementById('list');
const npTitle=document.getElementById('npTitle'), npSub=document.getElementById('npSub');
const seek=document.getElementById('seek'), curEl=document.getElementById('cur'), durEl=document.getElementById('dur');
const playBtn=document.getElementById('play'), rateBtn=document.getElementById('rate');
let cur=-1, audio=null, curRate=1, seeking=false, autoChain=0;
const dead=new Set();

function fmt(s){ if(!isFinite(s)||s<0)return '0:00'; s=Math.floor(s); return Math.floor(s/60)+':'+String(s%60).padStart(2,'0'); }
// resume positions are keyed by the track's name, not its index — adding a new
// test shifts every index, which used to restore the wrong position.
function posKey(i){ return 'lp_pos::'+PLAYLIST[i].key; }
function savedPos(i){ const v=parseFloat(localStorage.getItem(posKey(i))||'0'); return isFinite(v)&&v>0?v:0; }

// header stats
(function(){
  const withTr=PLAYLIST.filter(t=>t.tr).length;
  const st=document.getElementById('stats');
  st.innerHTML=`<span class="chip">${PLAYLIST.length} tracks</span>`+
    `<span class="chip">${withTr} with script</span>`;
})();

// build list grouped by book
if(!PLAYLIST.length){ document.getElementById('empty').style.display='block'; }
let lastGroup=null;
PLAYLIST.forEach((tk,i)=>{
  if(tk.group!==lastGroup){ lastGroup=tk.group; const g=document.createElement('div'); g.className='grp'; g.textContent=tk.group; listEl.appendChild(g); }
  const card=document.createElement('div'); card.className='card'; card.id='card-'+i;
  const scriptBtn = tk.tr ? `<button class="scriptbtn" aria-expanded="false" aria-label="Show script">📄 Script <span class="cv">▼</span></button>` : '';
  card.innerHTML=
    `<div class="trk">`+
      `<div class="idx">${i+1}</div>`+
      `<div class="eq" aria-hidden="true"><i></i><i></i><i></i></div>`+
      `<div class="meta"><div class="t">${tk.label}</div><div class="d">${tk.media}</div></div>`+
      scriptBtn+
      `<span class="badge ${tk.offline?'off':'on'}" id="badge-${i}">${tk.offline?'offline':'online'}</span>`+
    `</div>`+
    `<div class="panel" id="panel-${i}"></div>`;
  card.querySelector('.trk').addEventListener('click',()=>{
    // tapping the track that is already playing pauses it, instead of doing nothing
    if(i===cur && audio){ autoChain=0; if(audio.paused) audio.play().catch(()=>{}); else audio.pause(); return; }
    selectTrack(i,true);
  });
  const sb=card.querySelector('.scriptbtn');
  if(sb) sb.addEventListener('click',(e)=>{ e.stopPropagation(); togglePanel(i,sb); });
  listEl.appendChild(card);
});

function togglePanel(i, btn){
  const panel=document.getElementById('panel-'+i);
  const open=panel.classList.toggle('open');
  if(open && !panel.dataset.filled){
    const tk=PLAYLIST[i];
    const cap = tk.trtype==='snippets' ? 'Answer script — key lines' : 'Transcript';
    panel.innerHTML=`<p class="cap">${cap}</p>`+tk.tr;
    panel.dataset.filled='1';
  }
  btn.setAttribute('aria-expanded', open?'true':'false');
}

function el(i){ return document.getElementById(PLAYLIST[i].id); }

function markDead(i){
  dead.add(i);
  const c=document.getElementById('card-'+i); if(c) c.classList.add('dead');
  const b=document.getElementById('badge-'+i);
  if(b){ b.className='badge bad'; b.textContent='unavailable'; }
}

function showErr(msg){ npSub.textContent=msg; npSub.classList.add('err'); }
function clearErr(tk){ npSub.textContent=tk.media; npSub.classList.remove('err'); }

function selectTrack(i, autoplay){
  if(i<0||i>=PLAYLIST.length){ // walked off the end of the playlist — stop cleanly
    if(audio) audio.pause();
    return;
  }
  if(audio && cur!==i) audio.pause();
  document.querySelectorAll('.card').forEach(r=>r.classList.remove('active','playing'));
  const card=document.getElementById('card-'+i); if(card) card.classList.add('active');
  cur=i; const tk=PLAYLIST[i];
  audio=el(i);
  // the element is preload="none" so nothing downloads until a track is chosen;
  // once chosen we want its duration even while paused
  if(audio.preload!=='metadata'){ audio.preload='metadata'; audio.load(); }
  audio.playbackRate=curRate;
  npTitle.textContent=tk.label;
  clearErr(tk);
  if(dead.has(i)) showErr('Audio unavailable — the source link is dead.');
  wire(audio);
  updateMediaSession(tk);
  localStorage.setItem('lp_last', i);
  // show the stored position right away, before any metadata arrives
  const p=savedPos(i);
  curEl.textContent=fmt(audio.currentTime||p);
  durEl.textContent=fmt(audio.duration||0);
  seek.value=(audio.duration?String(Math.round((audio.currentTime||p)/audio.duration*1000)):'0');
  if(autoplay) audio.play().catch(()=>{ playBtn.textContent='▶'; });
}

let wired=new WeakSet();
function wire(a){
  if(wired.has(a)) return;
  wired.add(a);
  a.addEventListener('timeupdate',()=>{
    if(a!==audio) return;
    if(!seeking && a.duration) seek.value=String(Math.round(a.currentTime/a.duration*1000));
    if(!seeking) curEl.textContent=fmt(a.currentTime);
    durEl.textContent=fmt(a.duration);
    if(cur>=0) localStorage.setItem(posKey(cur), a.currentTime);
  });
  a.addEventListener('loadedmetadata',()=>{
    if(a!==audio) return;
    a.playbackRate=curRate;          // some browsers reset the rate on load
    durEl.textContent=fmt(a.duration);
    const p=savedPos(cur);
    if(p>0 && p<a.duration-2) a.currentTime=p;
    syncPosition(a);
  });
  a.addEventListener('play',()=>{ if(a===audio){ playBtn.textContent='❚❚'; const c=document.getElementById('card-'+cur); if(c)c.classList.add('playing'); syncPosition(a); } });
  a.addEventListener('pause',()=>{ if(a===audio){ playBtn.textContent='▶'; const c=document.getElementById('card-'+cur); if(c)c.classList.remove('playing'); } });
  a.addEventListener('ratechange',()=>{ if(a===audio) syncPosition(a); });
  a.addEventListener('ended',()=>{
    if(a!==audio) return;
    localStorage.removeItem(posKey(cur));   // a finished track restarts from 0
    autoChain=0;
    selectTrack(cur+1, true);
  });
  a.addEventListener('error',()=>{
    if(a!==audio) return;
    const i=cur;
    markDead(i);
    playBtn.textContent='▶';
    showErr('Audio unavailable — the source link is dead.');
    // during continuous play, hop over dead tracks instead of stalling —
    // but never run away through the whole playlist
    if(autoChain>0 && autoChain<6 && i+1<PLAYLIST.length){ autoChain++; selectTrack(i+1,true); }
  });
}

playBtn.addEventListener('click',()=>{ autoChain=1; if(cur<0){ selectTrack(0,true); return; } if(audio.paused) audio.play().catch(()=>{ playBtn.textContent='▶'; }); else audio.pause(); });
document.getElementById('next').addEventListener('click',()=>{ autoChain=1; selectTrack(cur<0?0:cur+1,true); });
document.getElementById('prev').addEventListener('click',()=>{ autoChain=1; if(cur<0){selectTrack(0,true);return;} if(audio.currentTime>3){audio.currentTime=0;} else selectTrack(cur-1,true); });
document.getElementById('fwd').addEventListener('click',()=>{ if(audio&&audio.duration) audio.currentTime=Math.min(audio.duration,audio.currentTime+15); });
document.getElementById('back').addEventListener('click',()=>{ if(audio) audio.currentTime=Math.max(0,audio.currentTime-15); });
// while a finger is on the slider, timeupdate must not fight the drag
seek.addEventListener('pointerdown',()=>{ seeking=true; });
seek.addEventListener('input',()=>{ if(audio&&audio.duration) curEl.textContent=fmt((+seek.value)/1000*audio.duration); });
function commitSeek(){ if(audio&&audio.duration) audio.currentTime=(+seek.value)/1000*audio.duration; seeking=false; }
seek.addEventListener('change',commitSeek);
seek.addEventListener('pointerup',commitSeek);
seek.addEventListener('pointercancel',()=>{ seeking=false; });

const rateMenu=document.getElementById('rateMenu');
const rateOpts=Array.prototype.slice.call(rateMenu.querySelectorAll('.rate-opt'));
function openRate(o){ rateMenu.hidden=!o; rateBtn.setAttribute('aria-expanded', o?'true':'false'); }
function applyRate(r){
  curRate=r; if(audio) audio.playbackRate=r;
  rateBtn.textContent=r+'×';
  rateOpts.forEach(x=>x.classList.toggle('active', parseFloat(x.dataset.rate)===r));
  localStorage.setItem('lp_rate', String(r));
}
rateBtn.addEventListener('click',(e)=>{ e.stopPropagation(); openRate(rateMenu.hidden); });
rateOpts.forEach(o=>o.addEventListener('click',(e)=>{ e.stopPropagation(); applyRate(parseFloat(o.dataset.rate)); openRate(false); }));
document.addEventListener('click',()=>openRate(false));

// keyboard: space plays/pauses, arrows nudge 15s
document.addEventListener('keydown',(e)=>{
  const t=e.target;
  // e.target can be the document itself when nothing is focused
  if(t&&t.closest&&t.closest('input,textarea,button,[contenteditable]')) return;
  if(e.code==='Space'){ e.preventDefault(); playBtn.click(); }
  else if(e.code==='ArrowLeft'){ e.preventDefault(); document.getElementById('back').click(); }
  else if(e.code==='ArrowRight'){ e.preventDefault(); document.getElementById('fwd').click(); }
});

function syncPosition(a){
  // without this the lock-screen / car scrubber stays frozen at 0:00
  if(!('mediaSession' in navigator) || !navigator.mediaSession.setPositionState) return;
  if(!isFinite(a.duration)||a.duration<=0) return;
  try{ navigator.mediaSession.setPositionState({duration:a.duration, playbackRate:a.playbackRate||1, position:Math.min(a.currentTime,a.duration)}); }catch(_){}
}

function updateMediaSession(tk){
  if(!('mediaSession' in navigator)) return;
  navigator.mediaSession.metadata=new MediaMetadata({title:tk.label, artist:tk.media, album:'Listening Player'});
  const set=(k,fn)=>{ try{ navigator.mediaSession.setActionHandler(k,fn); }catch(_){} };
  set('play',()=>audio&&audio.play());
  set('pause',()=>audio&&audio.pause());
  set('previoustrack',()=>selectTrack(cur-1,true));
  set('nexttrack',()=>selectTrack(cur+1,true));
  set('seekbackward',(d)=>{ if(audio) audio.currentTime=Math.max(0,audio.currentTime-((d&&d.seekOffset)||15)); });
  set('seekforward',(d)=>{ if(audio&&audio.duration) audio.currentTime=Math.min(audio.duration,audio.currentTime+((d&&d.seekOffset)||15)); });
  set('seekto',(d)=>{ if(audio&&d&&typeof d.seekTime==='number') audio.currentTime=d.seekTime; });
}

// restore speed, then the last selection (paused)
const savedRate=parseFloat(localStorage.getItem('lp_rate')||'1');
if([0.75,1,1.25,1.5,2].indexOf(savedRate)>=0) applyRate(savedRate);
const last=parseInt(localStorage.getItem('lp_last')||'-1',10);
if(last>=0 && last<PLAYLIST.length) selectTrack(last,false);
</script>
</body>
</html>
"""


def main():
    tracks = collect()
    audio_els = "\n".join(
        f'<audio id="{t["id"]}" preload="none" src="{html.escape(t["src"], quote=True)}"></audio>'
        for t in tracks
    )
    meta = [{"id": t["id"], "key": f'{t["group"]}|{t["label"]}',
             "group": t["group"], "label": t["label"],
             "media": t["media"], "offline": t["offline"],
             "tr": t["tr"], "trtype": t["trtype"]} for t in tracks]
    playlist_json = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE_HEAD.replace("__AUDIO_ELEMENTS__", audio_els)
                     .replace("__PLAYLIST__", playlist_json)
            + PAGE_TAIL)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    off = sum(1 for t in tracks if t["offline"])
    tr = sum(1 for t in tracks if t["tr"])
    print(f"Wrote {OUT}  ({len(tracks)} tracks: {off} offline, {len(tracks)-off} online, "
          f"{tr} with script, {len(page)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
