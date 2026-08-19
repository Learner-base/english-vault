#!/usr/bin/env python3
"""Regenerate /player.html — a self-contained listening-audio player for the road.

Scans every listening test HTML under listening/, and takes each test's audio FROM
THE TEST ITSELF (no separate audio files are created):
  * Cambridge 20 tests embed their four section tracks as base64 data: URIs — those
    are extracted and re-used, so the player plays fully offline.
  * Other tests (e.g. Cambridge 21/18) reference a remote audio URL — that URL is
    reused as-is (those tracks need an internet connection).

The result is a single /player.html with every track in one playlist, continuous
autoplay, and lock-screen / car controls (Media Session API).

Run after adding or moving any listening test:
    python3 scripts/build_player.py
It is also called automatically at the end of scripts/build_index.py.
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTEN_DIR = os.path.join(ROOT, "listening")
OUT = os.path.join(ROOT, "player.html")


def parse_book_test(fname):
    m = re.search(r"cambridge[\s\-]*?(\d+)", fname, re.I)
    book = int(m.group(1)) if m else 0
    m = re.search(r"test[\s\-]*?(\d+)", fname, re.I)
    test = int(m.group(1)) if m else 0
    return book, test


def extract_tracks(path):
    """Return list of (src, part_index_or_None) for one test HTML."""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    # 1) embedded AUDIO array (Cambridge 20 engine)
    m = re.search(r"const AUDIO\s*=\s*\[(.*?)\]", txt, re.S)
    if m:
        srcs = [s for s in re.findall(r'"([^"]+)"', m.group(1))
                if s.startswith(("data:", "http", "/", "audio/"))]
        if srcs:
            return [(s, i + 1) for i, s in enumerate(srcs)]
    # 2) single remote source (<source src> or <audio ... src>)
    for pat in (r'<source[^>]+src="([^"]+)"', r'<audio[^>]+src="([^"]+)"'):
        m = re.search(pat, txt)
        if m and (m.group(1).startswith("http") or m.group(1).startswith("data:")):
            return [(m.group(1), None)]
    return []


def collect():
    tracks = []
    for dirpath, _dirs, files in os.walk(LISTEN_DIR):
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            path = os.path.join(dirpath, f)
            book, test = parse_book_test(f)
            found = extract_tracks(path)
            multi = len(found) > 1
            for src, part in found:
                # local files (/audio/… or embedded data:) play offline; external URLs need internet
                offline = not re.match(r"https?://", src)
                if multi and part:
                    label = f"Test {test} · Part {part}"
                    media = f"Cambridge {book} — Test {test}, Part {part}"
                else:
                    label = f"Test {test}"
                    media = f"Cambridge {book} — Test {test}"
                tracks.append({
                    "group": f"Cambridge {book}", "book": book, "test": test,
                    "part": part or 0, "label": label, "media": media,
                    "src": src, "offline": offline,
                    "rel": os.path.relpath(path, ROOT),
                })
    tracks.sort(key=lambda t: (t["book"], t["test"], t["part"]))
    for i, t in enumerate(tracks):
        t["id"] = f"t{i}"
    return tracks


PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<meta name="theme-color" content="#0b1220"/>
<title>Listening Player</title>
<style>
  :root{--bg:#0b1220;--card:#131c2e;--line:#243149;--ink:#eaf0fb;--ink2:#95a3bd;--accent:#3b82f6;--accent2:#22c55e;--warn:#f59e0b}
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;padding-bottom:180px}
  .wrap{max-width:640px;margin:0 auto;padding:18px 16px 24px}
  h1{font-size:20px;margin:4px 0 2px;letter-spacing:-.01em}
  .sub{color:var(--ink2);font-size:13px;margin:0 0 16px}
  .grp{margin:18px 0 6px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2);font-weight:700}
  .trk{display:flex;align-items:center;gap:12px;padding:13px 12px;border:1px solid var(--line);background:var(--card);border-radius:12px;margin-bottom:8px;cursor:pointer;transition:.12s}
  .trk:hover{border-color:var(--accent)}
  .trk.active{border-color:var(--accent);box-shadow:0 0 0 2px rgba(59,130,246,.35);background:#16233c}
  .trk .idx{width:30px;height:30px;flex:none;border-radius:8px;background:#1c2942;color:var(--ink2);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
  .trk.active .idx{background:var(--accent);color:#fff}
  .trk .meta{min-width:0;flex:1}
  .trk .t{font-size:15px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .trk .d{font-size:12px;color:var(--ink2);margin-top:1px}
  .badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;flex:none}
  .badge.off{background:rgba(34,197,94,.16);color:#4ade80}
  .badge.on{background:rgba(245,158,11,.16);color:#fbbf24}
  .now{width:22px;flex:none;text-align:center;color:var(--accent)}
  /* bottom bar */
  .bar{position:fixed;left:0;right:0;bottom:0;background:rgba(11,18,32,.96);backdrop-filter:blur(12px);border-top:1px solid var(--line);padding:10px 16px calc(10px + env(safe-area-inset-bottom));z-index:50}
  .bar .inner{max-width:640px;margin:0 auto}
  .bar .title{font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .bar .st{font-size:12px;color:var(--ink2);margin-bottom:6px}
  .seekrow{display:flex;align-items:center;gap:10px}
  .time{font-size:11px;color:var(--ink2);font-variant-numeric:tabular-nums;min-width:38px;text-align:center}
  input[type=range]{-webkit-appearance:none;appearance:none;height:6px;border-radius:4px;background:#26344e;flex:1;cursor:pointer}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:#fff}
  input[type=range]::-moz-range-thumb{width:16px;height:16px;border:none;border-radius:50%;background:#fff}
  .ctrls{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:8px}
  .cbtn{background:#1c2942;color:var(--ink);border:none;border-radius:10px;height:44px;min-width:44px;padding:0 14px;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center}
  .cbtn:hover{background:#243350}
  .cbtn.play{background:var(--accent);min-width:60px;font-size:20px}
  .cbtn.small{font-size:12px;font-weight:700;color:var(--ink2)}
  .empty{color:var(--ink2);padding:40px 0;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎧 Listening Player</h1>
  <p class="sub">All listening tracks in one place — tap to play, plays continuously. <span class="badge off">offline</span> tracks work with no signal; <span class="badge on">online</span> need internet.</p>
  <div id="list"></div>
  <div id="empty" class="empty" style="display:none">No listening tracks found.</div>
</div>

<div class="bar">
  <div class="inner">
    <div class="title" id="npTitle">Select a track</div>
    <div class="st" id="npSub">—</div>
    <div class="seekrow">
      <span class="time" id="cur">0:00</span>
      <input type="range" id="seek" min="0" max="1000" value="0"/>
      <span class="time" id="dur">0:00</span>
    </div>
    <div class="ctrls">
      <button class="cbtn small" id="rate">1×</button>
      <button class="cbtn" id="prev">⏮</button>
      <button class="cbtn" id="back">−15</button>
      <button class="cbtn play" id="play">▶</button>
      <button class="cbtn" id="fwd">+15</button>
      <button class="cbtn" id="next">⏭</button>
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
let cur=-1, audio=null, rates=[1,1.25,1.5,0.75], ri=0;

function fmt(s){ if(!isFinite(s)||s<0)return '0:00'; s=Math.floor(s); return Math.floor(s/60)+':'+String(s%60).padStart(2,'0'); }

// build list grouped by book
if(!PLAYLIST.length){ document.getElementById('empty').style.display='block'; }
let lastGroup=null;
PLAYLIST.forEach((tk,i)=>{
  if(tk.group!==lastGroup){ lastGroup=tk.group; const g=document.createElement('div'); g.className='grp'; g.textContent=tk.group; listEl.appendChild(g); }
  const row=document.createElement('div'); row.className='trk'; row.id='row-'+i;
  row.innerHTML=`<div class="idx">${i+1}</div>`+
    `<div class="meta"><div class="t">${tk.label}</div><div class="d">${tk.media}</div></div>`+
    `<span class="badge ${tk.offline?'off':'on'}">${tk.offline?'offline':'online'}</span>`+
    `<span class="now" id="now-${i}"></span>`;
  row.addEventListener('click',()=>selectTrack(i,true));
  listEl.appendChild(row);
});

function el(i){ return document.getElementById(PLAYLIST[i].id); }

function selectTrack(i, autoplay){
  if(i<0||i>=PLAYLIST.length) return;
  if(audio && cur!==i){ audio.pause(); }
  document.querySelectorAll('.trk').forEach(r=>r.classList.remove('active'));
  document.querySelectorAll('.now').forEach(n=>n.textContent='');
  const row=document.getElementById('row-'+i); if(row) row.classList.add('active');
  cur=i; const tk=PLAYLIST[i];
  audio=el(i); audio.playbackRate=rates[ri];
  npTitle.textContent=tk.label; npSub.textContent=tk.media;
  wire(audio);
  updateMediaSession(tk);
  localStorage.setItem('lp_last', i);
  if(autoplay) audio.play().catch(()=>{});
  else { curEl.textContent=fmt(audio.currentTime||0); durEl.textContent=fmt(audio.duration||0); }
}

let wired=new WeakSet();
function wire(a){
  if(!wired.has(a)){
    wired.add(a);
    a.addEventListener('timeupdate',()=>{ if(a!==audio)return; if(a.duration) seek.value=String(Math.round(a.currentTime/a.duration*1000)); curEl.textContent=fmt(a.currentTime); durEl.textContent=fmt(a.duration); if(cur>=0) localStorage.setItem('lp_pos_'+cur, a.currentTime); });
    a.addEventListener('loadedmetadata',()=>{ if(a===audio){ durEl.textContent=fmt(a.duration); const p=parseFloat(localStorage.getItem('lp_pos_'+cur)||'0'); if(p>0&&p<a.duration-2) a.currentTime=p; } });
    a.addEventListener('play',()=>{ if(a===audio){ playBtn.textContent='❚❚'; const n=document.getElementById('now-'+cur); if(n)n.textContent='▶'; } });
    a.addEventListener('pause',()=>{ if(a===audio){ playBtn.textContent='▶'; const n=document.getElementById('now-'+cur); if(n)n.textContent=''; } });
    a.addEventListener('ended',()=>{ if(a===audio) selectTrack(cur+1, true); });
  }
}

playBtn.addEventListener('click',()=>{ if(cur<0){ selectTrack(0,true); return; } if(audio.paused) audio.play().catch(()=>{}); else audio.pause(); });
document.getElementById('next').addEventListener('click',()=>selectTrack(cur<0?0:cur+1,true));
document.getElementById('prev').addEventListener('click',()=>{ if(cur<0){selectTrack(0,true);return;} if(audio.currentTime>3){audio.currentTime=0;} else selectTrack(cur-1,true); });
document.getElementById('fwd').addEventListener('click',()=>{ if(audio) audio.currentTime=Math.min(audio.duration||0,audio.currentTime+15); });
document.getElementById('back').addEventListener('click',()=>{ if(audio) audio.currentTime=Math.max(0,audio.currentTime-15); });
seek.addEventListener('input',()=>{ if(audio&&audio.duration) audio.currentTime=(+seek.value)/1000*audio.duration; });
rateBtn.addEventListener('click',()=>{ ri=(ri+1)%rates.length; if(audio)audio.playbackRate=rates[ri]; rateBtn.textContent=rates[ri]+'×'; });

function updateMediaSession(tk){
  if(!('mediaSession' in navigator)) return;
  navigator.mediaSession.metadata=new MediaMetadata({title:tk.label, artist:tk.media, album:'Listening Player'});
  navigator.mediaSession.setActionHandler('play',()=>audio&&audio.play());
  navigator.mediaSession.setActionHandler('pause',()=>audio&&audio.pause());
  navigator.mediaSession.setActionHandler('previoustrack',()=>selectTrack(cur-1,true));
  navigator.mediaSession.setActionHandler('nexttrack',()=>selectTrack(cur+1,true));
  navigator.mediaSession.setActionHandler('seekbackward',()=>{ if(audio)audio.currentTime=Math.max(0,audio.currentTime-15); });
  navigator.mediaSession.setActionHandler('seekforward',()=>{ if(audio)audio.currentTime=Math.min(audio.duration||0,audio.currentTime+15); });
}

// restore last selection (paused)
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
    meta = [{"id": t["id"], "group": t["group"], "label": t["label"],
             "media": t["media"], "offline": t["offline"]} for t in tracks]
    page = (PAGE_HEAD.replace("__AUDIO_ELEMENTS__", audio_els)
                     .replace("__PLAYLIST__", json.dumps(meta, ensure_ascii=False))
            + PAGE_TAIL)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    off = sum(1 for t in tracks if t["offline"])
    print(f"Wrote {OUT}  ({len(tracks)} tracks: {off} offline, {len(tracks)-off} online, {len(page)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
