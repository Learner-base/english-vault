---
name: test-naming
description: The canonical short-file-name convention for generated test HTML in this vault (Cambridge reading/listening/writing/speaking tests and similar). Use whenever creating, renaming, or deciding the output filename of a generated test, so names stay short, consistent, and easy to scan in index.html. The reading-generate and listening-generate skills follow this.
---

# Test file-naming convention

Generated test files use **short, lowercase, hyphenated** names — never the long
"Cambridge 20 Test 1 Reading.html" form. Short names keep `index.html` scannable and
URLs clean.

## Format

```
C{book}-{type}{test}.html
```

- **Cambridge → `C`** — Cambridge 20 → `C20`, Cambridge 21 → `C21`.
- **Skill/type letter:**
  - reading → `r`
  - listening → `l`
  - writing → `w`
  - speaking → `s`
- **test number** follows the type letter.

### Examples

| Long name | Short name |
|-----------|------------|
| Cambridge 20 Test 1 Reading | `C20-r1.html` |
| Cambridge 21 Test 3 Listening | `C21-l3.html` |
| Cambridge 18 Test 1 Reading | `C18-r1.html` |
| Cambridge 21 Test 4 Writing | `C21-w4.html` |

## Location (unchanged)

The file still lives in its section/status/book folder — only the filename shortens:

```
reading/undone/cambridge/cambridge-20/C20-r1.html
listening/done/cambridge/cambridge-21/C21-l3.html
```

## Non-Cambridge sources

For other providers, keep the same spirit: a short lowercase slug that's obvious at a
glance — publisher abbreviation + type letter + number, e.g. `ielts-trainer-r2.html`,
`mock-l1.html`. Prefer the shortest name that stays unambiguous.

## Display text vs filename

This convention governs the **filename only**. Inside the page, the human-readable
`<title>`, header, and badge still spell things out (e.g. "Cambridge IELTS 20 — Reading
Test 1", badge `C20`). See the header-badge convention in the generate skills.

After creating or renaming any file, run `python3 dev/scripts/build_index.py` so the main
page and the road player pick up the new name.
