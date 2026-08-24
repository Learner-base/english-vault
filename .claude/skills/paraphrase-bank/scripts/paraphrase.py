#!/usr/bin/env python3
"""The paraphrase bank — question wording vs passage wording.

IELTS questions almost never reuse the passage's words: the question says
"a feeling of ...", the passage says "a sense of ...". Every pair you meet is
worth keeping, because the same pairs come back test after test.

`vocab/paraphrases.json` is the bank: `{"<test>": [pair, ...]}`, one key per
test, exactly like `vocab/learning.json`. A pair is

    {"q": "feeling of",            # the question's wording
     "p": "sense of",              # the passage's wording
     "qno": "31",                  # question number(s)
     "qtext": "...",               # optional: the question sentence
     "ptext": "...",               # optional: the passage sentence
     "uz": "..."}                  # optional: Uzbek gloss

Commands
--------
    harvest <test.html>     print one candidate row per question — the question
                            wording next to the passage evidence — as the raw
                            material to turn into pairs
    add <test> [-]          merge a JSON list of pairs (stdin or --file) into
                            the bank, de-duplicating on (q, p)
    check                   which finished tests are still missing from the bank
    list                    what is in the bank

`add` rebuilds the practice page (via dev/scripts/build_index.py) unless
--no-index is given.
"""
import argparse
import html as htmlmod
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BANK = ROOT / 'vocab' / 'paraphrases.json'


# ---------------------------------------------------------------- bank I/O

def load():
    if BANK.exists():
        return json.loads(BANK.read_text(encoding='utf-8'))
    return {}


def save(bank):
    BANK.parent.mkdir(parents=True, exist_ok=True)
    BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def test_ids():
    """Every test in the repo -> its html path."""
    out = {}
    for folder in ('reading', 'listening'):
        for p in sorted((ROOT / folder).rglob('*.html')):
            out[p.stem] = p
    return out


def done_ids():
    return {k: v for k, v in test_ids().items() if '/done/' in v.as_posix()}


# ---------------------------------------------------------------- harvest

STRIP = re.compile(r'<[^>]+>')


def text(s):
    return htmlmod.unescape(STRIP.sub(' ', s)).replace('\\"', '"').replace("\\'", "'")


def squeeze(s):
    return re.sub(r'\s+', ' ', s).strip()


def prompts(src):
    """question id -> the wording the candidate reads."""
    out = {}
    for m in re.finditer(r'\{\s*id\s*:\s*(\d+)\s*,\s*prompt\s*:\s*"((?:[^"\\]|\\.)*)"', src):
        out[int(m.group(1))] = squeeze(text(m.group(2)))
    # gap-fill questions carry their wording inside the group's template string.
    # Turning every tag into a line break puts each <p> of the template on its
    # own line, so the gap's own sentence is the line holding [[n]].
    lines = htmlmod.unescape(re.sub(r'<[^>]+>', '\n', src)).splitlines()
    for line in lines:
        for m in re.finditer(r'\[\[(\d+)\]\]', line):
            qid = int(m.group(1))
            if qid not in out:
                out[qid] = squeeze(line.replace('"+', ' ').replace('"', ' '))
    return out


def json_family(src):
    """The C21-style tests keep each question as one line of JSON:
    {"id": 8, "text": "...", "correctAnswer": "...", "explanation": "..."}."""
    ps, es = {}, {}
    for line in src.splitlines():
        if '"id"' not in line or '"explanation"' not in line:
            continue
        for m in re.finditer(r'"id"\s*:\s*(\d+)\s*,(.*?)(?="id"\s*:\s*\d|$)', line):
            qid, body = int(m.group(1)), m.group(2)
            t = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', body)
            e = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"', body)
            if t:
                ps[qid] = squeeze(text(t.group(1)))
            if e:
                es[qid] = squeeze(text(e.group(1)))
    return ps, es


