#!/usr/bin/env python3
"""Build a self-contained spelling-dictation quiz HTML from the project's vocab.

The page speaks an English word aloud (browser SpeechSynthesis); you type what you
hear; it checks the spelling. On a mistake it reveals the correct spelling and makes
you retype it before moving on. Words come from BOTH vocab/known.md and
vocab/learning.json (deduped). Words that exist in learning.json carry their meaning
(def / uz / example) so a little hint can be shown after you answer.

Usage:
    python build.py --repo-root . --out generated/dictation/dictation.html

Everything (word list + metadata) is embedded into the HTML, so the file works when
opened directly (file://) with no server.
"""
import argparse, json, os, re, html


def load_known(path):
    """vocab/known.md is a flat word list with '## A' headings. Return lowercase words."""
    if not os.path.exists(path):
        return []
    words = []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        for tok in s.split():
            w = tok.strip().lower()
            # keep plain alphabetic words (drop single letters, apostrophe-forms noise)
            if re.fullmatch(r"[a-z][a-z'’-]*[a-z]", w):
                words.append(w)
    return words


def load_learning(path):
    """vocab/learning.json → {word: {def,uz,ex,pos}} keyed by base word `w`."""
    if not os.path.exists(path):
        return {}
    data = json.load(open(path, encoding="utf-8"))
    meta = {}
    for cards in data.values():
        for c in cards:
            w = str(c.get("w", "")).strip().lower()
            if not w or not re.fullmatch(r"[a-z][a-z'’ -]*", w):
                continue
            meta[w] = {
                "def": c.get("def", ""),
                "uz": c.get("uz", ""),
                "ex": c.get("ex", ""),
                "pos": c.get("pos", ""),
            }
    return meta


# ---------------------------------------------------------------------------
# Spelling-difficulty tagging. This deck is for the HARD words: the ones that
# trip people on S vs C, TH, PH, silent letters, -ough, doubled letters and
# British spellings. Each kept word carries a `tags` list so the page can offer
# a "focus on one pattern" filter, and easy phonetic words are dropped.
# ---------------------------------------------------------------------------

# Obvious non-words / scraping artifacts that leaked into known.md.
JUNK = {
    "correctanswer", "qpart", "div", "span", "href", "http", "https", "html",
    "css", "aria", "nbsp", "img", "src", "utf", "www", "com", "png", "jpg",
}

# Clearly easy words to drop even though they're long enough (moderate filter).
EASY = {
    "about", "above", "after", "again", "along", "began", "being", "below",
    "every", "first", "great", "group", "house", "large", "learn", "leave",
    "money", "never", "night", "often", "other", "place", "plant", "point",
    "power", "quite", "right", "shall", "small", "sound", "start", "still",
    "story", "their", "there", "these", "thing", "think", "third", "three",
    "today", "under", "until", "water", "where", "which", "while", "white",
    "whole", "world", "would", "write", "young", "plans", "shops", "stops",
    "walks", "talks", "books", "kings", "rings", "stars", "roads", "rocks",
    "trees", "foods", "hours", "weeks", "years", "found", "round", "count",
    "close", "those", "since", "clean", "clear", "money", "table", "green",
}

# Friendly label per tag code (also mirrored in the page's JS).
TAG_ORDER = ["sc", "th", "ph", "ough", "silent", "double", "british", "vowel"]


def tag_word(w):
    """Return the set of spelling-challenge tags a word exercises."""
    t = set()
    if "ph" in w:
        t.add("ph")
    if "th" in w:
        t.add("th")
    if re.search(r"ough|augh", w):
        t.add("ough")
    if (re.search(r"^(kn|wr|gn|ps|rh)", w)          # knot, wrist, gnome, psalm, rhythm
            or re.search(r"(mb|bt|mn)$", w)          # thumb, doubt, autumn
            or re.search(r"isl|aisl|stle|sten|salm|onest|oreign|nsc", w)):  # island, castle, honest, foreign, conscience
        t.add("silent")
    if re.search(r"(bb|cc|dd|ff|gg|ll|mm|nn|pp|rr|ss|tt|zz)", w):
        t.add("double")
    if (re.search(r"iour|avour|olour|arbour|abour|eighbour|avor|olor", w)
            or re.search(r"is(e|ed|ing|ation)$", w)
            or re.search(r"[bcdgtv]re$", w)
            or "ae" in w or "oe" in w
            or "jewell" in w):
        t.add("british")
    if re.search(r"sc|c[eiy]|ss|ce$|se$|cei|cie|cious|scious|nce$|nse$", w):
        t.add("sc")
    if re.search(r"eau|ieu|eig|uea|oeu|iai|eou|uou|aer|ueue|uar", w):
        t.add("vowel")
    return t


