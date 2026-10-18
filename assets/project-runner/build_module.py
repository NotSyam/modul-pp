#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_module.py - Runner mandiri proyek modul e-learning (skill modul-pp)
=========================================================================
Mengompilasi `content.json` di folder ini menjadi `index.html` memakai engine
kanonik skill **modul-pp**.

Alur kerja:
  1. Validasi   -> scripts/validate_content.py  (skema + cek semantik)
  2. Build      -> scripts/build_module.py      (content.json -> index.html)
  3. Verifikasi -> tools/verify_module.py       (DOM, sintaks JS, parity COURSE)

Penggunaan:
  python build_module.py                  # validate -> build -> verify
  python build_module.py --check          # build ke file sementara + verify,
                                          # index.html TIDAK ditulis
  python build_module.py --skill-root X   # paksa lokasi skill modul-pp
  python build_module.py --print-skill-root

Lokasi skill dicari dengan urutan:
  1. --skill-root
  2. env MODUL_PP_SKILL_ROOT
  3. file konfigurasi opsional  .modul-pp.json  {"skillRoot": "..."}  di folder ini
  4. folder bernama `modul-pp` pada folder ini atau leluhurnya
  5. lokasi instalasi umum (diturunkan dari home dir, bukan path hardcode)

Catatan: hanya `content.json` yang perlu diubah. Setelah mengeditnya, jalankan
ulang skrip ini dan `index.html` akan dibangun ulang secara otomatis.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Hindari error encoding cp1252 pada terminal Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CWD = Path(__file__).resolve().parent
CONTENT_PATH = CWD / "content.json"
OUTPUT_PATH = CWD / "index.html"
CONFIG_NAME = ".modul-pp.json"

# Instalasi umum, DITURUNKAN dari home dir pengguna — tidak ada username hardcode.
HOME = Path.home()
SKILL_ROOT_CANDIDATES = [
    HOME / ".dsh" / "skills" / "modul-pp",
    HOME / ".gemini" / "config" / "skills" / "modul-pp",
    HOME / ".agents" / "skills" / "modul-pp",
    HOME / ".claude" / "skills" / "modul-pp",
]

LINE = "=" * 62


def is_skill_root(path) -> bool:
    p = Path(path)
    return (p / "scripts" / "build_module.py").exists() and (p / "assets" / "shell.template.html").exists()


def find_skill_root(explicit=None, quiet=False):
    """Kembalikan skill root yang valid, atau None."""
    candidates = []
    if explicit:
        candidates.append((Path(explicit), "--skill-root"))
    if os.environ.get("MODUL_PP_SKILL_ROOT"):
        candidates.append((Path(os.environ["MODUL_PP_SKILL_ROOT"]), "env MODUL_PP_SKILL_ROOT"))

    config_path = CWD / CONFIG_NAME
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(cfg.get("skillRoot"), str):
                candidates.append((Path(cfg["skillRoot"]), CONFIG_NAME))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[!] {CONFIG_NAME} tidak bisa dibaca: {e}")

    # folder `modul-pp` pada folder ini atau leluhurnya
    for base in [CWD, *CWD.parents]:
        candidates.append((base / "modul-pp", "sibling modul-pp"))
        # dan skill root bila folder ini berada di dalam repo skill
        if (base / "scripts" / "build_module.py").exists():
            candidates.append((base, "parent skill root"))

    for path in SKILL_ROOT_CANDIDATES:
        candidates.append((path, "instalasi umum"))

    for path, source in candidates:
        if is_skill_root(path):
            if not quiet:
                print(f"[*] Skill root   : {path}  (dari: {source})")
            return Path(path)

    if explicit:
        print(f"[!] --skill-root tidak valid (butuh scripts/build_module.py + assets/shell.template.html): {explicit}")
    return None


def run(label, cmd, cwd=None):
    print(f"\n[*] {label}")
    return subprocess.run(cmd, cwd=str(cwd or CWD)).returncode


