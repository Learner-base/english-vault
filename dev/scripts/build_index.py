#!/usr/bin/env python3
"""Regenerate the root index.html file browser from the current project tree.

Walks the whole project (skipping .git, .claude, __pycache__, .pyc, .DS_Store),
builds a nested JSON tree of every folder/file, and writes it into index.html —
a self-contained, expandable file browser shown as the site's main page.

Run this after creating or deleting ANY file or folder so the main page stays in
sync:

    python3 scripts/build_index.py
"""
import os, sys, json, subprocess

# importing the sibling builders must not litter dev/scripts/ with __pycache__
sys.dont_write_bytecode = True

# scripts/ now lives in dev/, so the site root is two levels up, not one.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIR = {".git", ".claude", "__pycache__", "scripts"}
# CLAUDE.md is an AI instruction file and index.html is this page itself — the user
# doesn't need either listed in the browser.
SKIP_FILE = {".DS_Store", "CLAUDE.md", "index.html", "progress.html", "vercel.json",
             "player.html", "future-prompts.md"}
# The page shows ONLY these top-level folders (and what is inside them). Everything
# else at the repo root — loose .md notes, templates/, config — stays out of the
# browser. Add a folder here if it should become visible.
TOP_LEVEL = {"generated", "listening", "reading", "vocab", "writing"}
# The pages live in dev/; Vercel rewrites serve them at the domain root.
OUT = os.path.join(ROOT, "dev", "index.html")


def walk(d, top=False):
    kids = []
    for name in sorted(os.listdir(d)):
        if name.startswith("."):  # dotfiles/dirs: .gitignore, .gitkeep, .DS_Store, .git, .claude…
            continue
        if name in SKIP_DIR or name in SKIP_FILE or name.endswith(".pyc"):
            continue
        p = os.path.join(d, name)
        if top and (name not in TOP_LEVEL or not os.path.isdir(p)):
            continue  # root level: only the allowed folders, never loose files
        rel = os.path.relpath(p, ROOT)
        if os.path.isdir(p):
            kids.append({"n": name, "t": "d", "c": walk(p)})
        else:
            kids.append({"n": name, "t": "f", "p": rel})
    return kids