# Curated hard-to-spell words: classic English spelling-demons + the ones the
# user named. Words not already in the vocab are added; `tags` here are merged
# with the auto-classifier so a word always lands in the right focus group.
CURATED = [
    # user's explicitly-confusing words
    {"w": "spelling", "tags": ["double"]},
    {"w": "photograph", "tags": ["ph"]},
    {"w": "photographer", "tags": ["ph"]},
    {"w": "behaviour", "tags": ["british"], "def": "the way someone acts (US spelling: behavior)."},
    {"w": "unnecessary", "tags": ["double", "sc"]},
    {"w": "sugar", "tags": ["sc"], "def": "sweet substance — the 'su' sounds like 'sh'."},
    {"w": "disease", "tags": ["sc"], "def": "an illness — note the s/c-style trap and the 'ea'."},
    {"w": "thought", "tags": ["th", "ough"]},
    {"w": "though", "tags": ["th", "ough"]},
    {"w": "through", "tags": ["th", "ough"]},
    {"w": "thread", "tags": ["th"]},
    # S / C confusables
    {"w": "necessary", "tags": ["sc", "double"]}, {"w": "conscience", "tags": ["sc", "silent"]},
    {"w": "conscious", "tags": ["sc"]}, {"w": "science", "tags": ["sc"]},
    {"w": "discipline", "tags": ["sc"]}, {"w": "fascinate", "tags": ["sc", "silent"]},
    {"w": "muscle", "tags": ["sc", "silent"]}, {"w": "scissors", "tags": ["sc", "silent", "double"]},
    {"w": "ascend", "tags": ["sc"]}, {"w": "descend", "tags": ["sc"]},
    {"w": "precise", "tags": ["sc"]}, {"w": "precious", "tags": ["sc"]},
    {"w": "sufficient", "tags": ["sc"]}, {"w": "efficient", "tags": ["sc", "double"]},
    {"w": "ancient", "tags": ["sc"]}, {"w": "receive", "tags": ["sc"]},
    {"w": "deceive", "tags": ["sc"]}, {"w": "licence", "tags": ["sc"]},
    {"w": "defence", "tags": ["sc"]}, {"w": "absence", "tags": ["sc"]},
    {"w": "success", "tags": ["sc", "double"]}, {"w": "accessory", "tags": ["sc", "double"]},
    # doubled letters
    {"w": "accommodate", "tags": ["double"]}, {"w": "occurrence", "tags": ["double", "sc"]},
    {"w": "embarrass", "tags": ["double"]}, {"w": "millennium", "tags": ["double"]},
    {"w": "parallel", "tags": ["double"]}, {"w": "exaggerate", "tags": ["double"]},
    {"w": "tomorrow", "tags": ["double"]}, {"w": "questionnaire", "tags": ["double", "vowel"]},
    {"w": "committee", "tags": ["double"]}, {"w": "possession", "tags": ["double"]},
    {"w": "beginning", "tags": ["double"]}, {"w": "recommend", "tags": ["double"]},
    {"w": "assessment", "tags": ["double", "sc"]},
    # silent letters
    {"w": "knowledge", "tags": ["silent"]}, {"w": "knife", "tags": ["silent"]},
    {"w": "wrist", "tags": ["silent"]}, {"w": "doubt", "tags": ["silent"]},
    {"w": "debt", "tags": ["silent"]}, {"w": "subtle", "tags": ["silent"]},
    {"w": "island", "tags": ["silent"]}, {"w": "aisle", "tags": ["silent"]},
    {"w": "honest", "tags": ["silent"]}, {"w": "foreign", "tags": ["silent"]},
    {"w": "campaign", "tags": ["silent"]}, {"w": "column", "tags": ["silent"]},
    {"w": "autumn", "tags": ["silent"]}, {"w": "wednesday", "tags": ["silent"]},
    {"w": "february", "tags": ["silent"]}, {"w": "rhythm", "tags": ["silent", "vowel"]},
    {"w": "rhyme", "tags": ["silent"]}, {"w": "yacht", "tags": ["silent", "vowel"]},
    # PH words
    {"w": "physical", "tags": ["ph"]}, {"w": "philosophy", "tags": ["ph"]},
    {"w": "phenomenon", "tags": ["ph"]}, {"w": "elephant", "tags": ["ph"]},
    {"w": "nephew", "tags": ["ph"]}, {"w": "emphasis", "tags": ["ph"]},
    {"w": "geography", "tags": ["ph"]}, {"w": "paragraph", "tags": ["ph"]},
    {"w": "pharmacy", "tags": ["ph"]}, {"w": "sphere", "tags": ["ph"]},
    {"w": "alphabet", "tags": ["ph"]}, {"w": "sympathy", "tags": ["ph", "th"]},
    # -ough / -augh
    {"w": "thorough", "tags": ["ough", "th"]}, {"w": "tough", "tags": ["ough"]},
    {"w": "enough", "tags": ["ough"]}, {"w": "cough", "tags": ["ough"]},
    {"w": "rough", "tags": ["ough"]}, {"w": "dough", "tags": ["ough"]},
    {"w": "bought", "tags": ["ough"]}, {"w": "brought", "tags": ["ough"]},
    {"w": "drought", "tags": ["ough"]}, {"w": "daughter", "tags": ["ough"]},
    {"w": "caught", "tags": ["ough"]},
    # British spellings & tricky vowels
    {"w": "colour", "tags": ["british"]}, {"w": "favourite", "tags": ["british"]},
    {"w": "neighbour", "tags": ["british", "vowel"]}, {"w": "jewellery", "tags": ["british", "double"]},
    {"w": "restaurant", "tags": ["vowel"]}, {"w": "bureau", "tags": ["vowel"]},
    {"w": "beautiful", "tags": ["vowel"]}, {"w": "queue", "tags": ["vowel"]},
    {"w": "manoeuvre", "tags": ["vowel"]}, {"w": "liaison", "tags": ["vowel"]},
    {"w": "guarantee", "tags": ["vowel", "double"]}, {"w": "colleague", "tags": ["vowel", "double"]},
    {"w": "definitely", "tags": []}, {"w": "separate", "tags": []},
    {"w": "environment", "tags": ["silent"]}, {"w": "government", "tags": ["silent"]},
    {"w": "business", "tags": ["silent", "double"]}, {"w": "vacuum", "tags": ["vowel"]},
    {"w": "category", "tags": []}, {"w": "calendar", "tags": []},
    {"w": "cemetery", "tags": ["sc"]}, {"w": "mischievous", "tags": ["sc"]},
    {"w": "pronunciation", "tags": ["sc"]}, {"w": "argument", "tags": []},
    {"w": "satellite", "tags": ["double"], "def": "an object (or spacecraft) that orbits a planet — note the single 't', double 'l'."},
]


