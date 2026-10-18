#!/usr/bin/env python3
"""
sync_installs.py — mirror one canonical modul-pp copy to the other installs.

This skill tends to exist in several places at once (a workspace checkout,
`~/.dsh/skills/modul-pp` for DeepSeek Harness, `~/.gemini/config/skills/modul-pp`
for Gemini/Antigravity, …). Editing one copy and forgetting the others is the
single most reliable way to ship a stale skill, so this tool compares every file
by SHA256 and mirrors the canonical copy onto the rest.

USAGE
  # show what differs (no writes) — exit 1 when any target is out of sync
  python3 tools/sync_installs.py

  # actually mirror the canonical copy onto the other installs
  python3 tools/sync_installs.py --apply

  # choose the canonical copy and/or explicit targets
  python3 tools/sync_installs.py --from "D:/repo/modul-pp" --to "~/.dsh/skills/modul-pp" --apply

  # list every install location this tool knows about
  python3 tools/sync_installs.py --list

DEFAULTS
  --from   the directory containing this script's parent (the skill root itself)
  --to     every known install location except --from

EXCLUDED (never copied, never compared)
  build/, __pycache__/, .git/, node_modules/, .DS_Store, *.pyc, *.log

Exit codes: 0 = in sync (or applied cleanly), 1 = drift found / apply failed.
"""
import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOME = Path.home()

# Install locations, derived from the home directory — no hardcoded usernames.
STANDARD_TARGETS = [
    HOME / ".dsh" / "skills" / "modul-pp",
    HOME / ".gemini" / "config" / "skills" / "modul-pp",
    HOME / ".agents" / "skills" / "modul-pp",
    HOME / ".claude" / "skills" / "modul-pp",
    HOME / ".cursor" / "skills" / "modul-pp",
]

WORKSPACE_CANDIDATES = [
    HOME / "OneDrive - Business" / "Documents" / "deepseek-harness" / "default-workspace" / "modul-pp",
    HOME / "OneDrive - Business" / "Documents" / "deepseek-harness" / "default-workspace" / "modul-pp-work",
    HOME / "Documents" / "deepseek-harness" / "default-workspace" / "modul-pp",
    HOME / "Documents" / "deepseek-harness" / "default-workspace" / "modul-pp-work",
]

KNOWN_TARGETS = STANDARD_TARGETS + [p for p in WORKSPACE_CANDIDATES if p.exists()]

EXCLUDE_DIRS = {"build", "__pycache__", ".git", "node_modules", "download", ".venv", "venv"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}


def is_excluded(rel: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if rel.name in EXCLUDE_NAMES or rel.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def walk(root: Path):
    """{relative posix path: sha256} for every tracked file under root."""
    files = {}
    if not root.exists():
        return files
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if is_excluded(rel):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files[rel.as_posix()] = digest
    return files


def looks_like_skill_root(path: Path) -> bool:
    return (path / "SKILL.md").exists() and (path / "scripts" / "build_module.py").exists()


def plan(source_files, target_files):
    added = sorted(set(source_files) - set(target_files))
    changed = sorted(k for k in set(source_files) & set(target_files) if source_files[k] != target_files[k])
    extra = sorted(set(target_files) - set(source_files))
    return added, changed, extra


def describe(target: Path, added, changed, extra):
    print(f"\n  → {target}")
    if not added and not changed and not extra:
        print("      in sync")
        return
    for name in added:
        print(f"      + add      {name}")
    for name in changed:
        print(f"      ~ update   {name}")
    for name in extra:
        print(f"      - extra    {name}   (left alone; use --prune to delete)")


def apply_plan(source: Path, target: Path, added, changed, extra, prune=False):
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in added + changed:
        src = source / name
        dst = target / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    removed = 0
    if prune:
        for name in extra:
            try:
                (target / name).unlink()
                removed += 1
            except OSError as e:
                print(f"      ! could not delete {name}: {e}", file=sys.stderr)
    return copied, removed


def main():
    ap = argparse.ArgumentParser(description="Mirror a canonical modul-pp copy to the other installs")
    ap.add_argument("--from", dest="source", default=None,
                    help="Canonical skill root (default: this script's skill root)")
    ap.add_argument("--to", dest="targets", action="append", default=None,
                    help="Target skill root (repeatable). Default: every known install except --from")
    ap.add_argument("--apply", action="store_true", help="Write the changes (default is a dry run)")
    ap.add_argument("--prune", action="store_true",
                    help="Also delete files in the target that do not exist in the canonical copy")
    ap.add_argument("--list", action="store_true", help="List known install locations and exit")
    args = ap.parse_args()

    script_root = Path(__file__).resolve().parent.parent

    if args.list:
        print("Known install locations:")
        for p in KNOWN_TARGETS:
            exists = "exists" if looks_like_skill_root(p) else "not a skill root"
            print(f"  {'*' if p == script_root else ' '} {p}  [{exists}]")
        print(f"\n  this script's skill root: {script_root}")
        return

    source = Path(args.source).expanduser().resolve() if args.source else script_root
    if not looks_like_skill_root(source):
        print(f"ERROR: {source} is not a modul-pp skill root (needs SKILL.md + scripts/build_module.py)",
              file=sys.stderr)
        sys.exit(1)

    if args.targets:
        targets = [Path(t).expanduser().resolve() for t in args.targets]
    else:
        targets = [p.resolve() for p in KNOWN_TARGETS if p.resolve() != source]

    if not targets:
        print("ERROR: no targets to sync (all known locations resolve to the canonical copy)", file=sys.stderr)
        sys.exit(1)

    print(f"Canonical : {source}")
    source_files = walk(source)
    print(f"Tracked   : {len(source_files)} files (build artifacts and caches excluded)")

    drift = False
    plans = []
    for target in targets:
        target_files = walk(target)
        added, changed, extra = plan(source_files, target_files)
        describe(target, added, changed, extra)
        if added or changed or extra:
            drift = True
        plans.append((target, added, changed, extra))

    if not args.apply:
        print("\n" + ("DRIFT DETECTED — rerun with --apply to mirror the canonical copy."
                      if drift else "All targets are in sync."))
        sys.exit(1 if drift else 0)

    print("\nApplying:")
    failed = False
    for target, added, changed, extra in plans:
        if not (added or changed or extra):
            continue
        copied, removed = apply_plan(source, target, added, changed, extra, prune=args.prune)
        print(f"  ✓ {target}: {copied} file(s) copied" + (f", {removed} removed" if removed else ""))

    # Verify the mirror is byte-exact afterwards.
    for target in targets:
        added, changed, extra = plan(source_files, walk(target))
        leftover = bool(added or changed or (extra and args.prune))
        if leftover:
            failed = True
            print(f"  ✗ {target} still differs: {len(added)} missing, {len(changed)} changed", file=sys.stderr)
        else:
            extra_note = f" ({len(extra)} extra file(s) left in place)" if extra else ""
            print(f"  ✓ verified in sync: {target}{extra_note}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
