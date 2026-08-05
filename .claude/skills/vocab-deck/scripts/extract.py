#!/usr/bin/env python3
"""Extract passages, questions and a known-words list from a reading-test HTML.

The reading HTML (e.g. reading/.../Cambridge 21 Test 3 Reading.html) embeds all
passage + question data as a `const testData = {...}` object inside a <script>.
This pulls it out cleanly (do NOT try to strip HTML tags — the prose lives in JS).

Usage:
    python extract.py <reading.html> <out_dir>

Writes into <out_dir>:
    readable.txt      passages + questions as readable text (source of EXACT example sentences)
    known_words.txt   sorted unique lowercased words from all passages + questions
    testData.json     the parsed raw object (for reference)
"""
import sys, re, json, os


def extract_testdata(raw):
    start = raw.find("const testData")
    if start == -1:
        raise SystemExit("Could not find `const testData` in the HTML.")
    start = raw.find("{", start)
    depth = 0; instr = False; esc = False; end = None
    for i in range(start, len(raw)):
        ch = raw[i]
        if instr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1; break
    if end is None:
        raise SystemExit("Unbalanced testData object.")
    return json.loads(raw[start:end])


def collect_text(data):
    chunks = []
    for p in data.get("parts", []):
        pa = p.get("passage", {})
        chunks.append("\n\n########## PART %s: %s ##########" % (p.get("id"), pa.get("title", "")))
        if pa.get("intro"):
            chunks.append("[INTRO] " + pa["intro"])
        c = pa.get("content")
        if isinstance(c, list):
            chunks.extend(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in c)
        elif c:
            chunks.append(str(c))
        chunks.append("\n===== QUESTIONS =====")
        chunks.append(json.dumps(p.get("questions", []), ensure_ascii=False, indent=1))
    return "\n".join(chunks)


def collect_words(data):
    bag = []
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for x in o: walk(x)
        elif isinstance(o, str):
            bag.append(o)
    for p in data.get("parts", []):
        walk(p.get("passage", {}))
        walk(p.get("questions", []))
    blob = re.sub(r"<[^>]+>", " ", " ".join(bag))
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", blob.lower())
    return sorted(set(words))


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    raw = open(src, encoding="utf-8", errors="ignore").read()
    data = extract_testdata(raw)
    json.dump(data, open(os.path.join(out_dir, "testData.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(out_dir, "readable.txt"), "w").write(collect_text(data))
    words = collect_words(data)
    open(os.path.join(out_dir, "known_words.txt"), "w").write("\n".join(words))
    print("parts:", len(data.get("parts", [])))
    for p in data.get("parts", []):
        print("  PART", p.get("id"), "-", p.get("passage", {}).get("title", ""))
    print("unique words:", len(words))
    print("wrote readable.txt, known_words.txt, testData.json to", out_dir)


if __name__ == "__main__":
    main()