def latest_added(n=5):
    """The n most recently added files, newest first, via git history."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--name-only", "--pretty=format:"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    seen, latest = set(), []
    for line in out.splitlines():
        rel = line.strip()
        if not rel or rel in seen:
            continue
        name = os.path.basename(rel)
        top = rel.split("/")[0]
        if top not in TOP_LEVEL or name in SKIP_FILE or name.endswith(".pyc"):
            continue
        # skip dotfiles anywhere in the path (.gitignore, .gitkeep, .DS_Store, .git/…)
        if any(seg.startswith(".") for seg in rel.split("/")):
            continue
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        seen.add(rel)
        latest.append({"n": name, "p": rel, "d": os.path.dirname(rel) or "/"})
        if len(latest) >= n:
            break
    return latest


PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>English Vault — Files</title>
<style>
  :root{
    --bg:#f5f8fd;--card:#FFFFFF;--ink:#0f172a;--ink-2:#475569;--ink-3:#8a94a6;
    --line:#e6eaf1;--line-2:#eef2f8;--soft:#eff4fb;
    --blue:#1e6de6;--blue2:#3b82f6;--blued:#0f2f66;--bluebg:#eff6ff;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased}
  .wrap{max-width:720px;margin:0 auto;padding:22px 20px 90px}
  .hero{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;border-radius:20px;
    padding:18px 24px 26px;box-shadow:0 14px 36px rgba(30,109,230,.24);margin-bottom:20px}
  .nav{display:flex;gap:6px;margin:0 -4px 12px}
  .nav a{font-size:13px;font-weight:600;color:#dbeafe;text-decoration:none;padding:7px 13px;border-radius:999px;transition:.12s}
  .nav a:hover{background:rgba(255,255,255,.16);color:#fff}
  .nav a.active{background:#fff;color:var(--blue)}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#bfdbfe}
  h1{font-weight:800;font-size:29px;margin:8px 0 6px;letter-spacing:-.02em;color:#fff}
  .lede{color:#dbeafe;font-size:14.5px;margin:0}
  .search{width:100%;font-size:14px;border:1px solid var(--line);border-radius:999px;padding:11px 16px;font-family:var(--sans);outline:none;margin-bottom:16px;background:var(--card);transition:.12s}
  .search:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(30,109,230,.14)}
  #tree,.latest{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px 12px;box-shadow:0 1px 3px rgba(16,24,40,.05)}
  ul{list-style:none;margin:0;padding:0}
  li{margin:0}
  .row{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:8px;text-decoration:none;color:inherit;font-size:14.5px}
  .row:hover{background:var(--soft)}
  .tw{width:14px;display:inline-block;text-align:center;color:var(--ink-3);font-family:var(--mono);font-size:11px;flex:none}
  .ic{width:18px;flex:none;text-align:center}
  .dir>.row{cursor:pointer;font-weight:600}
  .dir>ul{margin-left:20px;border-left:1px solid var(--line-2);padding-left:6px;display:none}
  .dir.open>ul{display:block}
  a.row .n{color:var(--ink)}
  .count{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin-top:14px}
  .hide{display:none!important}
  .dir>.row:hover .n{color:var(--blue)}
  .latest{margin-top:16px}
  .latest h2{font-weight:800;font-size:17px;margin:2px 2px 2px;letter-spacing:-.01em}
  .latest .sub{color:var(--ink-3);font-size:12.5px;margin:0 2px 10px}
  .latest a.row{align-items:flex-start}
  .latest .meta{display:flex;flex-direction:column;min-width:0}
  .latest .dirp{font-family:var(--mono);font-size:11px;color:var(--ink-3);margin-top:1px}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <nav class="nav">
      <a href="./index.html" class="active">Home</a>
      <a href="./player.html">Player</a>
      <a href="./progress.html">Progress</a>
    </nav>
    <div class="eyebrow">📚 English Vault</div>
    <h1>Project files</h1>
    <p class="lede">Browse every folder and file. Click a folder to open it, a file to view it.</p>
  </div>
  <input class="search" id="q" type="text" placeholder="filter files…" autocomplete="off"/>
  <div id="tree"></div>
  <div class="count" id="count"></div>
  <div class="latest" id="latest"></div>
</div>
<script>
const TREE = __TREE__;
const LATEST = __LATEST__;
let fileCount=0;
function node(item){
  const li=document.createElement("li");
  if(item.t==="d"){
    li.className="dir";
    const row=document.createElement("div"); row.className="row";
    row.innerHTML=`<span class="tw">▸</span><span class="ic">📁</span><span class="n">${item.n}</span>`;
    row.onclick=()=>{ li.classList.toggle("open"); row.querySelector(".tw").textContent=li.classList.contains("open")?"▾":"▸"; };
    li.appendChild(row);
    const ul=document.createElement("ul");
    (item.c||[]).forEach(c=>ul.appendChild(node(c)));
    li.appendChild(ul);
  } else {
    fileCount++;
    const a=document.createElement("a");
    a.className="row"; a.href="../"+item.p.split("/").map(encodeURIComponent).join("/");
    a.dataset.path=item.p.toLowerCase();
    a.innerHTML=`<span class="tw"></span><span class="ic">📄</span><span class="n">${item.n}</span>`;
    li.appendChild(a);
  }
  return li;
}
const root=document.createElement("ul");
TREE.forEach(x=>root.appendChild(node(x)));
document.getElementById("tree").appendChild(root);
document.getElementById("count").textContent=fileCount+" files";

if(LATEST.length){
  const box=document.getElementById("latest");
  box.innerHTML=`<h2>Latest added</h2><p class="sub">The ${LATEST.length} most recently added files.</p>`;
  const ul=document.createElement("ul");
  LATEST.forEach(f=>{
    const li=document.createElement("li");
    const a=document.createElement("a");
    a.className="row"; a.href="../"+f.p.split("/").map(encodeURIComponent).join("/");
    a.innerHTML=`<span class="ic">📄</span><span class="meta"><span class="n">${f.n}</span><span class="dirp">${f.d}</span></span>`;
    li.appendChild(a); ul.appendChild(li);
  });
  box.appendChild(ul);
}

const q=document.getElementById("q");
q.addEventListener("input",()=>{
  const t=q.value.trim().toLowerCase();
  document.querySelectorAll("#tree a.row").forEach(a=>{
    a.parentElement.classList.toggle("hide", t && !a.dataset.path.includes(t));
  });
  document.querySelectorAll("#tree li.dir").forEach(d=>{
    const anyVisible=[...d.querySelectorAll("a.row")].some(a=>!a.parentElement.classList.contains("hide"));
    d.classList.toggle("hide", t && !anyVisible);
    if(t && anyVisible){ d.classList.add("open"); const tw=d.querySelector(":scope > .row .tw"); if(tw) tw.textContent="▾"; }
  });
});
</script>
</body>
</html>
'''


def main():
    tree = json.dumps(walk(ROOT, top=True), ensure_ascii=False)
    latest = json.dumps(latest_added(5), ensure_ascii=False)
    html = PAGE.replace("__TREE__", tree).replace("__LATEST__", latest)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}")
    # keep the road-listening player in sync with the current set of listening tracks
    try:
        import build_player
        build_player.main()
    except Exception as e:
        print(f"WARNING: build_player failed ({e})")
    # keep the translation-practice page in sync with vocab/translations.json
    try:
        import build_translate
        build_translate.main()
    except Exception as e:
        print(f"WARNING: build_translate failed ({e})")
    # keep the all-vocabulary browser in sync with every deck's cards
    try:
        import build_all_vocab
        build_all_vocab.main()
    except Exception as e:
        print(f"WARNING: build_all_vocab failed ({e})")
    # keep the paraphrase practice page in sync with vocab/paraphrases.json
    try:
        import build_paraphrase
        build_paraphrase.main()
    except Exception as e:
        print(f"WARNING: build_paraphrase failed ({e})")
    # keep the dictation deck in sync with the vocab — a word carded today must
    # be drillable today. The builder lives with its skill, so it is run as a
    # subprocess rather than imported.
    dict_build = os.path.join(ROOT, ".claude", "skills", "dictation", "scripts", "build.py")
    if os.path.exists(dict_build):
        try:
            r = subprocess.run([sys.executable, dict_build, "--repo-root", ROOT,
                                "--out", "generated/dictation/dictation.html"],
                               cwd=ROOT, text=True, capture_output=True)
            print((r.stdout or "").strip() or "WARNING: dictation build said nothing")
            if r.returncode != 0:
                print(f"WARNING: dictation build failed:\n{(r.stderr or '').strip()}")
        except Exception as e:
            print(f"WARNING: dictation build failed ({e})")
    # keep the progress page pointing at the newest deck
    try:
        import build_progress
        build_progress.main()
    except Exception as e:
        print(f"WARNING: build_progress failed ({e})")


if __name__ == "__main__":
    main()
