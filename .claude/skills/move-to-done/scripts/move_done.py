#!/usr/bin/env python3
"""Move a test file from an `undone/` folder to the matching `done/` folder.

Usage:
    python3 .claude/skills/move-to-done/scripts/move_done.py <path> [<path> ...]

For each given file under `.../undone/...`, it:
  * computes the destination by swapping `/undone/` -> `/done/`,
  * creates the destination folder if it doesn't exist,
  * moves the file with `git mv` (falls back to os.rename if untracked),
  * refreshes the main page + player (dev/scripts/build_index.py, which also rebuilds
    player.html),
  * greps the repo for any other place that still references the old path/name and
    prints them so you can update those by hand.

It never commits — review, then commit with the user's go-ahead.
"""
import os, sys, re, subprocess

ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def move_one(path):
    rel = os.path.relpath(os.path.abspath(path), ROOT)
    if "/undone/" not in ("/" + rel):
        # allow both ".../undone/..." and "undone/..." at the start
        if not re.search(r"(^|/)undone/", rel):
            print(f"SKIP (no undone/ segment): {rel}")
            return None
    dest = re.sub(r"(^|/)undone/", r"\1done/", rel, count=1)
    if not os.path.exists(os.path.join(ROOT, rel)):
        print(f"SKIP (not found): {rel}")
        return None
    os.makedirs(os.path.join(ROOT, os.path.dirname(dest)), exist_ok=True)
    # git mv when tracked, else plain move
    tracked = sh("git", "ls-files", "--error-unmatch", rel).returncode == 0
    if tracked:
        r = sh("git", "mv", rel, dest)
        if r.returncode != 0:
            print(f"ERROR git mv {rel}: {r.stderr.strip()}")
            return None
    else:
        os.rename(os.path.join(ROOT, rel), os.path.join(ROOT, dest))
        sh("git", "add", dest)
    # if the source folder is now empty, drop it so it doesn't linger in the index
    src_dir = os.path.join(ROOT, os.path.dirname(rel))
    try:
        if os.path.isdir(src_dir) and not os.listdir(src_dir):
            os.rmdir(src_dir)
            print(f"removed empty folder  {os.path.dirname(rel)}")
    except OSError:
        pass
    print(f"moved  {rel}\n    ->  {dest}")
    return rel, dest


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    moved = [m for m in (move_one(p) for p in sys.argv[1:]) if m]
    if not moved:
        sys.exit("Nothing moved.")

    # rebuild main page (also rebuilds player.html)
    r = sh("python3", "dev/scripts/build_index.py")
    print(r.stdout.strip() or r.stderr.strip())

    # flag other references to the moved files (besides generated pages)
    print("\nOther references to check (update by hand if any):")
    hits = False
    for rel, dest in moved:
        base = os.path.basename(rel)
        for token in (rel, base):
            r = sh("git", "grep", "-n", "--fixed-strings", token,
                   "--", ":!index.html", ":!player.html")
            if r.stdout.strip():
                hits = True
                print(r.stdout.strip())
    if not hits:
        print("  none — index.html + player.html already updated.")
    print("\nReview, then commit with the user's go-ahead (do not push unless asked).")


if __name__ == "__main__":
    main()