def is_easy(w, tags):
    """Moderate filter: drop obvious/short/regular words, keep the rest."""
    if w in JUNK:
        return True
    if len(w) <= 3:
        return True
    if w in EASY:
        return True
    if len(w) == 4 and not tags:
        return True
    return False


def build_pool(known, learning, curated):
    """Merge sources, tag by spelling difficulty, drop easy words, sort."""
    seen = {}
    # learning first so their metadata wins
    for w, m in learning.items():
        seen[w] = {"w": w, "src": "learning", **m}
    for w in known:
        seen.setdefault(w, {"w": w, "src": "known", "def": "", "uz": "", "ex": "", "pos": ""})
    # curated: may introduce words absent from the vocab, and carries forced tags
    for c in curated:
        w = c["w"]
        if w in seen:
            seen[w].setdefault("_ct", set()).update(c.get("tags", []))
            if not seen[w].get("def") and c.get("def"):
                seen[w]["def"] = c["def"]
        else:
            seen[w] = {"w": w, "src": "curated", "def": c.get("def", ""), "uz": "",
                       "ex": "", "pos": "", "_ct": set(c.get("tags", []))}
    pool = []
    for v in seen.values():
        w = v["w"]
        if " " in w:  # phrases can't be dictated letter-perfect
            continue
        tags = sorted(tag_word(w) | v.pop("_ct", set()), key=lambda x: TAG_ORDER.index(x) if x in TAG_ORDER else 99)
        if is_easy(w, tags):
            continue
        v["tags"] = tags
        pool.append(v)
    pool.sort(key=lambda v: v["w"])
    return pool


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Spelling Dictation — English Vault</title>
<style>
  :root{
    color-scheme:light dark;
    --paper:#FBFAF7; --card:#FFFFFF; --card-2:#F6F5F0;
    --ink:#15150F; --ink-2:#55544A; --ink-3:#8B8A7E;
    --line:#E5E4DC; --line-2:#EFEEE8; --soft:#F3F2EA;
    --accent:#2E5AAC; --accent-soft:#E8EEFA;
    --ok:#1B6B45; --ok-bg:#E7F4EC;
    --red:#C0362C; --bad-bg:#FBEBE8;
    --shadow:0 1px 2px rgba(20,20,10,.04), 0 8px 24px -12px rgba(20,20,10,.18);
    --r:16px; --r-sm:11px;
    --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --paper:#14140F; --card:#1C1C16; --card-2:#232219;
      --ink:#F2F1EA; --ink-2:#B4B2A6; --ink-3:#84837A;
      --line:#2E2D24; --line-2:#26251E; --soft:#232219;
      --accent:#8CB2F5; --accent-soft:#1D2740;
      --ok:#6FD39B; --ok-bg:#16281E;
      --red:#F1897C; --bad-bg:#2C1A17;
      --shadow:0 1px 2px rgba(0,0,0,.5), 0 10px 30px -14px rgba(0,0,0,.8);
    }
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  html{-webkit-text-size-adjust:100%}
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;
    -webkit-font-smoothing:antialiased;overflow-wrap:break-word}
  .wrap{max-width:640px;margin:0 auto;
    padding:clamp(18px,4vw,32px) clamp(14px,4vw,22px) calc(84px + env(safe-area-inset-bottom))}
  button{font-family:inherit;cursor:pointer;color:inherit}
  :focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
  .hide{display:none!important}

  /* ---------- header ---------- */
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--ink-3);display:flex;align-items:center;gap:8px}
  .eyebrow::before{content:"";width:18px;height:1px;background:var(--ink-3)}
  h1{font-family:var(--serif);font-weight:600;font-size:clamp(26px,6.4vw,34px);line-height:1.1;
    margin:10px 0 6px;letter-spacing:-.015em}
  .lede{color:var(--ink-2);font-size:15px;margin:0;max-width:52ch}

  /* ---------- buttons ---------- */
  .btn{border:1px solid var(--ink);background:var(--ink);color:var(--paper);border-radius:999px;
    padding:13px 22px;font-size:15px;font-weight:600;min-height:46px;
    transition:opacity .15s,transform .06s,box-shadow .15s;box-shadow:var(--shadow)}
  .btn:hover{opacity:.9}.btn:active{transform:translateY(1px)}
  .btn.ghost{background:transparent;color:var(--ink);border-color:var(--line);box-shadow:none}
  .btn.ghost:hover{border-color:var(--ink-2)}
  .btn.wide{width:100%;justify-content:center}

  /* ---------- setup ---------- */
  .setup{margin-top:24px;display:grid;gap:14px}
  .fieldset{background:var(--card);border:1px solid var(--line);border-radius:var(--r);
    padding:16px 16px 18px;box-shadow:var(--shadow)}
  .lab{font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--ink-3);
    text-transform:uppercase;display:block;margin-bottom:10px}
  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  /* segmented control — scrolls sideways on a phone instead of wrapping into a wall */
  .switch{display:flex;gap:4px;background:var(--soft);border:1px solid var(--line);
    border-radius:999px;padding:4px;overflow-x:auto;scrollbar-width:none;
    -webkit-overflow-scrolling:touch;scroll-snap-type:x proximity}
  .switch::-webkit-scrollbar{display:none}
  .switch button{border:none;background:none;border-radius:999px;padding:9px 14px;font-size:13.5px;
    color:var(--ink-2);white-space:nowrap;flex:0 0 auto;min-height:38px;scroll-snap-align:start;
    transition:background .15s,color .15s}
  .switch button:hover{color:var(--ink)}
  .switch button[aria-pressed="true"]{background:var(--card);color:var(--ink);font-weight:650;
    box-shadow:0 1px 2px rgba(20,20,10,.12)}
  .switch button[disabled]{opacity:.5;cursor:default}
  .toggle{display:inline-flex;align-items:center;gap:9px;font-family:var(--mono);font-size:12px;
    letter-spacing:.04em;color:var(--ink-2);text-transform:uppercase;
    background:var(--card);border:1px solid var(--line);border-radius:999px;padding:9px 15px;
    min-height:42px;cursor:pointer}
  .toggle input{accent-color:var(--accent);width:16px;height:16px;margin:0}
  .stat-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;
    font-family:var(--mono);font-size:12px;color:var(--ink-2)}
  .stat{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:7px 13px}
  .stat b{color:var(--ink);font-size:13px}
  .reset-link{background:none;border:none;color:var(--ink-3);text-decoration:underline;
    font-family:var(--mono);font-size:12px;padding:6px 2px;margin-left:auto}

  /* ---------- quiz ---------- */
  #quiz{display:none}
  .top{display:flex;align-items:center;gap:12px;margin-bottom:10px}
  .top .back{background:none;border:none;color:var(--ink-2);font-size:14px;padding:8px 4px;min-height:40px}
  .top .spacer{flex:1}
  .counter{font-family:var(--mono);font-size:12px;color:var(--ink-3);
    background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:5px 11px}
  .counter b{color:var(--ink)}
  .progress{height:5px;background:var(--line-2);border-radius:999px;margin:0 0 20px;overflow:hidden}
  .progress i{display:block;height:100%;border-radius:999px;
    background:linear-gradient(90deg,var(--accent),var(--ink));width:0;transition:width .35s ease}

  .panel{border:1px solid var(--line);border-radius:var(--r);background:var(--card);
    padding:clamp(22px,5vw,34px) clamp(16px,4.5vw,28px);text-align:center;box-shadow:var(--shadow)}
  .pos{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-3);min-height:15px}
  /* speak button with pulsing rings while the word is being read */
  .speak-wrap{position:relative;width:92px;height:92px;margin:10px auto 6px;display:grid;place-items:center}
  .speak-big{position:relative;z-index:2;border:1px solid var(--line);background:var(--card-2);
    width:84px;height:84px;border-radius:50%;font-size:32px;display:grid;place-items:center;
    transition:border-color .15s,transform .08s,background .15s}
  .speak-big:hover{border-color:var(--accent);background:var(--accent-soft)}
  .speak-big:active{transform:scale(.96)}
  .speak-wrap::before,.speak-wrap::after{content:"";position:absolute;inset:4px;border-radius:50%;
    border:1px solid var(--accent);opacity:0}
  .speak-big.playing{border-color:var(--accent);background:var(--accent-soft)}
  .speak-wrap:has(.playing)::before{animation:ring 1.4s ease-out infinite}
  .speak-wrap:has(.playing)::after{animation:ring 1.4s ease-out .7s infinite}
  @keyframes ring{0%{transform:scale(.9);opacity:.55}100%{transform:scale(1.35);opacity:0}}
  .replay-hint{font-family:var(--mono);font-size:11px;color:var(--ink-3);margin:10px 0 22px;letter-spacing:.03em}
  .replay-hint kbd{font-family:var(--mono);font-size:10.5px;color:var(--ink-2);background:var(--soft);
    border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:2px 6px}
  .replay-hint .taponly{display:none}
  @media (max-width:420px){ .replay-hint .kbonly{display:none} .replay-hint .taponly{display:inline} }

  /* 17px keeps iOS Safari from zooming the page when the field is focused */
  .answer{width:100%;font-family:var(--serif);font-size:clamp(24px,7vw,32px);text-align:center;
    border:none;border-bottom:2px solid var(--line);background:transparent;color:var(--ink);
    padding:10px 4px;letter-spacing:.02em;outline:none;transition:border-color .18s,color .18s;
    min-height:56px}
  .answer::placeholder{font-family:var(--sans);font-size:16px;color:var(--ink-3);letter-spacing:0}
  .answer:focus{border-color:var(--accent)}
  .answer.ok{border-color:var(--ok);color:var(--ok)}
  .answer.bad{border-color:var(--red);color:var(--red)}
  .answer:disabled{opacity:1}

  .verdict{min-height:62px;margin-top:16px}
  .verdict .diff{font-family:var(--serif);font-size:clamp(20px,5.5vw,26px);letter-spacing:.02em;
    word-break:break-word;background:var(--soft);border-radius:var(--r-sm);padding:10px 12px;display:inline-block}
  .verdict .diff .wrong{color:var(--red);text-decoration:line-through;text-decoration-thickness:1px}
  .verdict .diff .miss{color:var(--ok);border-bottom:2px solid var(--ok)}
  .verdict .lbl{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;
    color:var(--ink-3);margin-bottom:8px;display:block}
  .verdict.good .msg{color:var(--ok);font-weight:650;font-size:19px;
    background:var(--ok-bg);border-radius:999px;padding:9px 18px;display:inline-block}
  .verdict .retype{font-family:var(--mono);font-size:12.5px;color:var(--red);margin-top:10px}

  .meaning{margin-top:20px;padding-top:16px;border-top:1px solid var(--line-2);text-align:left;
    font-size:15px;color:var(--ink-2)}
  .meaning .d{color:var(--ink)}
  .meaning .uz{font-style:italic;margin-top:4px}
  .meaning .ex{margin-top:10px;font-family:var(--serif);color:var(--ink-2);
    border-left:2px solid var(--line);padding-left:12px}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
  .chips .lbl{width:100%;margin-bottom:2px}
  .chip{font-family:var(--mono);font-size:11px;border:1px solid var(--line);border-radius:999px;
    padding:4px 10px;color:var(--ink-2);background:var(--soft)}
  .cta{margin-top:24px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  .cta .btn{min-width:160px}

  /* ---------- done ---------- */
  .done{text-align:center;padding:46px 16px;display:none}
  .done .mark{font-size:40px;line-height:1}
  .done h2{font-family:var(--serif);font-size:clamp(23px,5.6vw,28px);margin:12px 0 8px}
  .done p{color:var(--ink-2);margin:0 0 26px;font-family:var(--mono);font-size:13px}

  @media (prefers-reduced-motion:reduce){
    *{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
  }
</style>
</head>
<body>
<div class="wrap">

  <!-- SETUP -->
  <section id="setup">
    <div class="eyebrow">English Vault · Dictation</div>
    <h1>Spelling test — hard words</h1>
    <p class="lede">Only the tricky ones: S vs C, TH, PH, silent letters, -ough, doubled letters and
      British spellings. Listen, type it, retype any you miss.</p>

    <div class="setup">
      <div class="fieldset">
        <span class="lab">Focus on a spelling pattern</span>
        <div class="switch" id="focusSwitch">
          <button data-tag="all" aria-pressed="true">All hard</button>
          <button data-tag="sc">S / C</button>
          <button data-tag="th">TH</button>
          <button data-tag="ph">PH</button>
          <button data-tag="ough">-ough</button>
          <button data-tag="silent">Silent</button>
          <button data-tag="double">Double</button>
          <button data-tag="british">British</button>
        </div>
      </div>

      <div class="fieldset">
        <span class="lab">Word source</span>
        <div class="switch" id="srcSwitch">
          <button data-src="all" aria-pressed="true">All words</button>
          <button data-src="learning">Learning only</button>
          <button data-src="mistakes">My mistakes</button>
        </div>
      </div>

      <div class="fieldset">
        <span class="lab">Word set</span>
        <div class="switch" id="modeSwitch">
          <button data-mode="groups" aria-pressed="true">Groups of 30</button>
          <button data-mode="random">Random</button>
        </div>
        <div id="groupsWrap" style="margin-top:14px">
          <span class="lab">Pick a group of 30</span>
          <div class="switch" id="batchSwitch"></div>
        </div>
        <div id="randomWrap" style="margin-top:14px;display:none">
          <span class="lab">How many random words</span>
          <div class="switch" id="lenSwitch">
            <button data-len="15" aria-pressed="true">15</button>
            <button data-len="30">30</button>
            <button data-len="50">50</button>
            <button data-len="0">All</button>
          </div>
        </div>
      </div>

      <div class="row">
        <label class="toggle"><input type="checkbox" id="shuffle" checked> Shuffle</label>
        <label class="toggle"><input type="checkbox" id="slow"> Speak slowly</label>
      </div>

      <button class="btn wide" id="startBtn">Start test →</button>

      <div class="stat-row">
        <span class="stat">Pool <b id="poolCount">0</b></span>
        <span class="stat">Mastered <b id="masterCount">0</b></span>
        <span class="stat">Mistakes <b id="missCount">0</b></span>
        <button class="reset-link" id="resetBtn">reset progress</button>
      </div>
    </div>
  </section>

  <!-- QUIZ -->
  <section id="quiz">
    <div class="top">
      <button class="back" id="backBtn">← End</button>
      <div class="spacer"></div>
      <div class="counter"><b id="idx">1</b> / <span id="total">1</span></div>
    </div>
    <div class="progress"><i id="bar"></i></div>

    <div class="panel">
      <div class="pos" id="pos"></div>
      <div class="speak-wrap">
        <button class="speak-big" id="speakBtn" title="Play (Space / R)" aria-label="Play the word">🔊</button>
      </div>
      <div class="replay-hint"><span class="kbonly"><kbd>Space</kbd> or <kbd>R</kbd> to replay ·
        <kbd>Enter</kbd> to check</span><span class="taponly">tap 🔊 to hear it again</span></div>

      <input class="answer" id="answer" type="text" autocomplete="off" autocapitalize="off"
             autocorrect="off" spellcheck="false" enterkeyhint="done" inputmode="text"
             placeholder="type what you hear" />

      <div class="verdict" id="verdict"></div>
      <div class="meaning hide" id="meaning"></div>

      <div class="cta" id="cta"></div>
    </div>
  </section>

  <!-- DONE -->
  <section id="doneScreen" class="done">
    <div class="mark">✓</div>
    <h2 id="doneTitle">Session complete</h2>
    <p id="doneStats"></p>
    <button class="btn" id="againBtn">Back to start</button>
  </section>

</div>

<script>
const WORDS = /*__WORDS__*/[];
const LS_MASTER = "dict_mastered_v1";
const LS_MISS   = "dict_mistakes_v1";

const $ = s => document.querySelector(s);
const load = (k) => { try { return JSON.parse(localStorage.getItem(k)) || {}; } catch(e){ return {}; } };
const save = (k,v) => localStorage.setItem(k, JSON.stringify(v));
let mastered = load(LS_MASTER);   // {word:true}
let mistakes = load(LS_MISS);     // {word:count}

// ---- setup state ----
let src="all", focus="all", sessionLen=15, mode="groups", batchIndex=0;
const GROUP=30;
const TAG_LABELS={sc:"S / C",th:"TH",ph:"PH",ough:"-ough",silent:"silent letter",double:"double letter",british:"British",vowel:"tricky vowels"};
function matchPool(){
  let p=WORDS.slice();
  if(src==="learning") p=p.filter(w=>w.src==="learning");
  if(src==="mistakes") p=p.filter(w=>mistakes[w.w]);
  if(focus!=="all") p=p.filter(w=>(w.tags||[]).includes(focus));
  return p;
}
// split the current pool into consecutive groups of GROUP words: [[start,end],…]
function batchRanges(){
  const n=matchPool().length, out=[];
  for(let i=0;i<n;i+=GROUP) out.push([i, Math.min(i+GROUP, n)]);
  return out;
}
function renderBatches(){
  const ranges=batchRanges(), box=$("#batchSwitch");
  if(batchIndex>=ranges.length) batchIndex=0;
  box.innerHTML="";
  if(!ranges.length){
    box.innerHTML='<button aria-pressed="true" disabled>— no words —</button>';
    return;
  }
  ranges.forEach(([s,e],k)=>{
    const b=document.createElement("button");
    b.dataset.batch=k; b.textContent=(s+1)+"–"+e;
    if(k===batchIndex) b.setAttribute("aria-pressed","true");
    box.appendChild(b);
  });
}
function refreshStats(){
  $("#poolCount").textContent = matchPool().length;
  $("#masterCount").textContent = Object.keys(mastered).length;
  $("#missCount").textContent = Object.keys(mistakes).length;
  renderBatches();
}
$("#srcSwitch").addEventListener("click", e=>{
  const b=e.target.closest("button"); if(!b) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed", x===b));
  src=b.dataset.src; batchIndex=0; refreshStats();
});
$("#focusSwitch").addEventListener("click", e=>{
  const b=e.target.closest("button"); if(!b) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed", x===b));
  focus=b.dataset.tag; batchIndex=0; refreshStats();
});
$("#modeSwitch").addEventListener("click", e=>{
  const b=e.target.closest("button"); if(!b) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed", x===b));
  mode=b.dataset.mode;
  $("#groupsWrap").style.display = mode==="groups" ? "" : "none";
  $("#randomWrap").style.display = mode==="random" ? "" : "none";
});
$("#batchSwitch").addEventListener("click", e=>{
  const b=e.target.closest("button"); if(!b || b.disabled) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed", x===b));
  batchIndex=+b.dataset.batch;
});
$("#lenSwitch").addEventListener("click", e=>{
  const b=e.target.closest("button"); if(!b) return;
  [...e.currentTarget.children].forEach(x=>x.setAttribute("aria-pressed", x===b));
  sessionLen=+b.dataset.len;
});
$("#resetBtn").addEventListener("click", ()=>{
  if(!confirm("Clear mastered words and mistake log?")) return;
  mastered={}; mistakes={}; save(LS_MASTER,mastered); save(LS_MISS,mistakes); refreshStats();
});

// ---- speech ----
let slow=false;
function speak(word){
  if(!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(word);
  u.lang="en-GB"; u.rate= slow?0.6:0.9;
  const vs=speechSynthesis.getVoices();
  const v=vs.find(x=>/en-GB/i.test(x.lang)) || vs.find(x=>/en/i.test(x.lang));
  if(v) u.voice=v;
  const btn=$("#speakBtn");
  u.onstart=()=>btn.classList.add("playing");
  u.onend=()=>btn.classList.remove("playing");
  speechSynthesis.speak(u);
}
if("speechSynthesis" in window) speechSynthesis.onvoiceschanged=()=>{};

// ---- session ----
let queue=[], pos=0, retrying=false, correctThisWord=0, wrongThisWord=0, doneWords=0;
function shuffleInPlace(a){
  for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; }
  return a;
}
function buildQueue(){
  const pool = matchPool();
  if(mode==="groups"){
    // exactly the chosen group of 30 (last group may be shorter); groups never overlap
    const r=batchRanges()[batchIndex];
    let words = r ? pool.slice(r[0], r[1]) : [];
    if($("#shuffle").checked) shuffleInPlace(words);
    return words;
  }
  // random: a chosen number of words drawn randomly from the whole (filtered) pool
  let words = shuffleInPlace(pool.slice());
  if(sessionLen>0) words = words.slice(0, sessionLen);
  return words;
}
function startSession(){
  slow=$("#slow").checked;
  queue=buildQueue();
  if(!queue.length){ alert("No words match that filter yet."); return; }
  pos=0; doneWords=0;
  $("#setup").style.display="none";
  $("#doneScreen").style.display="none";
  $("#quiz").style.display="block";
  $("#total").textContent=queue.length;
  showWord();
}
function current(){ return queue[pos]; }

function showWord(){
  retrying=false;
  const w=current();
  $("#idx").textContent=pos+1;
  $("#bar").style.width = ((pos)/queue.length*100)+"%";
  $("#pos").textContent = w.pos || "";
  const a=$("#answer");
  a.value=""; a.disabled=false; a.className="answer"; a.placeholder="type what you hear";
  $("#verdict").className="verdict"; $("#verdict").innerHTML="";
  $("#meaning").className="meaning hide"; $("#meaning").innerHTML="";
  $("#cta").innerHTML="";
  a.focus();
  setTimeout(()=>speak(w.w), 250);
}

// letter-diff render: user's answer vs correct
function renderDiff(user, correct){
  let out="", i=0;
  const u=user.toLowerCase();
  // simple char-by-char alignment
  const max=Math.max(u.length, correct.length);
  for(i=0;i<max;i++){
    const cc=correct[i]||"", uc=u[i]||"";
    if(cc===uc){ out+=`<span>${cc}</span>`; }
    else if(cc && uc){ out+=`<span class="wrong">${uc}</span><span class="miss">${cc}</span>`; }
    else if(cc){ out+=`<span class="miss">${cc}</span>`; }
    else { out+=`<span class="wrong">${uc}</span>`; }
  }
  return out;
}
function showMeaning(w){
  const tags=(w.tags||[]);
  if(!(w.def || w.uz || w.ex || tags.length)) return;
  let h="";
  if(w.def) h+=`<div class="d">${w.def}</div>`;
  if(w.uz)  h+=`<div class="uz">${w.uz}</div>`;
  if(w.ex)  h+=`<div class="ex">“${w.ex}”</div>`;
  if(tags.length){
    h+=`<div class="chips"><span class="lbl">Why it's tricky</span>`
      + tags.map(t=>`<span class="chip">${TAG_LABELS[t]||t}</span>`).join("") + `</div>`;
  }
  $("#meaning").innerHTML=h; $("#meaning").className="meaning";
}
function nextBtn(label){
  const b=document.createElement("button");
  b.className="btn"; b.textContent=label;
  b.onclick=advance; $("#cta").appendChild(b);
  b.focus();
}

function check(){
  const a=$("#answer");
  const w=current();
  const guess=a.value.trim().toLowerCase();
  if(!guess) { speak(w.w); return; }
  const correct = w.w.toLowerCase();

  if(retrying){
    // must match exactly to proceed
    if(guess===correct){
      a.className="answer ok"; a.disabled=true;
      $("#verdict").className="verdict good";
      $("#verdict").innerHTML=`<div class="msg">✓ Correct spelling</div>`;
      nextBtn(pos+1<queue.length?"Next →":"Finish");
    } else {
      a.className="answer bad";
      $("#verdict").className="verdict";
      $("#verdict").innerHTML=`<div class="lbl">Not yet — copy it exactly</div>
        <div class="diff">${renderDiff(guess,correct)}</div>
        <div class="retype">Correct spelling: <b>${correct}</b></div>`;
    }
    return;
  }

  if(guess===correct){
    a.className="answer ok"; a.disabled=true;
    $("#verdict").className="verdict good";
    $("#verdict").innerHTML=`<div class="msg">✓ ${correct}</div>`;
    mastered[correct]=true; save(LS_MASTER,mastered);
    showMeaning(w);
    nextBtn(pos+1<queue.length?"Next →":"Finish");
  } else {
    // wrong → show diff, log mistake, force retype
    a.className="answer bad"; a.value=""; a.placeholder="retype the correct spelling";
    mistakes[correct]=(mistakes[correct]||0)+1; save(LS_MISS,mistakes);
    delete mastered[correct]; save(LS_MASTER,mastered);
    retrying=true;
    $("#verdict").className="verdict";
    $("#verdict").innerHTML=`<div class="lbl">You wrote → correct</div>
      <div class="diff">${renderDiff(guess,correct)}</div>
      <div class="retype">Now type it correctly: <b>${correct}</b></div>`;
    showMeaning(w);
    a.focus();
  }
}
function advance(){
  pos++;
  if(pos>=queue.length){ finish(); return; }
  showWord();
}
function finish(){
  $("#bar").style.width="100%";
  $("#quiz").style.display="none";
  $("#doneScreen").style.display="block";
  const missNow=queue.filter(w=>mistakes[w.w]).length;
  $("#doneStats").textContent=`${queue.length} words · ${Object.keys(mistakes).length} in mistake log`;
}

// ---- events ----
$("#startBtn").onclick=startSession;
$("#againBtn").onclick=()=>{ $("#doneScreen").style.display="none"; $("#setup").style.display="block"; refreshStats(); };
$("#backBtn").onclick=()=>{ $("#quiz").style.display="none"; $("#setup").style.display="block"; refreshStats(); };
$("#speakBtn").onclick=()=>speak(current().w);
$("#answer").addEventListener("keydown", e=>{
  if(e.key==="Enter"){ e.preventDefault(); check(); return; }
});
document.addEventListener("keydown", e=>{
  if($("#quiz").style.display!=="block") return;
  const typing = document.activeElement===$("#answer");
  // R replays; Space replays only when not mid-typing text
  if(e.key==="r" && (e.ctrlKey||e.metaKey||!typing)) { /* let normal r type */ }
  if((e.key==="r"||e.key==="R") && !typing){ e.preventDefault(); speak(current().w); }
  if(e.code==="Space" && !typing){ e.preventDefault(); speak(current().w); }
});

refreshStats();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out", default="generated/dictation/dictation.html")
    a = ap.parse_args()

    root = a.repo_root
    known = load_known(os.path.join(root, "vocab", "known.md"))
    learning = load_learning(os.path.join(root, "vocab", "learning.json"))
    pool = build_pool(known, learning, CURATED)

    payload = json.dumps(pool, ensure_ascii=False)
    page = PAGE.replace("/*__WORDS__*/[]", payload)

    out = os.path.join(root, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)

    n_cur = sum(1 for w in pool if w["src"] == "curated")
    by_tag = {t: sum(1 for w in pool if t in w["tags"]) for t in TAG_ORDER}
    print(f"Wrote {out}")
    print(f"  {len(pool)} hard words  ({n_cur} curated classics added)")
    print("  by pattern: " + ", ".join(f"{t}={by_tag[t]}" for t in TAG_ORDER))


if __name__ == "__main__":
    main()
