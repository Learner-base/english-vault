#!/usr/bin/env python3
"""Regenerate the root index.html file browser from the current project tree.

Walks the whole project (skipping .git, .claude, __pycache__, .pyc, .DS_Store),
builds a nested JSON tree of every folder/file, and writes it into index.html —
a self-contained, expandable file browser shown as the site's main page.

Run this after creating or deleting ANY file or folder so the main page stays in
sync:

    python3 scripts/build_index.py
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIR = {".git", ".claude", "__pycache__", "scripts"}
# CLAUDE.md is an AI instruction file and index.html is this page itself — the user
# doesn't need either listed in the browser.
SKIP_FILE = {".DS_Store", "CLAUDE.md", "index.html"}
OUT = os.path.join(ROOT, "index.html")


def walk(d):
    kids = []
    for name in sorted(os.listdir(d)):
        if name in SKIP_DIR or name in SKIP_FILE or name.endswith(".pyc"):
            continue
        p = os.path.join(d, name)
        rel = os.path.relpath(p, ROOT)
        if os.path.isdir(p):
            kids.append({"n": name, "t": "d", "c": walk(p)})
        else:
            kids.append({"n": name, "t": "f", "p": rel})
    return kids


PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>English Vault — Files</title>
<style>
  :root{
    --paper:#FCFCFA;--card:#FFFFFF;--ink:#17170F;--ink-2:#57564C;--ink-3:#8A897E;
    --line:#E4E3DC;--line-2:#EFEEE8;--soft:#F4F3EC;--focus:#2E5AAC;
    --serif:Georgia,"Times New Roman",serif;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased}
  .wrap{max-width:720px;margin:0 auto;padding:26px 20px 90px}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3)}
  h1{font-family:var(--serif);font-weight:600;font-size:30px;margin:6px 0 4px;letter-spacing:-.01em}
  .lede{color:var(--ink-2);font-size:15px;margin:0 0 20px}
  .search{width:100%;font-size:14px;border:1px solid var(--line);border-radius:999px;padding:11px 16px;font-family:var(--sans);outline:none;margin-bottom:18px;background:var(--card)}
  .search:focus{border-color:var(--ink)}
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
</style>
</head>
<body>
<div class="wrap">
  <div class="eyebrow">English Vault</div>
  <h1>Project files</h1>
  <p class="lede">Browse every folder and file. Click a folder to open it, a file to view it.</p>
  <input class="search" id="q" type="text" placeholder="filter files…" autocomplete="off"/>
  <div id="tree"></div>
  <div class="count" id="count"></div>
</div>
<script>
const TREE = __TREE__;
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
    a.className="row"; a.href="./"+item.p.split("/").map(encodeURIComponent).join("/");
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
    tree = json.dumps(walk(ROOT), ensure_ascii=False)
    html = PAGE.replace("__TREE__", tree)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