def file_hash(path: Path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--skill-root", default=None,
                    help="Lokasi folder skill modul-pp (opsional, biasanya terdeteksi otomatis)")
    ap.add_argument("--content", default=None, help="Path content.json (default: ./content.json)")
    ap.add_argument("--output", default=None, help="Path index.html (default: ./index.html)")
    ap.add_argument("--check", action="store_true",
                    help="Build ke file sementara lalu verifikasi; index.html tidak diubah")
    ap.add_argument("--print-skill-root", action="store_true", help="Tampilkan lokasi skill lalu keluar")
    args = ap.parse_args()

    content = Path(args.content).resolve() if args.content else CONTENT_PATH
    output = Path(args.output).resolve() if args.output else OUTPUT_PATH

    if args.print_skill_root:
        root = find_skill_root(args.skill_root)
        if root is None:
            print("[!] Skill 'modul-pp' tidak ditemukan. Setel MODUL_PP_SKILL_ROOT atau pakai --skill-root.")
            sys.exit(1)
        print(root)
        return

    print(LINE)
    print("  Modul PP Compiler — interactive e-learning module builder")
    print(LINE)

    if not content.exists():
        print(f"[!] content.json tidak ditemukan di: {content}")
        sys.exit(1)

    skill_root = find_skill_root(args.skill_root)
    if skill_root is None:
        print("[!] Folder skill 'modul-pp' tidak ditemukan.")
        print("    Setel env MODUL_PP_SKILL_ROOT, atau jalankan dengan --skill-root <path>,")
        print(f"    atau tulis {{\"skillRoot\": \"...\"}} ke {CONFIG_NAME}.")
        print("    Kandidat yang sudah dicoba:")
        for p in SKILL_ROOT_CANDIDATES:
            print(f"      - {p}")
        sys.exit(1)

    validator = skill_root / "scripts" / "validate_content.py"
    builder = skill_root / "scripts" / "build_module.py"
    verifier = skill_root / "tools" / "verify_module.py"

    print(f"[*] Sumber Konten : {content.name}")
    print(f"[*] Target HTML   : {output.name}")
    print(f"[*] Skill root    : {skill_root}")

    # ---- 1. Validasi ----
    if validator.exists():
        if run("Menjalankan validasi konten...", [sys.executable, str(validator), str(content)]) != 0:
            print("\n[!] Validasi gagal. Perbaiki content.json lalu ulangi.")
            sys.exit(1)
    else:
        print(f"[!] Validator tidak ditemukan, dilewati: {validator}")

    # ---- 2. Build ----
    # --check membangun ke file sementara supaya verifikasi benar-benar menguji
    # content.json saat ini, bukan index.html lama yang mungkin sudah usang.
    build_target = output
    if args.check:
        build_target = output.with_name(output.stem + ".check.html")
        print(f"\n[*] Mode --check: menulis ke {build_target.name}, index.html tidak diubah.")

    before_hash = file_hash(output) if not args.check else None
    cmd = [sys.executable, str(builder),
           "--content", str(content),
           "--output", str(build_target),
           "--skill-root", str(skill_root)]
    if run("Mengompilasi modul HTML...", cmd) != 0:
        print("\n[!] Gagal mengompilasi modul HTML.")
        sys.exit(1)

    # ---- 3. Verifikasi ----
    rc = 0
    if verifier.exists():
        rc = run("Menjalankan audit verifikasi kualitas...",
                 [sys.executable, str(verifier), str(build_target), "--content", str(content)])
    else:
        print(f"[!] Verifier tidak ditemukan, dilewati: {verifier}")

    after_hash = file_hash(build_target)

    if args.check:
        try:
            build_target.unlink()
            print(f"\n[*] File sementara {build_target.name} dihapus.")
        except OSError:
            pass
    elif before_hash and after_hash and before_hash == after_hash:
        print("\n[i] Catatan: isi index.html identik dengan sebelumnya (tidak ada perubahan konten).")

    if rc != 0:
        print("\n[!] Audit verifikasi menemukan masalah. Lihat detail di atas.")
        sys.exit(1)

    print("\n" + LINE)
    if args.check:
        print("[OK] Pemeriksaan selesai tanpa error (index.html tidak diubah).")
    else:
        print("[OK] Selesai! Modul berhasil dibuat di:")
        print(f"     file:///{str(output).replace(os.sep, '/')}")
    print(LINE)


if __name__ == "__main__":
    main()