def expls(src):
    """question id -> the passage evidence, from the EXPL table."""
    m = re.search(r'const\s+EXPL\s*=\s*(\{.*?\})\s*;', src, re.S)
    if not m:
        return {}
    try:
        raw = json.loads(m.group(1))
    except Exception:
        return {}
    return {int(k): squeeze(text(str(v))) for k, v in raw.items()}


def harvest(path):
    src = Path(path).read_text(encoding='utf-8')
    ps, es = prompts(src), expls(src)
    jps, jes = json_family(src)
    ps = {**jps, **ps}
    es = {**jes, **es}
    ids = sorted(set(ps) | set(es))
    print(f'# {Path(path).stem} — {len(ids)} questions')
    print('# qno\tquestion wording\tpassage evidence')
    for i in ids:
        print(f'{i}\t{ps.get(i, "")}\t{es.get(i, "")}')


# ---------------------------------------------------------------- add

FIELDS = ('q', 'p', 'qno', 'qtext', 'ptext', 'uz', 'note')


def clean(pair):
    out = {}
    for f in FIELDS:
        v = pair.get(f)
        if v not in (None, ''):
            out[f] = squeeze(str(v))
    if 'q' not in out or 'p' not in out:
        raise SystemExit(f'pair without q/p: {pair}')
    return out


def add(test, pairs):
    bank = load()
    have = bank.setdefault(test, [])
    seen = {(x['q'].lower(), x['p'].lower()) for x in have}
    added = 0
    for pair in pairs:
        c = clean(pair)
        key = (c['q'].lower(), c['p'].lower())
        if key in seen:
            continue
        seen.add(key)
        have.append(c)
        added += 1
    have.sort(key=lambda x: (float(re.split(r'\D+', x.get('qno', '999') or '999')[0] or 999), x['q'].lower()))
    save(bank)
    print(f'{test}: +{added} pair(s), {len(have)} in the bank')
    return added


# ---------------------------------------------------------------- reports

def check():
    bank, done = load(), done_ids()
    missing = [t for t in sorted(done) if not bank.get(t)]
    for t in sorted(done):
        n = len(bank.get(t, []))
        print(f'{n:>4}  {t}' + ('   <- nothing collected yet' if not n else ''))
    stale = [t for t in bank if t not in test_ids()]
    if stale:
        print('\nin the bank but no such test any more: ' + ', '.join(sorted(stale)))
    if missing:
        print('\nfinished tests with no pairs yet: ' + ', '.join(missing))
        print('harvest one with:  python3 .claude/skills/paraphrase-bank/scripts/paraphrase.py harvest '
              + done[missing[0]].relative_to(ROOT).as_posix())
    return missing


def show():
    bank = load()
    total = sum(len(v) for v in bank.values())
    for t, pairs in sorted(bank.items()):
        print(f'\n== {t} ({len(pairs)})')
        for x in pairs:
            print(f'  {x.get("qno",""):>5}  {x["q"]}  ->  {x["p"]}')
    print(f'\n{total} pairs in {len(bank)} tests')


def rebuild():
    subprocess.run([sys.executable, str(ROOT / 'dev' / 'scripts' / 'build_index.py')],
                   cwd=ROOT, check=False)


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    h = sub.add_parser('harvest'); h.add_argument('html')
    a = sub.add_parser('add')
    a.add_argument('test'); a.add_argument('--file', default='-')
    a.add_argument('--no-index', action='store_true')
    sub.add_parser('check')
    sub.add_parser('list')

    args = ap.parse_args()
    if args.cmd == 'harvest':
        harvest(args.html)
    elif args.cmd == 'add':
        raw = sys.stdin.read() if args.file == '-' else Path(args.file).read_text(encoding='utf-8')
        pairs = json.loads(raw)
        if isinstance(pairs, dict):
            pairs = pairs.get('pairs', [])
        add(args.test, pairs)
        if not args.no_index:
            rebuild()
    elif args.cmd == 'check':
        check()
    else:
        show()


if __name__ == '__main__':
    main()
