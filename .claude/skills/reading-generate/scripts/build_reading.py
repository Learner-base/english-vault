#!/usr/bin/env python3
"""Assemble a Cambridge-20-style interactive reading test from templates/reading.html.

Injects a data block (const TEST / const EXPL / const answerHighlightQuotes) into the
template, sets the title/header/badge, VERIFIES every answerHighlightQuotes value is an
exact (whitespace-flexible) substring of the passages, and checks the script parses.

Usage:
  python .claude/skills/reading-generate/scripts/build_reading.py \
    --data <scratch>/data.js \
    --title "Cambridge 20 — Reading Test 1" \
    --header "Cambridge IELTS 20 — Reading Test 1" \
    --badge 20 \
    --out "reading/undone/cambridge/cambridge-20/C20-r1.html"
"""
import re, sys, json, subprocess, argparse, tempfile, os

ap = argparse.ArgumentParser()
ap.add_argument('--data', required=True, help='JS file defining const TEST, const EXPL, const answerHighlightQuotes')
ap.add_argument('--out', required=True)
ap.add_argument('--title', required=True, help='<title> text, e.g. "Cambridge 20 — Reading Test 1"')
ap.add_argument('--header', required=True, help='Header line, e.g. "Cambridge IELTS 20 — Reading Test 1"')
ap.add_argument('--badge', default='IR', help='Short badge text (e.g. C20)')
ap.add_argument('--template', default='templates/reading.html')
a = ap.parse_args()

tpl = open(a.template).read()
data = open(a.data).read().strip()

START = '/* ==== DATA-START ==== */'
END = '/* ==== DATA-END ==== */'
if START not in tpl or END not in tpl:
    sys.exit('Template is missing DATA-START/DATA-END markers — did templates/reading.html change?')
i = tpl.index(START); j = tpl.index(END) + len(END)
out = tpl[:i] + START + "\n" + data + "\n" + END + tpl[j:]

out, n1 = re.subn(r'<title>.*?</title>', '<title>' + a.title + '</title>', out, count=1)
out, n2 = re.subn(r'(<div class="font-bold text-gray-900 leading-tight">).*?(</div>)',
                  lambda m: m.group(1) + a.header + m.group(2), out, count=1)
out, n3 = re.subn(r'(flex items-center justify-center">)[^<]*(</div>)',
                  lambda m: m.group(1) + a.badge + m.group(2), out, count=1)
if not (n1 and n2 and n3):
    sys.exit(f'Header patch failed (title={n1} header={n2} badge={n3}) — template markup changed.')

# --- validate data JS + quotes against the passages ---
node_src = data + ("\nconst _p=TEST.passages.map(p=>p.body.join(' ')).join(' ').replace(/<[^>]+>/g,' ');"
                   "console.log(JSON.stringify({p:_p,q:(typeof answerHighlightQuotes!=='undefined'?answerHighlightQuotes:{}),"
                   "ids:TEST.groups.flatMap(g=>g.type==='multi'?g.ids:g.questions.map(q=>q.id))}));")
r = subprocess.run(['node', '-e', node_src], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit('Data JS error:\n' + r.stderr)
obj = json.loads(r.stdout)
passtext, quotes, ids = obj['p'], obj['q'], sorted(obj['ids'])

def esc(q): return r"\s+".join(re.escape(t) for t in q.split())
miss = [k for k, v in quotes.items() if not re.search(esc(v), passtext, re.I)]
if miss:
    sys.exit('answerHighlightQuotes NOT found in passages (fix or remove): ' + ', '.join(sorted(miss, key=int)))

warn = []
if ids != list(range(1, 41)):
    warn.append(f'question ids are {ids[:3]}..{ids[-3:]} (expected a full 1..40)')

# --- verify the assembled script parses ---
scr = re.search(r'<script>([\s\S]*)</script>', out).group(1)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as tf:
    tf.write(scr); tmp = tf.name
c = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if c.returncode != 0:
    sys.exit('Assembled script has a syntax error:\n' + c.stderr)

os.makedirs(os.path.dirname(a.out), exist_ok=True)
open(a.out, 'w').write(out)
print(f'OK  wrote {a.out}  ({len(out)} bytes)')
print(f'    quotes verified: {len(quotes)}   questions: {len(ids)}')
for w in warn:
    print('    WARNING:', w)
